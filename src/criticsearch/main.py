import asyncio
import concurrent.futures
import importlib.resources
import json
import re
import argparse
import sys
import uuid
from pathlib import Path

import yaml
from rich.progress import Progress, BarColumn, TextColumn
from tenacity import retry, stop_after_attempt, wait_fixed
from jinja2 import Template

from .base_agent import BaseAgent
from .critic_agent import CriticAgent
from .reportbench.report_benchmark import ReportBenchmark
from .reportbench.verifier import ReportVerifier
from .rich_output import printer
from .tools.search_adapter.search_aggregator import SearchAggregator
from .tools.note_manager import set_session
from .utils import (
    extract_answer_from_response,
    extract_queries_from_response,
    extract_thought_from_response,
    extract_citations,
    extract_actions,
    extract_tag_content,
)
from .config import settings


def flatten_outline(section, depth=1, path=None):
    # 将 outline_json 展平，记录每个节点及其层级和路径
    if path is None:
        path = []
    current = {
        "path": path + [section.get("title")],
        "section": section,
        "depth": depth,
    }
    flat = [current]
    if "children" in section:
        for child in section["children"]:
            flat.extend(
                flatten_outline(child, depth + 1, path + [section.get("title")])
            )
    return flat


def generate_content_for_section(agent: BaseAgent, section, task):
    # 保持 prompt 不变，仅生成单层章节内容，不递归
    title = section.get("title")
    search_query = f"generate some search queries about '{title}' under the background of this TOPIC/TASK: '{task}'."
    search_results = agent.search_and_browse(search_query)
    prompt = (
        f"Using the following search results:\n\n{search_results}\n\n"
        f"Write one or several detailed paragraphs with data and facts in a logical way about '{title}' under the background of this TOPIC/TASK: '{task}', formatted in pure text, without summary sentences."
        f"Please make sure you are always obeying and using '<\cite>The url link that you used for supporting the previous statement<\cite>' format in every sentence that you are using data from the web."
    )
    paragraph = agent.chat(usr_prompt=prompt)
    printer.rule(f"Generated content for '{title}'")
    printer.print(paragraph)
    return paragraph


def reconstruct_markdown(outline, flat_contents):
    """
    根据展平后的内容与原 outline 结构，拼接生成最终 Markdown 文本
    使用完整路径为key确保唯一性
    """
    # 构建以完整路径为key的映射字典
    content_map = {}
    for item, content in flat_contents:
        path_key = tuple(item["path"])  # 使用完整路径作为key
        content_map[path_key] = content

    def helper(section, path=[]):
        current_path = path + [section.get("title")]
        path_key = tuple(current_path)

        # 生成标题（深度就是路径的长度）
        depth = len(current_path)
        md = f"{'#' * depth} {section.get('title')}\n\n"

        # 添加该节的内容（如果有）
        if path_key in content_map:
            md += f"{content_map[path_key]}\n\n"

        # 处理子节点
        if "children" in section:
            for child in section["children"]:
                md += helper(child, current_path)
        return md

    result = ""
    if "title" in outline:
        result += f"# {outline['title']}\n\n"

    for section in outline.get("children", []):
        result += helper(section, [outline.get("title")] if "title" in outline else [])

    return result


