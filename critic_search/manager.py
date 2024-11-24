# The Manager module is responsible for task scheduling and decomposition in the entire system. Its main responsibilities include:
#   • Receiving input tasks: Obtaining a complex task that needs to be completed from an external source.
#   • Analyzing tasks: Determining the complexity, type, and requirements of the task.
#   • Task decomposition: Breaking down the complex task into manageable sub-tasks or different levels.
#   • Task assignment: Preparing the sub-tasks for the subsequent AgentGenerator to generate corresponding Agents.

from critic_search.base_agent import BaseAgent


class Manager(BaseAgent):
    def __init__(self):
        super().__init__()
        self.original_task = ""
        self.sub_tasks = []
        self.breakdown_prompt = self.env.get_template("manager_break_down.txt")
        self.reflection_prompt = None

    def breakdown_task(self):
        """
        将任务拆解成子任务。
        """
        data = self.get_data_for_breakdown()
        return self.chat_with_template(data, self.breakdown_prompt)

    def get_data_for_breakdown(self):
        return {"task": self.original_task}


if __name__ == "__main__":
    manager = Manager()

    task = """Assuming scientists in the famous youtube video The Thinking Machine (Artificial Intelligence in the 1960s) were interviewed the same year, what is the name of the scientist predicting the sooner thinking machines or robots? Answer using the format First name Last name"""
    manager.receive_task(task)
    response_message = manager.breakdown_task()
    print(f"Decompose:\n\n{response_message}")
