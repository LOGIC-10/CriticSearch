import logging

import yaml
from colorama import Fore, Style, init

from .base_agent import BaseAgent
from .critic_agent import CriticAgent
from .search_plan_agent import SearchPlanAgent

# Constants
MAX_ITERATION = 50
TASK = """I was trying to remember how well the Cheater Beater performed in comparison to the Cheater when James tested it on his channel. I know that the Cheater still outperformed the Cheater Beater in terms of CFM. Could you please look that up for me, and report the CFM of both the Cheater and the Cheater Beater? I'm not sure if he made any changes to his testing, but this was back in season 4, so just report the value from that season. Please format your response like this: CFM number for Cheater, CFM number for Cheater beater"""


# Initialize agents
common_agent = BaseAgent()
plan_agent = SearchPlanAgent()

# Initialize colorama
init()


# Configure logger
def setup_logger():
    logger = logging.getLogger("AgentLogger")
    logger.setLevel(logging.INFO)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    logger.addHandler(ch)
    return logger


logger = setup_logger()


def main():
    for iteration in range(MAX_ITERATION):
        # Iteration header with bold cyan
        logger.info(
            f"\n{Fore.CYAN}{Style.BRIGHT}{'=' * 20}== Iteration {iteration + 1} =={'=' * 20}{Style.RESET_ALL}\n"
        )

        if iteration == 0:
            # Model confidence check - yellow
            agent_confident = common_agent.model_confident(TASK)
            agent_confident = (
                yaml.safe_load(common_agent.extract_and_validate_yaml(agent_confident))
                .get("confidence", "true")
                .lower()
                == "true"
            )
            logger.info(
                f"\n{Fore.YELLOW}{'=' * 20}== MODEL_CONFIDENT =={'=' * 20}{Style.RESET_ALL}\n{agent_confident}\n"
            )

            if agent_confident:
                common_agent_answer = common_agent.common_chat(query=TASK)
            else:
                # Search plan - green
                search_plan = common_agent.initialize_search(TASK)
                search_plan = common_agent.extract_and_validate_yaml(search_plan)
                logger.info(
                    f"\n{Fore.GREEN}{'=' * 20}== AGENT_SEARCH_PLAN =={'=' * 20}{Style.RESET_ALL}\n{search_plan}\n"
                )

                initial_search_queries = [
                    item["Query"]
                    for item in yaml.safe_load(search_plan).get("SearchQueries", [])
                ]
                logger.info(
                    f"\n{Fore.GREEN}{'=' * 20}== INITIAL_SEARCH_PLAN =={'=' * 20}{Style.RESET_ALL}\n{initial_search_queries}\n"
                )

                common_agent.queryDB.update(initial_search_queries)
                search_results = common_agent.search_aggregator.search(
                    initial_search_queries
                )
                logger.info(
                    f"\n{Fore.GREEN}{'=' * 20}== INITIAL_SEARCH_RESULTS =={'=' * 20}{Style.RESET_ALL}\n{search_results}\n"
                )

                search_prompt = (
                    f"Answer user question based on the following search results. \n\n"
                    f"Here is the user question: {TASK}\n\n"
                    f"And here are the search results:\n\n{search_results}"
                )
                common_agent_answer = common_agent.common_chat(query=search_prompt)
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
        next_search_plan = plan_agent.plan(common_agent_answer, critic_agent_response)
        new_queries = [
            item["Query"]
            for item in yaml.safe_load(next_search_plan).get("NewSearchQueries", [])
        ]
        logger.info(
            f"\n{Fore.GREEN}{'=' * 20}== AGENT_NEXT_SEARCH_PLAN =={'=' * 20}{Style.RESET_ALL}\n{next_search_plan}\n"
        )

        # Search results - green
        common_agent.queryDB.update(new_queries)
        search_results = common_agent.search_aggregator.search(new_queries)
        logger.info(
            f"\n{Fore.GREEN}{'=' * 20}== SEARCH_RESULTS =={'=' * 20}{Style.RESET_ALL}\n{search_results}\n"
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


if __name__ == "__main__":
    main()