def create_document_structure(outline_json, flat_contents):
    """
    基于outline结构和生成的内容创建文档结构
    """
    document = {
        "document": {
            "title": outline_json.get("title", ""),
            "level": 1,
            "subsections": [],
        }
    }

    # 构建路径到内容的映射
    content_map = {}
    for item, content in flat_contents:
        path_key = tuple(item["path"])
        content_map[path_key] = content

    def process_section(section, depth=1, path=[]):
        current_path = path + [section.get("title")]
        path_key = tuple(current_path)

        section_data = {"title": section.get("title"), "level": depth, "paragraphs": []}

        # 如果有内容，处理段落
        if path_key in content_map:
            content = content_map[path_key]
            paragraphs = content.split("\n\n")  # 假设段落用空行分隔
            for para in paragraphs:
                if para.strip():  # 忽略空段落
                    citations = extract_citations(para)
                    paragraph_data = {
                        "text": para.strip(),  # 保留原始文本，包括cite标记
                        "citations": citations,
                    }
                    section_data["paragraphs"].append(paragraph_data)

        # 处理子节点
        if "children" in section:
            section_data["subsections"] = []
            for child in section["children"]:
                child_data = process_section(child, depth + 1, current_path)
                section_data["subsections"].append(child_data)

        return section_data

    # 处理根节点下的所有节点
    for section in outline_json.get("children", []):
        doc_section = process_section(
            section, 2, [outline_json.get("title")] if "title" in outline_json else []
        )
        document["document"]["subsections"].append(doc_section)

    return document


def parse_markdown_to_structure(markdown_text):
    """从markdown文本解析出文档结构"""
    lines = markdown_text.split("\n")
    document = {"document": {"title": "", "level": 1, "subsections": []}}

    current_section = document["document"]
    section_stack = [current_section]
    current_level = 1
    current_text = []

    for line in lines:
        if line.strip():
            # 处理标题
            if line.startswith("#"):
                # 如果有待处理的段落文本，先处理完
                if current_text:
                    paragraph_text = " ".join(current_text)
                    if paragraph_text.strip():
                        citations = extract_citations(paragraph_text)
                        current_section.setdefault("paragraphs", []).append(
                            {"text": paragraph_text.strip(), "citations": citations}
                        )
                    current_text = []

                # 处理新标题
                level = len(line.split()[0])  # 计算#的数量
                title = " ".join(line.split()[1:])

                # 根据层级调整当前section
                while len(section_stack) > 1 and level <= section_stack[-1]["level"]:
                    section_stack.pop()

                new_section = {
                    "title": title,
                    "level": level,
                    "subsections": [],
                    "paragraphs": [],
                }

                section_stack[-1].setdefault("subsections", []).append(new_section)
                section_stack.append(new_section)
                current_section = new_section

            else:
                # 收集段落文本
                current_text.append(line)
        else:
            # 空行，处理当前段落
            if current_text:
                paragraph_text = " ".join(current_text)
                if paragraph_text.strip():
                    citations = extract_citations(paragraph_text)
                    current_section.setdefault("paragraphs", []).append(
                        {"text": paragraph_text.strip(), "citations": citations}
                    )
                current_text = []

    # 处理最后一个段落
    if current_text:
        paragraph_text = " ".join(current_text)
        if paragraph_text.strip():
            citations = extract_citations(paragraph_text)
            current_section.setdefault("paragraphs", []).append(
                {"text": paragraph_text.strip(), "citations": citations}
            )

    return document

##### 分割线，上面的无关函数全部需要移动到utils.py中 #####

def _get_xml_tool_response(
    agent: BaseAgent,
    search_results: str,
    task: str,
    current_section: str,
):
    """
    使用XML格式让模型决定下一步行动
    """
    # 使用专门的XML格式决策prompt
    response = agent.chat_with_template("xml_action_decision.txt", {
        "task": task,
        "current_section": current_section,
        "search_results": search_results
    })
    
    return response


