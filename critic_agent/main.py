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

max_iteration = 10  # 最大迭代次数

for iteration in range(max_iteration):
    print(f"\n{'=' * 20}\nIteration {iteration + 1}\n{'=' * 20}\n")
    
    if iteration == 0: # 第一次回答
        common_agent_answer = common_agent.common_chat(query=task) # common_chat里面可以用tool search
    else:
        # 根据上一次的搜索结果，上一次的回答，以及上一次的critic反馈，更新回答
        common_agent_answer = common_agent.update_answer(query=task, previous_answer=common_agent_answer, search_results=formatted_search_results, critic_feedback=critic_agent_response)
    
    print(f"{'%' * 30}\nCOMMON_AGENT_ANSWER:\n\n{common_agent_answer}\n\n")
    
    critic_agent = CriticAgent()
    critic_agent.receive_task(task)
    critic_agent.receive_agent_answer(common_agent_answer)
    
    critic_agent_response = critic_agent.critic()
    print(f"{'%' * 30}\nCRITIC_AGENT_RESPONSE:\n\n{critic_agent_response}\n\n")
    
    plan_agent.receive_task(task)
    agent_next_search_plan = plan_agent.plan(common_agent_answer, critic_agent_response)
    
    new_query_list = [item["Query"] for item in yaml.safe_load(agent_next_search_plan).get('NewSearchQueries', [])]
    
    common_agent.queryDB.update(new_query_list)
    search_results = common_agent.parallel_search(new_query_list)
    formatted_search_results = common_agent.format_parallel_search_to_string(search_results)
    print(f"{'%' * 30}\nSEARCH_RESULTS:\n\n{formatted_search_results}\n\n")


