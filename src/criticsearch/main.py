import asyncio
import json
import time
import concurrent.futures
import re

import yaml

from criticsearch.reportbench.report_benchmark import ReportBenchmark
from .base_agent import BaseAgent
from .config import settings
from .critic_agent import CriticAgent
from .log import colorize_message, logger, set_logger_level_from_config
from .utils import extract_answer_from_response, extract_queries_from_response, extract_thought_from_response
from .tools.search_adapter.search_aggregator import SearchAggregator
from criticsearch.reportbench.verifier import ReportVerifier  # 添加verifier的引用

def flatten_outline(section, depth=1, path=None):
    # 将 outline_json 展平，记录每个节点及其层级和路径
    if path is None:
        path = []
    current = {"path": path + [section.get("title")], "section": section, "depth": depth}
    flat = [current]
    if "children" in section:
        for child in section["children"]:
            flat.extend(flatten_outline(child, depth + 1, path + [section.get("title")]))
    return flat

def generate_content_for_section(common_agent, section, TASK):
    # 保持 prompt 不变，仅生成单层章节内容，不递归
    title = section.get("title")
    search_query = f"generate some search queries about '{title}' under the background of this TOPIC/TASK: '{TASK}'."
    search_results = common_agent.search_and_browse(search_query)
    prompt = (
        f"Using the following search results:\n\n{search_results}\n\n"
        f"Write one or several detailed paragraphs with data and facts in a logical way about '{title}' under the background of this TOPIC/TASK: '{TASK}', formatted in pure text, without summary sentences."
        f"Please make sure you are always obeying and using '<\cite>The url link that you used for supporting the previous statement<\cite>' format in every sentence that you are using data from the web."
    )
    paragraph = common_agent.common_chat(usr_prompt=prompt)
    print(f"--- Generated content for '{title}' ---")
    print(paragraph)
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

def extract_citations(text):
    """从文本中提取引用的URLs"""
    citations = []
    pattern = r'<cite>(.*?)<\/cite>'
    matches = re.findall(pattern, text)
    return matches

