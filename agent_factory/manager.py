# The Manager module is responsible for task scheduling and decomposition in the entire system. Its main responsibilities include:
#   • Receiving input tasks: Obtaining a complex task that needs to be completed from an external source.
#   • Analyzing tasks: Determining the complexity, type, and requirements of the task.
#   • Task decomposition: Breaking down the complex task into manageable sub-tasks or different levels.
#   • Task assignment: Preparing the sub-tasks for the subsequent AgentGenerator to generate corresponding Agents.

from config import read_config
from utils import read_prompt_template
import os

class Manager:
    def __init__(self):
        self.original_task = ''
        self.sub_tasks = []
        self.config = read_config()
        self.model = self.config.get('default_model')
        self.sys_prompt = ''
        self.breakdown_prompt = read_prompt_template(os.path.join(self.config.get('prompt_folder_path'), 'manager_break_down.txt'))
        self.reflection_prompt = None
        self.repeat_turns = 10


    def receive_task(self, task):
        """
        接收原始任务。
        """
        self.original_task = task
        print(f"Manager received task: {self.original_task}")

    def breakdown_task(self):
        """
        将任务拆解成子任务。
        """

manager = Manager()
manager.receive_task("I want to book a flight ticket.")

print(manager.breakdown_prompt)

print(manager.config)       