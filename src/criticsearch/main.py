import asyncio
import concurrent.futures
import importlib.resources
import json
import re
import argparse
import sys

import yaml

from .base_agent import BaseAgent
from .critic_agent import CriticAgent
from .reportbench.report_benchmark import ReportBenchmark
from .reportbench.verifier import ReportVerifier
from .rich_output import printer
from .tools.search_adapter.search_aggregator import SearchAggregator
from .utils import (
    extract_answer_from_response,
    extract_queries_from_response,
    extract_thought_from_response,
    extract_citations,
    extract_actions,
)


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

def _model_action_decision(
    agent: BaseAgent,
    search_results: str,
    task: str,  
    current_section: str,   
):
    decision = agent.chat_with_template("model_action_decision.txt", {
        "search_results": search_results, 
        "task": task, 
        "current_section": current_section
    })
    thought = extract_thought_from_response(decision)
    actions = extract_actions(decision)
    action = next(iter(actions)) if actions else ""

    printer.rule("Model Decision")
    printer.print(decision)

    if action == "SEARCH":
        queries = extract_queries_from_response(decision)
        return thought, action, queries
    elif action == "BROWSE":
        urls = extract_citations(decision)
        return thought, action, urls
    elif action == "START_WRITING":
        return thought, action, None


def _action_router(
    agent: BaseAgent,
    search_results: str,    
    task: str,
    current_section: str,
    iteration: int,
    agent_report: str,
    guide_line: str,
    detailed_web_results: str = "",
):
    # 获取模型的行动决策
    thought, action, data = _model_action_decision(agent, search_results, task, current_section)

    # 根据不同的行动类型进行处理
    if action == "SEARCH":
        # 执行新的搜索
        new_search_results = asyncio.run(agent.search_aggregator.search(data))
        agent.training_data.append({"from": "agent", "thought": thought, "action": action, "action_content": data, "action_result": new_search_results[:200]})

        ## 让模型记笔记
        new_notes = agent.taking_notes(new_search_results); agent.training_data.append({"from": "agent", "action": "TAKING_NOTES", "action_content": new_notes})
        # 递归调用自身处理新的搜索结果让模型决定下一步的行动
        return _action_router(agent, new_search_results, task, current_section,iteration, agent_report, guide_line, detailed_web_results)
        
    elif action == "BROWSE":
        # 执行网页爬取
        web_scraper_results = asyncio.run(
            agent.content_scraper.scrape(urls=data)
        )
        detailed_web_results+='\n\n'+web_scraper_results # 防止出现连续的browsing， 要把之前的browsing结果保存下来
        agent.training_data.append({"from": "agent", "thought": thought, "action": action, "action_content": data, "action_result": web_scraper_results[:200]})
        ## 让模型记笔记
        new_notes = agent.taking_notes(web_scraper_results); agent.training_data.append({"from": "agent", "action": "TAKING_NOTES", "action_content": new_notes})
        # 递归调用自身处理爬取结果让模型决定下一步的行动
        return _action_router(
            agent, search_results + '\n\n' + web_scraper_results, task, current_section,
            iteration, agent_report, guide_line, detailed_web_results
        )
        
    elif action == "START_WRITING":
        # 生成最终的内容
        section_content = agent.chat_with_template(
            "guided_generation_thought.txt",
            {
                "task": task,
                "context": "There is no previous context since this is the first section at the beginning of the article, only the user's question exists"
                if iteration == 0
                else f"Previous report content written by you is:\n\n{agent_report}",
                "guidline": guide_line,
                "search_result": detailed_web_results,
                "memo": agent.memo, # 每次模型写新的内容的时候都会可以看到之前所有的笔记
            }
        )

        writing_thought = extract_thought_from_response(section_content)
        writing_content = extract_answer_from_response(section_content)

        printer.rule("Generated Section Content")
        printer.print(section_content)
        agent.training_data.append({"from": "agent", "thought": writing_thought+'\n\n'+thought, "action": action, "action_content": writing_content, "citation": extract_citations(section_content)})

        return writing_content