def _execute_tool_action(agent: BaseAgent, tool_xml: str):
    """
    执行工具调用并返回结果
    """
    tool_name = extract_tag_content(tool_xml, "name")
    arg_str = extract_tag_content(tool_xml, "arguments") or "{}"
    
    try:
        args = json.loads(arg_str)
        
        # 对于异步工具，需要使用asyncio.run
        if tool_name == "search":
            result = asyncio.run(agent.search_aggregator.search(args.get("query", [])))
        elif tool_name == "scrape":
            result = asyncio.run(agent.content_scraper.scrape(args.get("urls", [])))
        elif tool_name == "taking_notes":
            # 使用工具注册表调用笔记工具
            result = agent.tool_registry.invoke_tool(tool_name, args)
        elif tool_name == "retrieve_notes":
            # 使用工具注册表调用笔记工具
            result = agent.tool_registry.invoke_tool(tool_name, args)
        else:
            # 对于其他工具，直接调用
            result = agent.tool_registry.invoke_tool(tool_name, args)
        
        result_xml = (
            f"<tool_use_result><name>{tool_name}</name>"
            f"<result>{json.dumps(result, ensure_ascii=False)}</result>"
            f"</tool_use_result>"
        )
        
        return tool_name, args, result, result_xml
        
    except json.JSONDecodeError:
        error_xml = (
            f"<tool_use_result><name>{tool_name}</name>"
            f"<error>arguments_not_json</error></tool_use_result>"
        )
        raise ValueError(f"Invalid JSON arguments: {arg_str}")
        
    except Exception as exc:
        error_xml = (
            f"<tool_use_result><name>{tool_name}</name>"
            f"<error>{str(exc)}</error></tool_use_result>"
        )
        raise ValueError(f"Tool execution failed: {str(exc)}")


def _action_router_xml(
    agent: BaseAgent,
    search_results: str,    
    task: str,
    current_section: str,
    iteration: int,
    agent_report: str,
    guide_line: str,
    sharegpt_conversation: list,
    detailed_web_results: str = "",
):
    """
    使用XML格式的行动路由器，直到模型提供最终答案
    完整记录所有工具调用和返回结果到ShareGPT格式
    """
    max_iterations = 10
    current_iteration = 0
    
    while current_iteration < max_iterations:
        # 获取模型的XML格式响应
        response = _get_xml_tool_response(agent, search_results, task, current_section)
        
        # 添加模型响应到ShareGPT对话记录
        sharegpt_conversation.append({
            "from": "gpt", 
            "value": response
        })
        
        printer.rule("Model XML Response")
        printer.print(response)
        
        # 检查是否是工具调用
        tool_xml = extract_tag_content(response, "tool_use")
        
        if tool_xml:
            # 执行工具调用
            try:
                tool_name, args, result, result_xml = _execute_tool_action(agent, tool_xml)
                
                printer.rule(f"Tool Result: {tool_name}")
                printer.print(result_xml)
                
                # 添加工具结果到ShareGPT对话记录（作为human响应）
                sharegpt_conversation.append({
                    "from": "human",
                    "value": result_xml
                })
                
                # 更新搜索结果（如果是搜索相关工具）
                if tool_name == "search":
                    search_results += f"\n\n{result}"
                elif tool_name == "scrape":
                    detailed_web_results += f"\n\n{result}"
                    search_results += f"\n\n{result}"
                
                current_iteration += 1
                continue
                
            except ValueError as e:
                error_msg = f"<error>{str(e)}</error>"
                sharegpt_conversation.append({
                    "from": "human",
                    "value": error_msg
                })
                current_iteration += 1
                continue
        
        # 检查是否提供了最终答案
        final_answer = extract_tag_content(response, "answer")
        if final_answer:
            printer.rule("Final Section Content")
            printer.print(final_answer)
            return final_answer
        
        # 如果既没有工具调用也没有最终答案，提示模型
        error_msg = "<error>请使用工具调用或提供最终答案</error>"
        sharegpt_conversation.append({
            "from": "human",
            "value": error_msg
        })
        current_iteration += 1
    
    # 如果达到最大迭代次数，返回最后的响应内容
    return extract_tag_content(response, "answer") or "无法生成章节内容"


def create_sharegpt_conversation(system_prompt: str, initial_user_query: str) -> list:
    """
    创建ShareGPT格式的对话记录
    """
    return [
        {"from": "system", "value": system_prompt},
        {"from": "human", "value": initial_user_query}
    ]


