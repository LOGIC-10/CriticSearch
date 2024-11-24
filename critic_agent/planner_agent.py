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


class SearchPlanAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.original_task = ''
        self.reflection_and_plan_prompt = self.env.get_template('planner_agent_with_reflection.txt')

    def plan(self, common_agent_answer, critic_feedback):
        """
        生成计划。
        """
        data = self.get_data_for_plan(common_agent_answer, critic_feedback)
        model_response = self.chat_with_template(data, self.reflection_and_plan_prompt)
        self.history.append({"role": "planner", "content": model_response})

        try:
            formatted_yaml = self.extract_and_validate_yaml(model_response)
            return formatted_yaml

        except yaml.YAMLError as exc:
            print(f"Invalid YAML content: {exc}")
            return None
        
    def get_data_for_plan(self, common_agent_answer, critic_feedback):
        return {
            'user_question': self.original_task,
            'agent_answer': common_agent_answer,
            'user_feedback': critic_feedback,
            'search_history': self.queryDB
        }