def process_single_task(task, max_iterations, file_name=None):
    # Initialize agents
    agent = BaseAgent()
    agent.receive_task(task)
    agent.training_data = [
        {"from": "human", "value": task},
    ]
    agent.memo = set()
    search_agg = agent.search_aggregator
    verifier = ReportVerifier(agent)

    package_name = "criticsearch.reportbench.wiki_data"
    file_name = file_name or "2024_Syrian_opposition_offensives.json"

    with importlib.resources.files(package_name).joinpath(file_name) as json_file_path:
        json_file = str(json_file_path)

    benchmark = ReportBenchmark(json_file)
    outline = benchmark.generate_benchmark_item(max_window_tokens=200)

    # initialize the task
    agent.user_question = task

    printer.log(f"Starting the conversation with task: \n{task}")

    BaseAgent.conversation_manager.append_to_history(role="user", content=task)

    for iteration in range(max_iterations):
        printer.rule(f"ITERATION {iteration + 1}")

        if iteration == 0:
            # Initialize search_results as None
            search_results = None
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
                agent_report_sections = []

                for item in outline: # 遵循给定的GT wiki的内容进行滑动窗口大小的section生成
                    section_path = item["path"]
                    merged_section_content = item["merged_section_window_content"]
                    extracted_facts = item["extracted_facts"]

                    agent_report = "\n".join(agent_report_sections)

                    search_thought_and_queries = agent.chat_with_template(
                        "guided_search_thought.txt",
                        {
                            "task": task,
                            "context": "There is no previous context since this is the first section at the beginning of the article, only the user's question exists"
                            if iteration == 0
                            else f"Previous text written by the Agent is:\n\n{agent_report}",
                            "GroundTruth": merged_section_content,
                        },
                    )

                    thought_content = extract_thought_from_response(search_thought_and_queries)
                    queries_list = extract_queries_from_response(search_thought_and_queries)
                    printer.print(search_thought_and_queries)
                    search_results = asyncio.run(search_agg.search(queries_list))
                    agent.training_data.append({"from": "agent", "thought": thought_content, "action": "SEARCH", "action_content": queries_list, "action_result": search_results[:200]})
                    # detailed_web_results = agent.web_scrape_results(search_results)
                    new_notes = agent.taking_notes(search_results); agent.training_data.append({"from": "agent", "action": "TAKING_NOTES", "action_content": new_notes})

                    ## 从这里开始我们提供了详细的网页信息，由模型决定下一步的行动
                    ## 模型会根据上一次的搜索结果，决定下一步的行动
                    answer_content = _action_router(agent, search_results, task, section_path, iteration, agent_report, section_path, search_results) # 本次迭代模型生成的这一节（paragraph）内容


                    # 将生成的内容添加到agent_report_sections
                    agent_report_sections.append(answer_content)

                    # 使用verifier进行factual QA验证，得到这个段落写作的reward分数（也就是准确率）
                    accuracy = verifier.verify_section(answer_content, extracted_facts)
                    agent.training_data.append({"from": "verifier", "section": section_path, "accuracy": accuracy})


                # 拼接完整的report
                agent_answer = "\n".join(agent_report_sections)
                agent.training_data.append({"from": "agent", "final_report": agent_answer, "citation": extract_citations(agent_answer)})
                # 保存到一个json文件
                with open("conversation_data.json", "w", encoding="utf-8") as f:
                    json.dump(agent.training_data, f, indent=4, ensure_ascii=False)
                exit(1)

                # verify the outline is a json string
                outline_json = agent.extract_and_validate_json(outline)

                # Flatten the outline to get all sections at all levels
                flat_sections = flatten_outline(outline_json)

                # Generate content for all sections in parallel
                with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
                    future_to_section = {
                        executor.submit(
                            generate_content_for_section,
                            agent,
                            item["section"],
                            task,
                        ): item
                        for item in flat_sections
                    }

                    # Collect results as they complete
                    flat_contents = []
                    for future in concurrent.futures.as_completed(future_to_section):
                        item = future_to_section[future]
                        try:
                            content = future.result()
                            flat_contents.append((item, content))
                        except Exception:
                            printer.print_exception(
                                f"Error generating content for section {item['section'].get('title')}"
                            )

                # Reconstruct the markdown with proper hierarchy
                agent_answer = reconstruct_markdown(outline_json, flat_contents)
                printer.log(
                    agent_answer
                )  # 这里是第一次生成的report,还没有polish

                # 用deepseek润色一下到正式的version1 report
                polish_prompt = agent.load_template("polish_first_version.txt")
                polish_rendered_prompt = agent.render_template(
                    polish_prompt,
                    {
                        "task": task,
                        "report": agent_answer,
                    },
                )
                agent_answer = agent.chat_with_template(
                    "polish_first_version.txt",
                    {
                        "task": task,
                        "report": agent_answer,
                    },
                    model="gpt-4o",
                )
                printer.log(
                    agent_answer
                )  # 这里是第一次生成的正式的polished report
                # 保存到一个md
                with open("first_version_report.md", "w") as f:
                    f.write(agent_answer)

                # Polish后从markdown解析出文档结构
                document_structure = parse_markdown_to_structure(agent_answer)
                agent.document_structure = document_structure

                # 保存到一个json文件
                with open("document_structure.json", "w") as f:
                    json.dump(document_structure, f, indent=4, ensure_ascii=False)

        else:
            # 替换update answer调用
            agent_answer = agent.chat_with_template(
                "agent_update_answer.txt",
                {
                    "query": task,
                    "previous_answer": agent_answer,
                    "search_results": web_result_markdown_text,
                    "critic_feedback": critic_agent_response,
                },
            )

        # ========================== #
        ## 这里在if-else结构之外 ##
        printer.rule(f"AGENT ANSWER")
        printer.log(agent_answer)

        critic_agent = CriticAgent()
        critic_agent.receive_task(task)
        critic_agent.receive_agent_answer(agent_answer)
        critic_agent_response = critic_agent.chat_with_template(
            "critic_evaluation.txt", {"task": task, "answer": agent_answer}
        )
        printer.rule(f"CRITIC_AGENT_RESPONSE")
        printer.log(critic_agent_response)

        if yaml.safe_load(critic_agent_response).get("Stop", {}).lower() == "true":
            printer.rule(f"[red]TOTAL ITERATIONS: {iteration + 1}")
            printer.rule(f"ALL SEARCH QUERIES")
            printer.log(agent.queryDB)
            printer.rule(f"[red]FINAL ANSWER")
            printer.log(agent_answer)

            return f"\n{agent_answer}\n"

        # 根据critic的建议再执行一次搜索和爬虫操作
        # 先构建rendered_prompt
        reflection_data = {
            "user_question": task,
            "previous_answer": agent_answer,
            "user_feedback": critic_agent_response,
            "search_history": agent.queryDB,
        }
        search_again_prompt = agent.render_template(
            agent.load_template("planner_agent_with_reflection.txt"),
            reflection_data,
        )
        try:
            web_result_markdown_text = agent.search_and_browse(
                search_again_prompt
            )
        except:
            printer.rule(f"[red]TOTAL ITERATIONS: {iteration + 1}")
            printer.rule(f"ALL SEARCH QUERIES")
            printer.log(agent.queryDB)
            printer.rule(f"[red]FINAL ANSWER")
            printer.log(agent_answer)

            # we run out of searches for now, so we force the agent to give a final answer:
            return f"\n{agent_answer}\n"

        # Check if reached max iterations
        if iteration == max_iterations - 1:
            printer.rule(f"[red]TOTAL ITERATIONS: {iteration + 1}")
            printer.rule(f"ALL SEARCH QUERIES")
            printer.log(agent.queryDB)
            printer.rule(f"[red]FINAL ANSWER")
            printer.log(agent_answer)

            return f"\n{agent_answer}\n"

# 新增：命令行入口
def main():
    parser = argparse.ArgumentParser(description="Run CriticSearch pipeline")
    parser.add_argument("task", help="用户任务描述")
    parser.add_argument("--max-iterations", "-n", type=int, default=3, help="最大迭代次数")
    parser.add_argument("--file-name", "-f", default=None, help="GT 数据文件名")
    args = parser.parse_args()
    try:
        result = process_single_task(args.task, args.max_iterations, args.file_name)
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