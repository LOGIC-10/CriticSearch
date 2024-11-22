import json
import re
import sys
import os

import sys
from pathlib import Path

import yaml

project_root = Path(__file__).resolve().parents[1]  # 获取项目根目录
# print(f"Project root: {project_root}")
sys.path.append(str(project_root))  # 添加项目根目录到搜索路径中
# print(f"sys.path: {sys.path}")

from agent_factory.agent import BaseAgent
from critic_agent import CriticAgent
from planner_agent import SearchPlanAgent

task = """why do we say google is facing chaleenges in 2019?"""

common_agent = BaseAgent()
plan_agent = SearchPlanAgent()
# 假设一个search result

common_agent_answer = common_agent.common_chat(query=task)
print(f"\n\n{'%' * 30}\nCOMMON_AGENT_ANSWER:\n\n{common_agent_answer}\n\n")
CriticAgent = CriticAgent()
CriticAgent.receive_task(task)
CriticAgent.receive_agent_answer(common_agent_answer)

critic_agent_response = CriticAgent.critic()
print(f"{'%' * 30}\nCRITIC_AGENT_RESPONSE:\n\n{critic_agent_response}\n\n")
# 从critic_agent_response中解析出好的方面,为后面的citationDB做准备。但是现在先暂时跳过

plan_agent.receive_task(task)
agent_next_search_plan = plan_agent.plan(common_agent_answer, critic_agent_response)
# print(f"agent_next_search_plan:\n\n{agent_next_search_plan}\n\n")

new_query_list = [item["Query"] for item in yaml.safe_load(agent_next_search_plan).get('NewSearchQueries')]
print(f"{'%' * 30}\nSEARCH_PLAN_LIST:\n\n{new_query_list}\n\n")
# 把新的搜索问题加入到queryDB中
common_agent.queryDB.update(new_query_list)

common_agent.parallel_search(new_query_list)




# 接下来要对response_message中的yaml内容进行解析