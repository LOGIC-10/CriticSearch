import yaml

from .base_agent import BaseAgent
from .rich_output import printer


class CriticAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.original_task = ""
        self.critic_prompt = self.load_template("critic_agent.txt")

    def critic(self):
        """
        生成评论。
        """
        data = self.get_data_for_critic()

        rendered_prompt = self.render_template(self.critic_prompt, data)
        model_response = self.chat(usr_prompt=rendered_prompt, role="critic")

        try:
            formatted_yaml = self.extract_and_validate_yaml(model_response)
            return formatted_yaml

        except yaml.YAMLError:
            printer.print_exception(f"Invalid YAML content.")
            return None

    def receive_agent_answer(self, agent_answer):
        self.agent_answer = agent_answer

    def get_data_for_critic(self):
        return {"user_question": self.original_task, "agent_answer": self.agent_answer}