def process_single_task(task, file_name=None):
    # Initialize agents
    agent = BaseAgent()
    agent.receive_task(task)
    
    # 设置 session ID 用于笔记管理
    session_id = str(uuid.uuid4())
    set_session(session_id)
    
    # 不再初始化training_data，只使用ShareGPT格式
    # agent.training_data = [
    #     {"from": "human", "value": task},
    # ]
    agent.memo = set()
    search_agg = agent.search_aggregator
    verifier = ReportVerifier(agent)

    package_name = "criticsearch.reportbench.wiki_data"
    file_name = file_name or "2024_Syrian_opposition_offensives.json"

    with importlib.resources.files(package_name).joinpath(file_name) as json_file_path:
        json_file = str(json_file_path)

    benchmark = ReportBenchmark(json_file)
    outline = benchmark.generate_benchmark_item(max_window_tokens=1, use_cache=True)

    # initialize the task
    agent.user_question = task

    printer.log(f"Starting the conversation with task: \n{task}")

    BaseAgent.conversation_manager.append_to_history(role="user", content=task)

    # 创建ShareGPT格式的对话记录
    tool_schemas = agent.get_all_tool_schemas()
    tpl = Path(agent.prompts_dir) / "tool_use_short.txt"
    system_prompt_content = Template(tpl.read_text(encoding="utf-8")).render(
        AVAILABLE_TOOLS=json.dumps(tool_schemas, ensure_ascii=False),
    )
    
    all_sharegpt_conversations = []

    # ============ 进度条 =============
    progress = Progress(
        TextColumn("[bold cyan]Chapter Progress:"),
        BarColumn(bar_width=None),
        # 显示 completed(name)/total
        TextColumn("{task.completed}({task.fields[section_name]})/{task.total}"),
        TextColumn("{task.percentage:>3.0f}%"),
        disable=getattr(settings, "disable_progress", False),
    )
    with progress:
        # 初始时用第一个 section 的 name 作为 section_name
        first_name = outline[0]["path"].split("->")[-1].strip().lstrip("# ").strip()
        section_task = progress.add_task("processing", total=len(outline), section_name=first_name)

        printer.rule("BEGIN SECTION‑BY‑SECTION GENERATION")

        # 先判断一次模型信心
        agent_confident = agent.chat_with_template("agent_confidence.txt", {"user_question": task})
        agent_confident_yaml = agent.extract_and_validate_yaml(agent_confident)

        if agent_confident_yaml is None:
            printer.log("Failed to extract valid YAML content. Defaulting to 'false'.")
            agent_confident = False
        else:
            agent_confident_dict = yaml.safe_load(agent_confident_yaml)
            agent_confident = agent_confident_dict.get("confidence", "true").lower() == "true"

        if agent_confident:
            agent_answer = agent.chat_with_template("direct_response.txt", {"task": task})
        else:
            agent_report_sections = []  # Initialize the list to store report sections
            for item in outline:  # 按wiki的GT大纲走一次滑窗
                # 提取当前窗口的"名称"，这里直接用 path 文本，或者你也可以进一步 split 拿最后的标题
                current_name = item["path"].split("->")[-1].strip().lstrip("# ").strip()
                # 更新进度条里的字段
                progress.update(section_task, section_name=current_name)
                # 推进"节"计数
                progress.advance(section_task)

                section_path = item["path"]
                merged_section_content = item["merged_section_window_content"]
                extracted_facts = item["extracted_facts"]

                agent_report = "\n".join(agent_report_sections)
                
                # 为每个section创建新的ShareGPT对话
                section_user_prompt = f"""任务：{task}

{"这是文章的第一个章节。" if not agent_report else f"前面已写的内容：{agent_report}"}

当前需要写的章节：{section_path}

请使用工具搜索相关信息，然后生成这个章节的内容。"""

                sharegpt_conversation = create_sharegpt_conversation(
                    system_prompt_content, 
                    section_user_prompt
                )
                
                # 执行初始搜索 - 直接使用XML决策模板
                initial_search_response = agent.chat_with_template("xml_action_decision.txt", {
                    "task": task,
                    "current_section": section_path,
                    "search_results": "这是第一次搜索，需要获取基础信息。"
                })

                # 记录模型的初始XML响应
                sharegpt_conversation.append({
                    "from": "gpt", 
                    "value": initial_search_response
                })

                # 解析并执行初始搜索
                search_results = ""
                tool_xml = extract_tag_content(initial_search_response, "tool_use")
                if tool_xml:
                    try:
                        tool_name, args, result, result_xml = _execute_tool_action(agent, tool_xml)
                        
                        # 记录工具执行结果到ShareGPT
                        sharegpt_conversation.append({
                            "from": "human",
                            "value": result_xml
                        })
                        
                        if tool_name == "search":
                            search_results = result
                        else:
                            # 如果不是搜索，执行默认查询
                            search_results = asyncio.run(search_agg.search([section_path, task]))
                            default_result_xml = f"<tool_use_result><name>search</name><result>{json.dumps(search_results, ensure_ascii=False)}</result></tool_use_result>"
                            sharegpt_conversation.append({
                                "from": "human",
                                "value": default_result_xml
                            })
                    except:
                        # 如果解析失败，使用默认查询
                        search_results = asyncio.run(search_agg.search([section_path, task]))
                        default_result_xml = f"<tool_use_result><name>search</name><result>{json.dumps(search_results, ensure_ascii=False)}</result></tool_use_result>"
                        sharegpt_conversation.append({
                            "from": "human",
                            "value": default_result_xml
                        })
                else:
                    # 如果没有工具调用，使用默认查询
                    search_results = asyncio.run(search_agg.search([section_path, task]))
                    default_result_xml = f"<tool_use_result><name>search</name><result>{json.dumps(search_results, ensure_ascii=False)}</result></tool_use_result>"
                    sharegpt_conversation.append({
                        "from": "human",
                        "value": default_result_xml
                    })

                # 使用新的XML格式行动路由器
                answer_content = _action_router_xml(
                    agent, 
                    search_results, 
                    task, 
                    section_path, 
                    0, 
                    agent_report, 
                    section_path, 
                    sharegpt_conversation,
                    search_results
                )

                # 保存这个section的ShareGPT对话
                all_sharegpt_conversations.append({
                    "conversations": sharegpt_conversation,
                    "system": system_prompt_content,
                    "section": section_path
                })

                # 将生成的内容添加到agent_report_sections
                agent_report_sections.append(answer_content)

                # 使用verifier进行factual QA验证，得到这个段落写作的reward分数（也就是准确率）
                accuracy = 0.000

            # 拼接完整的report
            agent_answer = "\n".join(agent_report_sections)

    # 保存ShareGPT格式的对话记录
    output_dir = Path("conversation_histories")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"sharegpt_conversations_{hash(task) % 10000}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_sharegpt_conversations, f, ensure_ascii=False, indent=2)
    
    printer.log(f"ShareGPT conversations saved to: {output_file}")
    
    # 返回ShareGPT格式的对话记录而不是training_data
    return all_sharegpt_conversations


def main():
    parser = argparse.ArgumentParser(description="Run CriticSearch pipeline")
    parser.add_argument("task", help="用户任务描述")
    parser.add_argument("--file-name", "-f", default=None, help="GT 数据文件名")
    args = parser.parse_args()
    try:
        result = process_single_task(args.task, file_name=args.file_name)
        if result:
            print(result)
    except Exception as e:
        printer.print_exception(f"运行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

# Usage example:
"""
# 不指定文件名，用默认 2024_Syrian_opposition_offensives.json
criticsearch "给我写一份2024年叙利亚反对派进攻战役概述" -n 5

# 指定文件名
criticsearch "给我写一份2024年叙利亚反对派进攻战役概述" -n 5 -f my_custom_data.json"""