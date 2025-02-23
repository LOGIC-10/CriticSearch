import json
import time
import concurrent.futures

import yaml

from .base_agent import BaseAgent
from .config import settings
from .critic_agent import CriticAgent
from .log import colorize_message, logger, set_logger_level_from_config



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
    使用完整路径作为key确保唯一性
    """
    # 构建以完整路径为键的映射字典
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

def main(TASK, MAX_ITERATION):
    # Initialize agents
    common_agent = BaseAgent()

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
            agent_confident = common_agent.model_confident(TASK)
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
                # When confident, only get the answer
                common_agent_answer = common_agent.common_chat(usr_prompt=TASK)
            else:
                # When not confident, get both answer and search results
                # 并且第一次全面的搜索后的结果用来构建一个report的结构
                data = {
                    "user_question": TASK,
                }
                initial_search_prompt = common_agent.load_template(
                    "planner_agent_initial_search_plan.txt"
                )
                initial_search_rendered_prompt = common_agent.render_template(
                    initial_search_prompt, data
                )
                logger.info(
                    f"initial_search_rendered_prompt: {initial_search_rendered_prompt}"
                )

                initial_web_result_markdown_text = common_agent.search_and_browse(
                    initial_search_rendered_prompt
                )# 这里返回的是模型决定了访问哪些后的网页爬取extract的结果

                logger.info(f"Initial web result: {initial_web_result_markdown_text}")

                # Generate report outline based on search results
                outline_prompt = common_agent.render_template(
                    common_agent.load_template("outline_generation.txt"),
                    {
                        "user_question": common_agent.user_question,
                        "web_result_markdown_text": initial_web_result_markdown_text,
                    },
                )

                outline = common_agent.common_chat(
                    usr_prompt=outline_prompt,
                )

                # verify the outline is a json string   
                outline_json = common_agent.extract_and_validate_json(outline)
                
                # Flatten the outline to get all sections at all levels
                flat_sections = flatten_outline(outline_json)
                
                # Generate content for all sections in parallel
                with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
                    future_to_section = {
                        executor.submit(generate_content_for_section, common_agent, item["section"], TASK): item 
                        for item in flat_sections[:3]
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
                # 用deepseek润色一下得到正式的version1 report
                polish_prompt = common_agent.load_template("polish_first_version.txt")
                polish_rendered_prompt = common_agent.render_template(
                    polish_prompt,
                    {
                        "task": TASK,
                        "report": common_agent_answer,
                    },
                )
                common_agent_answer = common_agent.common_chat(
                    usr_prompt=polish_rendered_prompt,
                    model="gpt-4o"
                )
                print(common_agent_answer)  # 这里是第一次生成的正式的polished report

                # 保存第一次生成的report    
                with open("first_report.md", "w") as f:
                    f.write(common_agent_answer)
 
        else:
            # 前面根据critc的返回得到了新的网页搜索结果web_result_markdown_text
            common_agent_answer = common_agent.update_answer(
                query=TASK,
                previous_answer=common_agent_answer,
                search_results=web_result_markdown_text,
                critic_feedback=critic_agent_response,
            )
            time.sleep(0.1)  # hitting rate limits for gpt mini

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
        critic_agent_response = critic_agent.critic()

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
