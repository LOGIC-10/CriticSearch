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

task = """why do we say google is facing chaleenges in 2019?"""

common_agent = BaseAgent()
common_agent_answer = common_agent.common_chat(query=task)
print(f"common_agent_answer:\n\n{common_agent_answer}\n\n")
CriticAgent = CriticAgent()
CriticAgent.receive_task(task)
CriticAgent.receive_agent_answer(common_agent_answer)

response_message = CriticAgent.critic()

# 接下来要对response_message中的yaml内容进行解析