import yaml
from colorama import Fore, Style, init
from loguru import logger

from .base_agent import BaseAgent
from .critic_agent import CriticAgent
from .search_plan_agent import SearchPlanAgent



def main(TASK, MAX_ITERATION=10):
    
    # Initialize agents
    common_agent = BaseAgent()
    plan_agent = SearchPlanAgent()

    # initialize the task
    common_agent.user_question = TASK

    # Define the tool schema for function calling
    common_agent.search_tool = [common_agent.tool_registry.get_tool_schema(common_agent.search_aggregator.search)]
    common_agent.web_scrape_tool = [common_agent.tool_registry.get_tool_schema(common_agent.web_scraper.scrape)]
    common_agent.search_tool_schema_list = common_agent.search_tool + common_agent.web_scrape_tool

    # Initialize colorama
    init()

    for iteration in range(MAX_ITERATION):
        # Iteration header with bold cyan
        logger.info(
            f"\n{Fore.CYAN}{Style.BRIGHT}{'=' * 20}== Iteration {iteration + 1} =={'=' * 20}{Style.RESET_ALL}\n"
        )

        if iteration == 0:
            # Initialize search_results as None
            search_results = None
            
            # Model confidence check - yellow
            agent_confident = common_agent.model_confident(TASK)
            agent_confident_yaml = common_agent.extract_and_validate_yaml(agent_confident)

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
                data = {
                    "user_question": TASK,
                }
                initial_search_prompt = common_agent.load_template(
                    "planner_agent_initial_search_plan.txt"
                )
                initial_search_rendered_prompt = common_agent.render_template(initial_search_prompt, data)

                initial_web_result_markdown_text = common_agent.search_and_browse(
                    initial_search_rendered_prompt
                )

                common_agent_answer = common_agent.initialize_search(
                    web_result_markdown_text=initial_web_result_markdown_text
                )

        else:
            # 前面根据critc的返回得到了新的网页搜索结果web_result_markdown_text
            common_agent_answer = common_agent.update_answer(
                query=TASK,
                previous_answer=common_agent_answer,
                search_results=web_result_markdown_text,
                critic_feedback=critic_agent_response,
            )

        # Agent answer - magenta
        logger.info(
            f"\n{Fore.MAGENTA}{'=' * 20}== COMMON_AGENT_ANSWER =={'=' * 20}{Style.RESET_ALL}\n{common_agent_answer}\n"
        )

        # Critic evaluation - blue
        critic_agent = CriticAgent()
        critic_agent.receive_task(TASK)
        critic_agent.receive_agent_answer(common_agent_answer)
        critic_agent_response = critic_agent.critic()
        logger.info(
            f"\n{Fore.BLUE}{'=' * 20}== CRITIC_AGENT_RESPONSE =={'=' * 20}{Style.RESET_ALL}\n{critic_agent_response}\n"
        )

        if yaml.safe_load(critic_agent_response).get("Stop", {}).lower() == "true":
            logger.info(
                f"\n{Fore.RED}{'=' * 20}== TOTAL ITERATIONS: {iteration + 1} =={'=' * 20}{Style.RESET_ALL}\n"
            )
            logger.info(
                f"\n{Fore.BLACK}{'=' * 20}== ALL SEARCH QUERIES =={'=' * 20}{Style.RESET_ALL}\n{common_agent.queryDB}\n"
            )
            logger.info(
                f"\n{Fore.RED}{'=' * 20}== FINAL ANSWER =={'=' * 20}{Style.RESET_ALL}\n{common_agent_answer}\n"
            )
            return f"\n{Fore.RED}{'=' * 20}== FINAL ANSWER =={'=' * 20}{Style.RESET_ALL}\n{common_agent_answer}\n"

        # 根据critic的建议再执行一次搜索和爬虫操作
        # 先构建rendered_prompt
        reflection_data = {
            "user_question": TASK,
            "previous_answer": common_agent_answer,
            "user_feedback": critic_agent_response,
            "search_history": common_agent.queryDB,
        }
        search_again_prompt = common_agent.render_template(common_agent.load_template("planner_agent_with_reflection.txt"), reflection_data)
        web_result_markdown_text = common_agent.search_and_browse(search_again_prompt)
        logger.info(
            f"\n{Fore.BLUE}{'=' * 20}== WEB_RESULT_MARKDOWN_TEXT =={'=' * 20}{Style.RESET_ALL}\n{web_result_markdown_text}\n"
        )

        # Check if reached max iterations
        if iteration == MAX_ITERATION - 1:
            logger.info(
                f"\n{Fore.RED}{'=' * 20}== TOTAL ITERATIONS: {iteration + 1} =={'=' * 20}{Style.RESET_ALL}\n"
            )
            logger.info(
                f"\n{Fore.BLACK}{'=' * 20}== ALL SEARCH QUERIES =={'=' * 20}{Style.RESET_ALL}\n{common_agent.queryDB}\n"
            )
            logger.info(
                f"\n{Fore.RED}{'=' * 20}== FINAL ANSWER =={'=' * 20}{Style.RESET_ALL}\n{common_agent_answer}\n"
            )
            return f"\n{Fore.RED}{'=' * 20}== FINAL ANSWER =={'=' * 20}{Style.RESET_ALL}\n{common_agent_answer}\n"


if __name__ == "__main__":
    main()
