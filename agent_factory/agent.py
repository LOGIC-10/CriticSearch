# import os
# from autogen import AssistantAgent, UserProxyAgent
# from autogen import ConversableAgent
# from config import read_config

# config = read_config()
# model = config.get('default_model',"gpt-4o-mini")
# api_key = config.get("models").get(model).get("api_key")
# base_url = config.get("models").get(model).get("base_url")

# llm_config = { "config_list": [{ "model": model, "api_key": api_key }], "base_url": base_url}


# # 定义一个critic agent
# critic_agent = ConversableAgent(
#     "CriticAgent",
#     system_message="Your name is Cathy and you are a part of a duo of comedians.",
#     llm_config=llm_config,
#     human_input_mode="NEVER",  # Never ask for human input.
# )

# # 填充prompt模板内容   

# # 使用 critic agent 生成回复
# critic_agent_reply = critic_agent.generate_reply(messages=[{"content": "Tell me a joke.", "role": "user"}])
# print(critic_agent_reply)

from config import read_config
import os

from jinja2 import Environment, FileSystemLoader
from utils import call_llm


class BaseAgent:
    def __init__(self):
        self.config = read_config()
        self.model = self.config.get('default_model', "gpt-4o-mini")
        self.env = Environment(loader=FileSystemLoader(self.config.get('prompt_folder_path')))
        self.sys_prompt = ''
        self.repeat_turns = 10

    
    def chat(self, data, prompt_template):
        """
        通用的聊天方法，根据传入的data字典适配不同的prompt。
        """
        rendered_prompt = prompt_template.render(**data)
        # print(rendered_prompt)
        response_message = call_llm(model=self.model, sys_prompt=self.sys_prompt, usr_prompt=rendered_prompt, config=self.config)
        return response_message