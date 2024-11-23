import json
import yaml
from agent_factory.config import read_config
import os

from jinja2 import Environment, FileSystemLoader
from agent_factory.utils import call_llm
from agent_factory.search_adapter.aggregator import SearchAggregator
import concurrent.futures



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
        self.history = []

    def search_query(self, query):
        # 初始化 SearchAggregator
        aggregator = SearchAggregator()
        # 调用搜索方法
        response = aggregator.search(query=query)
        # 提取结果中的标题、URL 和内容
        results = [
            {
                "title": res.get('title'),
                "url": res.get('url'),
                "content": res.get('content')
            }
            for res in response.get("results")
        ]
        # 返回查询、响应时间和结果
        return {
            "query": response.get('query'),
            "response_time": response.get('response_time'),
            "results": results # 有用的其实是results[List]中的title, url, content
        }


    def parallel_search(self,queries):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_query = {executor.submit(self.search_query, query): query for query in queries}
            results = []
            for future in concurrent.futures.as_completed(future_to_query):
                query = future_to_query[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as exc:
                    print(f"{query} generated an exception: {exc}")
                    
        return results


    def format_parallel_search_to_string(self, data_list):
        result = []
        for item in data_list:
            query = item.get("query")
            results = item.get("results", [])
            result.append(f"Query: {query}\nSearch Results:\n" + "-"*50)
            for i, res in enumerate(results, 1):
                result.append(f"[{i}]:\nTITLE: {res['title']}\nURL: {res['url']}\nCONTENT: {res['content']}\n" + "-"*50)
            result.append("\n")
        return "\n".join(result)

    def common_chat(self, query):
        llm_response = call_llm(model=self.model, sys_prompt=self.sys_prompt, usr_prompt=query, config=self.config)
        self.history.append({"role": "user", "content": query})
        self.history.append({"role": "assistant", "content": llm_response})
        return llm_response
    
    def clear_history(self):
        self.history = []

    def update_answer(self, query, previous_answer, search_results, critic_feedback):

        data = {
            "query": query,
            "previous_answer": previous_answer,
            "search_results": search_results,
            "critic_feedback": critic_feedback
        }
        updated_answer = self.chat_with_template(data, self.env.get_template('agent_update_answer.txt'))
        return updated_answer
    
    def model_confident(self, query):
        """
        检查模型是否对当前问题有信心。
        """
        data = {
            "user_question": query
        }
        model_response = self.chat_with_template(data, self.env.get_template('agent_confidence.txt'))
        return model_response
    
    def initialize_search(self, query):
        """
        初始化搜索。
        """
        data = {
            "user_question": query
        }
        model_response = self.chat_with_template(data, self.env.get_template('planner_agent_initial_search_plan.txt'))
        return model_response   
    
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
        
    