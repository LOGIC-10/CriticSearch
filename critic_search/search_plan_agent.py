from colorama import Fore, Style, init
from loguru import logger

from .base_agent import BaseAgent


class SearchPlanAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.original_task = ""
        self.reflection_and_plan_prompt = self.load_template(
            "planner_agent_with_reflection.txt"
        )

    def plan(self, common_agent_answer, critic_feedback):
        """
        生成计划。
        """
        data = {
            "user_question": self.original_task,
            "previous_answer": common_agent_answer,
            "user_feedback": critic_feedback,
            "search_history": BaseAgent.queryDB,
        }

        reflection_and_plan_rendered_prompt = self.render_template(self.reflection_and_plan_prompt, data)

        search_plan_agent_answer, search_result = self.initialize_search(
            search_rendered_prompt=reflection_and_plan_rendered_prompt
        )

        self.history.append({"role": "planner", "content": search_plan_agent_answer})
