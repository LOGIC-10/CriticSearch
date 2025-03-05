import time

import yaml

from .base_agent import BaseAgent
from .config import settings
from .critic_agent import CriticAgent
from .log import colorize_message, logger, set_logger_level_from_config


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
                common_agent_answer = common_agent.chat(usr_prompt=TASK)
            else:
                # When not confident, start searching information
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
                )
                logger.info(f"Initial web result: {initial_web_result_markdown_text}")

                rag_based_answer_prompt = common_agent.render_template(
                    common_agent.load_template("rag_based_answer.txt"),
                    {
                        "user_question": common_agent.user_question,
                        "web_result_markdown_text": initial_web_result_markdown_text,
                    },
                )

                common_agent_answer = common_agent.chat(
                    usr_prompt=rag_based_answer_prompt,
                )

        else:
            # 前面根据critc的返回得到了新的网页搜索结果web_result_markdown_text
            common_agent_answer = common_agent.update_answer(
                query=TASK,
                previous_answer=common_agent_answer,
                search_results=web_result_markdown_text,
                critic_feedback=critic_agent_response,
            )
            time.sleep(0.5)  # hitting rate limits for gpt mini

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
