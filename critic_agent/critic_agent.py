import json
import re
import sys
import os

import sys
from pathlib import Path

import yaml

project_root = Path(__file__).resolve().parents[1]  # 获取项目根目录
sys.path.append(str(project_root / 'agent_factory'))  # 添加到搜索路径中
sys.path.append(str(project_root / 'critic_agent'))

from agent_factory.agent import BaseAgent


class CriticAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.original_task = ''
        self.critic_prompt = self.env.get_template('critic_agent.txt')

    def critic(self):
        """
        生成评论。
        """
        data = self.get_data_for_critic()
        model_response = self.chat_with_template(data, self.critic_prompt)
        # 这里模型在模拟user作出回应
        self.history.append({"role": "critic_user", "content": model_response})
        try:
            formatted_yaml = self.extract_and_validate_yaml(model_response)
            return formatted_yaml
        
        except yaml.YAMLError as exc:
            print(f"Invalid YAML content: {exc}")
            return None
    
    def receive_agent_answer(self, agent_answer):
        self.agent_answer = agent_answer

    def get_data_for_critic(self):
        return {
            'user_question': self.original_task,
            'agent_answer': self.agent_answer
        }


