import yaml
from colorama import Fore, Style, init
from loguru import logger

from .base_agent import BaseAgent
from .critic_agent import CriticAgent
from .search_plan_agent import SearchPlanAgent

# Constants
MAX_ITERATION = 10
TASK = """
Did the car bombing in 1993 resulted in 6 deaths had a higher number of death than the train wreck in 1989 resulted in 645 deaths?
"""


# Initialize agents
common_agent = BaseAgent()
plan_agent = SearchPlanAgent()

# Initialize colorama
init()


def main():
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
                initial_search_prompt = common_agent.env.get_template(
                    "planner_agent_initial_search_plan.txt"
                )
                initial_search_rendered_prompt = initial_search_prompt.render(**data)

                common_agent_answer, search_results = common_agent.initialize_search(
                    search_rendered_prompt=initial_search_rendered_prompt, user_question=TASK
                )

        else:
            common_agent_answer = common_agent.update_answer(
                query=TASK,
                previous_answer=common_agent_answer,
                search_results=search_results,
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
            break

        # Next search plan - green
        plan_agent.receive_task(TASK)
        plan_agent.plan(common_agent_answer, critic_agent_response)

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


if __name__ == "__main__":
    main()