def create_document_structure(outline_json, flat_contents):
    """
    基于outline结构和生成的内容创建文档结构
    """
    document = {
        "document": {
            "title": outline_json.get("title", ""),
            "level": 1,
            "subsections": []
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
        
        section_data = {
            "title": section.get("title"),
            "level": depth,
            "paragraphs": []
        }
        
        # 如果有内容，处理段落
        if path_key in content_map:
            content = content_map[path_key]
            paragraphs = content.split('\n\n')  # 假设段落用空行分隔
            for para in paragraphs:
                if para.strip():  # 忽略空段落
                    citations = extract_citations(para)
                    paragraph_data = {
                        "text": para.strip(),  # 保留原始文本，包括cite标记
                        "citations": citations
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
        doc_section = process_section(section, 2, [outline_json.get("title")] if "title" in outline_json else [])
        document["document"]["subsections"].append(doc_section)
    
    return document

def parse_markdown_to_structure(markdown_text):
    """从markdown文本解析出文档结构"""
    lines = markdown_text.split('\n')
    document = {
        "document": {
            "title": "",
            "level": 1,
            "subsections": []
        }
    }
    
    current_section = document["document"]
    section_stack = [current_section]
    current_level = 1
    current_text = []
    
    for line in lines:
        if line.strip():
            # 处理标题
            if line.startswith('#'):
                # 如果有待处理的段落文本，先处理完
                if current_text:
                    paragraph_text = ' '.join(current_text)
                    if paragraph_text.strip():
                        citations = extract_citations(paragraph_text)
                        current_section.setdefault("paragraphs", []).append({
                            "text": paragraph_text.strip(),
                            "citations": citations
                        })
                    current_text = []
                
                # 处理新标题
                level = len(line.split()[0])  # 计算#的数量
                title = ' '.join(line.split()[1:])
                
                # 根据层级调整当前section
                while len(section_stack) > 1 and level <= section_stack[-1]["level"]:
                    section_stack.pop()
                
                new_section = {
                    "title": title,
                    "level": level,
                    "subsections": [],
                    "paragraphs": []
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
                paragraph_text = ' '.join(current_text)
                if paragraph_text.strip():
                    citations = extract_citations(paragraph_text)
                    current_section.setdefault("paragraphs", []).append({
                        "text": paragraph_text.strip(),
                        "citations": citations
                    })
                current_text = []
    
    # 处理最后一个段落
    if current_text:
        paragraph_text = ' '.join(current_text)
        if paragraph_text.strip():
            citations = extract_citations(paragraph_text)
            current_section.setdefault("paragraphs", []).append({
                "text": paragraph_text.strip(),
                "citations": citations
            })

    return document


def main(TASK, MAX_ITERATION):
    # Initialize agents
    common_agent = BaseAgent()
    search_agg = SearchAggregator()
    verifier = ReportVerifier(common_agent)  # 初始化verifier

    json_file = "/workspaces/CriticSearch/src/criticsearch/reportbench/wiki_data/2024_Syrian_opposition_offensives.json"
    benchmark = ReportBenchmark(json_file)
    outline = benchmark.generate_benchmark_item()

    conversation_data = [
        {
            "from": "huamn",
            "value": TASK   
        }
    ]

    # initialize the task
    common_agent.user_question = TASK

    set_logger_level_from_config(log_level=settings.log_level.upper())

    logger.success(f"Starting the conversation with task: {TASK}")

    BaseAgent.conversation_manager.append_to_history(role="user", content=TASK)

    for iteration in range(MAX_ITERATION):
        colorize_message(
            message_title=f"ITERATION {iteration + 1}", color="cyan", style="bold"
        )

        if iteration == 0:
            # Initialize search_results as None
            search_results = None

            # Model confidence check - yellow
            agent_confident = common_agent.chat_with_template(
                "agent_confidence.txt",
                {"user_question": TASK}
            )
            agent_confident_yaml = common_agent.extract_and_validate_yaml(
                agent_confident
            )

            if agent_confident_yaml is None:
                logger.warning(
                    "Failed to extract valid YAML content. Defaulting to 'false'."
                )
                agent_confident = False
            else:
                agent_confident_dict = yaml.safe_load(agent_confident_yaml)
                agent_confident = (
                    agent_confident_dict.get("confidence", "true").lower() == "true"
                )

            if agent_confident:
                # 使用chat_with_template替换direct chat
                common_agent_answer = common_agent.chat_with_template(
                    "direct_response.txt",
                    {"task": TASK}
                )
            else:
                agent_report_sections = []

                for item in outline:
                    section_path = item["path"]
                    merged_section_content = item["merged_section_window_content"]
                    extracted_facts = item["extracted_facts"]   

                    angent_report = '\n'.join(agent_report_sections)

                    search_thought_and_queries = common_agent.chat_with_template(
                        "guided_search_thought.txt",
                        {
                            "TASK": TASK,
                            "context": "There is no previous context since this is the first section at the beginning of the article, only the user's question exists" if iteration == 0 else f"Previous text written by the Agent is:\n\n{angent_report}",
                            "GroundTruth": merged_section_content,
                        }
                    )
                    
                    # 提取thought内容
                    thought_content = extract_thought_from_response(search_thought_and_queries)
                    if thought_content:
                        print(f"Extracted thought process: {thought_content}")
                    else:
                        logger.warning("No thought process found in the response")
                    
                    # 提取查询列表,最多尝试5次
                    max_retries = 5
                    retry_count = 0
                    queries_list = None
                    
                    while (retry_count < max_retries):
                        queries_list = extract_queries_from_response(search_thought_and_queries)
                        if queries_list and isinstance(queries_list, list) and len(queries_list) > 0:
                            print(f"Extracted queries: {queries_list}")
                            conversation_data.append({
                                "from": "agent",
                                "thougth": thought_content,
                                "search": queries_list,
                            })
                            break
                        
                        logger.warning(f"Attempt {retry_count + 1}: Invalid or empty queries, retrying...")
                        # 重新生成��索思维和查询
                        search_thought_and_queries = common_agent.chat_with_template(
                            "guided_search_thought.txt",
                            {
                                "TASK": TASK,
                                "context": "There is no previous context since this is the first section at the beginning of the article, only the user's question exists" if iteration == 0 else f"Previous text written by the Agent is:\n\n{angent_report}",
                                "GroundTruth": merged_section_content,
                            }
                        )
                        retry_count += 1
                    
                    if retry_count == max_retries:
                        logger.error("Failed to extract valid queries after maximum retries")
                        continue  # 跳过当���section,处理下一个
                        
                    print(search_thought_and_queries)
                    search_results = asyncio.run(search_agg.search(queries_list))
                    detailed_web_results = common_agent.web_scrape_results(search_results)

                    # 生成section内容   
                    section_content = common_agent.chat_with_template(
                        "guided_generation_thought.txt",
                        {
                            "TASK": TASK,
                            "context": "There is no previous context since this is the first section at the beginning of the article, only the user's question exists" if iteration == 0 else f"Previous report content written by you is:\n\n{angent_report}",
                            "guidline": section_path,
                            "search_result": detailed_web_results,
                        }
                    )

                    print("--------- Section Content ---------")
                    print(section_content)
                    print("----------------------------------")

                    # 分别提取thought和answer，citation
                    thought_content = extract_thought_from_response(section_content)
                    answer_content = extract_answer_from_response(section_content)
                    citations = extract_citations(answer_content)

                    
                    # 将生成的内容添加到agent_report_sections
                    agent_report_sections.append(answer_content)

                    conversation_data.append(
                        {
                            "from": "agent",
                            "thougth": thought_content,
                            "answer": answer_content,
                            "citations": citations,
                        }
                    )

                    # 使用verifier进行factual QA验证
                    accuracy = verifier.verify_section(answer_content, extracted_facts)
                    conversation_data.append({
                        "from": "verifier",
                        "accuracy": accuracy,
                        "section": section_path
                    })




                # 保存到一个json文件
                with open("conversation_data.json", "w") as f:
                    json.dump(conversation_data, f, indent=4, ensure_ascii=False)


                exit(1)


                # verify the outline is a json string   
                outline_json = common_agent.extract_and_validate_json(outline)
                
                # Flatten the outline to get all sections at all levels
                flat_sections = flatten_outline(outline_json)
                
                # Generate content for all sections in parallel
                with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
                    future_to_section = {
                        executor.submit(generate_content_for_section, common_agent, item["section"], TASK): item 
                        for item in flat_sections
                    }
                    
                    # Collect results as they complete
                    flat_contents = []
                    for future in concurrent.futures.as_completed(future_to_section):
                        item = future_to_section[future]
                        try:
                            content = future.result()
                            flat_contents.append((item, content))
                        except Exception as e:
                            logger.error(f"Error generating content for section {item['section'].get('title')}: {e}")
                
                # Reconstruct the markdown with proper hierarchy
                common_agent_answer = reconstruct_markdown(outline_json, flat_contents)
                print(common_agent_answer)  # 这里是第一次生成的report,还没有polish

                # 用deepseek润色一下得到正式的version1 report
                polish_prompt = common_agent.load_template("polish_first_version.txt")
                polish_rendered_prompt = common_agent.render_template(
                    polish_prompt,
                    {
                        "task": TASK,
                        "report": common_agent_answer,
                    },
                )
                common_agent_answer = common_agent.chat_with_template(
                    "polish_first_version.txt",
                    {
                        "task": TASK,
                        "report": common_agent_answer,
                    },
                    model="gpt-4o"
                )
                print(common_agent_answer)  # 这里是第一次生成的正式的polished report
                # 保存到一个md
                with open("first_version_report.md", "w") as f:
                    f.write(common_agent_answer)

                # Polish后从markdown解析出文档结构
                document_structure = parse_markdown_to_structure(common_agent_answer)
                common_agent.document_structure = document_structure

                # 保存到一个json文件
                with open("document_structure.json", "w") as f:
                    json.dump(document_structure, f, indent=4, ensure_ascii=False)
 
        else:
            # 替换update answer调用
            common_agent_answer = common_agent.chat_with_template(
                "agent_update_answer.txt",
                {
                    "query": TASK,
                    "previous_answer": common_agent_answer,
                    "search_results": web_result_markdown_text,
                    "critic_feedback": critic_agent_response,
                }
            )

        # ========================== #
        ## 这里在if-else结构之外 ##
        colorize_message(
            message_title="COMMON AGENT ANSWER",
            color="magenta",
            message_content=common_agent_answer,
        )

        # Critic evaluation - blue
        critic_agent = CriticAgent()
        critic_agent.receive_task(TASK)
        critic_agent.receive_agent_answer(common_agent_answer)
        critic_agent_response = critic_agent.chat_with_template(
            "critic_evaluation.txt",
            {
                "task": TASK,
                "answer": common_agent_answer
            }
        )

        colorize_message(
            message_title="CRITIC_AGENT_RESPONSE",
            color="blue",
            message_content=critic_agent_response,
        )

        if yaml.safe_load(critic_agent_response).get("Stop", {}).lower() == "true":
            colorize_message(
                message_title=f"TOTAL ITERATIONS: {iteration + 1}", color="red"
            )

            colorize_message(
                message_title="ALL SEARCH QUERIES",
                color="black",
                message_content=", ".join(map(str, common_agent.queryDB)),
            )
            colorize_message(
                message_title="FINAL ANSWER",
                color="red",
                message_content=common_agent_answer,
            )

            return f"\n{common_agent_answer}\n"

        # 根据critic的建议再执行一次搜索和爬虫操作
        # 先构建rendered_prompt
        reflection_data = {
            "user_question": TASK,
            "previous_answer": common_agent_answer,
            "user_feedback": critic_agent_response,
            "search_history": common_agent.queryDB,
        }
        search_again_prompt = common_agent.render_template(
            common_agent.load_template("planner_agent_with_reflection.txt"),
            reflection_data,
        )
        try:
            web_result_markdown_text = common_agent.search_and_browse(
                search_again_prompt
            )
        except:
            colorize_message(
                message_title=f"TOTAL ITERATIONS: {iteration + 1}", color="red"
            )

            colorize_message(
                message_title="ALL SEARCH QUERIES",
                color="black",
                message_content=", ".join(map(str, common_agent.queryDB)),
            )

            colorize_message(
                message_title="FINAL ANSWER",
                color="red",
                message_content=common_agent_answer,
            )

            # we run out of searches for now, so we force the agent to give a final answer:
            return f"\n{common_agent_answer}\n"

        # Check if reached max iterations
        if iteration == MAX_ITERATION - 1:
            colorize_message(
                message_title=f"TOTAL ITERATIONS: {iteration + 1}", color="red"
            )

            colorize_message(
                message_title="ALL SEARCH QUERIES",
                color="black",
                message_content=", ".join(map(str, common_agent.queryDB)),
            )

            colorize_message(
                message_title="FINAL ANSWER",
                color="red",
                message_content=common_agent_answer,
            )

            return f"\n{common_agent_answer}\n"
