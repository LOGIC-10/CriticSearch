# The Manager module is responsible for task scheduling and decomposition in the entire system. Its main responsibilities include:
#   • Receiving input tasks: Obtaining a complex task that needs to be completed from an external source.
#   • Analyzing tasks: Determining the complexity, type, and requirements of the task.
#   • Task decomposition: Breaking down the complex task into manageable sub-tasks or different levels.
#   • Task assignment: Preparing the sub-tasks for the subsequent AgentGenerator to generate corresponding Agents.

from config import read_config
import os

from jinja2 import Environment, FileSystemLoader
from utils import call_llm

class Manager:
    def __init__(self):
        self.original_task = ''
        self.sub_tasks = []
        self.config = read_config()
        self.model = self.config.get('default_model',"gpt-4o-mini")
        self.env = Environment(loader=FileSystemLoader(self.config.get('prompt_folder_path')))
        self.sys_prompt = ''
        self.breakdown_prompt = self.env.get_template('manager_break_down.txt')
        self.reflection_prompt = None
        self.repeat_turns = 10


    def receive_task(self, task):
        """
        接收原始任务。
        """
        self.original_task = task

    def breakdown_task(self):
        """
        将任务拆解成子任务。
        """
        data = {
            'task': self.original_task
        }
        rendered_prompt = self.breakdown_prompt.render(**data)
        response_message = call_llm(model=self.model,sys_prompt=self.sys_prompt,usr_prompt=rendered_prompt,config=self.config)
        return response_message


manager = Manager()

task = """Assuming scientists in the famous youtube video The Thinking Machine (Artificial Intelligence in the 1960s) were interviewed the same year, what is the name of the scientist predicting the sooner thinking machines or robots? Answer using the format First name Last name"""
manager.receive_task(task)
response_message = manager.breakdown_task()
# print(f"Decompose:\n\n{response_message}")



