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

import yaml
from agent_factory.config import read_config
import os

from jinja2 import Environment, FileSystemLoader
from agent_factory.utils import call_llm


class BaseAgent:
    def __init__(self):
        self.config = read_config()
        self.model = self.config.get('default_model', "gpt-4o-mini")
        self.env = Environment(loader=FileSystemLoader(self.config.get('prompt_folder_path')))
        # 定一个通用格式,queryDB应该是一个set,里面每个元素是一个query
        self.queryDB = set() # 对于citationDB,应该是一个字典，key是query，value是内容和来源
        # 这个列表中的每个元素都是一个字典，代表一个搜索的问题以及对应的搜索结果
        self.citationDB = [{ # citationDB中只会把受到critic表扬的搜索结果加入
            "why do we say google was facing challenges in 2019?": {
                "document_id":{ # 这个document_id是一个唯一的标识符，用于标识这个文档
                    "url": "",
                    "title": "",
                    "content": ""
                }
            }
        }]
        self.sys_prompt = ''
        self.repeat_turns = 10

    def common_chat(self, query):
        return call_llm(model=self.model, sys_prompt=self.sys_prompt, usr_prompt=query, config=self.config)
    
    def chat_with_template(self, data, prompt_template):
        """
        通用的聊天方法，根据传入的data字典适配不同的prompt。
        """
        rendered_prompt = prompt_template.render(**data)
        # print(rendered_prompt)
        response_message = self.common_chat(query=rendered_prompt)
        return response_message
    

    def receive_task(self, task):
        """
        接收原始任务。
        """
        self.original_task = task
        
    def extract_and_validate_yaml(self, model_response):
        # 正则表达式匹配包裹在```yaml```之间的内容
        import re
        match = re.search(r'```yaml\n([\s\S]*?)\n```', model_response, re.DOTALL)
        
        if not match:
            return None  # 如果没有找到匹配的内容，返回None
        
        model_response = match.group(1).strip()
        
        try:
            # 尝试解析YAML内容
            parsed_yaml = yaml.safe_load(model_response)
            return yaml.dump(parsed_yaml, default_flow_style=False)

        except yaml.YAMLError as exc:
            print(f"Invalid YAML content: {exc}")
            return None