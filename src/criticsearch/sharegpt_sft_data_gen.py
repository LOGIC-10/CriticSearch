import json
import os
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, List
from jinja2 import Template
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from criticsearch.base_agent import BaseAgent
from criticsearch.tools.note_manager import set_session  # Only import session management
from criticsearch.utils import extract_tag_content
from criticsearch.reportbench.instruction_generator import InstructionGenerator
# from criticsearch.reportbench.verifier import ReportVerifier

class DeepResearchEnvChat:
    def __init__(self):
        self.cfg = type('Config', (), {
            'max_steps': 100,
            'max_tokens': 16384,
            'invalid_penalty': -1.0,
            'format_penalty': -1.0
        })()
        self.episode_id = str(uuid.uuid4())
        self._step_count = 0
        self.history = []
        self.current_observation_for_action = None
        self.render_cache = None

        # 配置日志记录器
        # 使用项目根目录下的 logs 文件夹存储日志
        self.save_path = Path(__file__).resolve().parent.parent.parent / "logs"
        self.save_path.mkdir(parents=True, exist_ok=True)
        
        logger_name = f"{__name__}.{self.__class__.__name__}.{str(uuid.uuid4())[:8]}"
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            log_file_path = self.save_path / "env_chat.log"
            file_handler = logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            self.logger.propagate = False

        self.agent = BaseAgent()  # BaseAgent will auto-discover tools by default
        self.instruction_generator = InstructionGenerator()
        self.section_level_samples = self.instruction_generator.get_all_section_level_instructions()
        self.current_facts = None

    def _log_info(self, message: str):
        self.logger.info(f"[Epi: {self.episode_id} | Step: {self._step_count}] {message}")

    def _log_warning(self, message: str):
        self.logger.warning(f"[Epi: {self.episode_id} | Step: {self._step_count}] {message}")

    def _log_error(self, message: str):
        self.logger.error(f"[Epi: {self.episode_id} | Step: {self._step_count}] {message}")

    def reset(self) -> str:
        """重置环境，返回初始观察"""
        self._step_count = 0
        self.history = []

        set_session(str(uuid.uuid4()))
        sample = self.instruction_generator.get_all_section_level_instructions()[0]  # 使用第一个样本
        user_prompt = "User Query: " + sample["section_full_prompt"]
        self.current_facts = sample["extracted_facts"]

        # 获取所有自动发现的工具schemas
        schemas = self.agent.get_all_tool_schemas()

        # 构建系统提示
        tpl = Path(self.agent.prompts_dir) / "tool_use_short.txt"
        system_prompt_content = Template(tpl.read_text(encoding="utf-8")).render(
            AVAILABLE_TOOLS=json.dumps(schemas, ensure_ascii=False),
        )

        self.history.append({"role": "system", "content": system_prompt_content})
        self.history.append({"role": "user", "content": user_prompt})
        
        full_prompt = f"{system_prompt_content}\n\n{user_prompt}"
        self.current_observation_for_action = full_prompt
        self.render_cache = full_prompt

        self._log_info(f"--- Environment Reset ---")
        self._log_info(f"System Prompt: {system_prompt_content}")
        self._log_info(f"User Prompt: {user_prompt}")

        return full_prompt

    def step(self, action: str) -> Tuple[str, float, bool, Dict]:
        """执行一步交互"""
        self._step_count += 1
        remarks = ""

        self._log_info(f"--- Model Action (a_{self._step_count-1}) ---")
        self._log_info(action)

        self.history.append({"role": "assistant", "content": action})

        obs = ""
        reward = 0.0
        done = False
        info = {}

        if self._step_count > self.cfg.max_steps:
            msg = "<error>max_steps_exceeded</error>"
            remarks = "Max steps exceeded"
            self.render_cache = msg
            self.history.append({"role": "user", "content": msg})
            self._log_warning(f"Max steps exceeded. Action: {action}, Msg: {msg}")
            obs, reward, done, info = msg, self.cfg.invalid_penalty, True, {}
        else:
            tool_xml = extract_tag_content(action, "tool_use")
            if not tool_xml:
                answer_content = extract_tag_content(action, "answer")
                if not answer_content:
                    msg = "<error>format_error_no_tool_or_answer</error>"
                    remarks = "Format error: No tool use or answer tag detected"
                    self.history.append({"role": "user", "content": msg})
                    self._log_warning(f"No tool use or answer tag detected. Action: {action}")
                    obs, reward, done, info = msg, self.cfg.format_penalty, False, {}
                else:
                    remarks = "Final answer provided by model"
                    # verifier = ReportVerifier(self.agent)
                    # acc = verifier.verify_section(action, self.current_facts)
                    acc = 1.0
                    self.render_cache = action
                    self._log_info(f"--- Model Section Answer ---")
                    self._log_info(action)
                    self._log_info(f"--- Accuracy ---")
                    self._log_info(str(acc))
                    obs, reward, done, info = action, acc, True, {}
            else:
                self._log_info(f"--- Detected Model Tool Use ---")
                self._log_info(tool_xml)
                tool_name = extract_tag_content(tool_xml, "name")
                arg_str = extract_tag_content(tool_xml, "arguments") or "{}"
                remarks = f"Tool call attempt: {tool_name}"
                try:
                    args = json.loads(arg_str)
                except json.JSONDecodeError:
                    error_xml = (
                        f"<tool_use_result><name>{tool_name}</name>"
                        f"<error>arguments_not_json</error></tool_use_result>"
                    )
                    remarks = f"Tool call error: arguments_not_json for {tool_name}"
                    self.render_cache = error_xml
                    self.history.append({"role": "user", "content": error_xml})
                    self._log_error(f"Failed to parse tool arguments: {arg_str}. Error XML: {error_xml}")
                    obs, reward, done, info = error_xml, self.cfg.invalid_penalty, False, {}
                else:
                    try:
                        result = self.agent.tool_registry.invoke_tool(tool_name, args)
                        result_xml = (
                            f"<tool_use_result><name>{tool_name}</name>"
                            f"<result>{json.dumps(result, ensure_ascii=False)}</result>"
                            f"</tool_use_result>"
                        )
                        print("tool_xml:\n", result_xml)
                        # print("end of tool xml")

                        remarks = f"Tool call success: {tool_name}"
                        self.render_cache = result_xml
                        self._log_info(f"--- Tool Use Result ---")
                        self._log_info(result_xml)
                        self.history.append({"role": "user", "content": result_xml})
                        obs, reward, done, info = result, 1.0, False, {}
                    except Exception as exc:
                        error_xml = (
                            f"<tool_use_result><name>{tool_name}</name>"
                            f"<error>{str(exc)}</error></tool_use_result>"
                        )
                        remarks = f"Tool call exception: {tool_name} - {str(exc)}"
                        self.history.append({"role": "user", "content": error_xml})
                        self._log_error(f"Error invoking tool {tool_name} with args {args}. Exception: {exc}. Error XML: {error_xml}")
                        self.render_cache = error_xml
                        obs, reward, done, info = error_xml, self.cfg.invalid_penalty, False, {}

        obs_str = json.dumps(obs, ensure_ascii=False) if isinstance(obs, (dict, list)) else str(obs)
        final_obs_str = obs_str[: self.cfg.max_tokens]

        self._log_info(f"--- Environment Feedback ---")
        self._log_info(f"Reward (r_{self._step_count}): {reward}")
        self._log_info(f"Done: {done}")
        self._log_info(f"Next Observation (s_{self._step_count}) before truncation: {obs_str}")
        if len(obs_str) > self.cfg.max_tokens:
            self._log_info(f"Next Observation (s_{self._step_count}) (truncated): {final_obs_str}")

        current_traj_entry = {
            "episode_id": self.episode_id,
            "step": self._step_count,
            "observation_for_action": self.current_observation_for_action,
            "action_taken": action,
            "reward_received": reward,
            "next_observation": final_obs_str,
            "done": done,
            "remarks": remarks
        }

        with open(self.save_path / "trajectory_chat.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(current_traj_entry, ensure_ascii=False) + "\n")

        self.current_observation_for_action = final_obs_str
        
        return final_obs_str, reward, done, info

    def convert_history_to_sharegpt_format(self) -> List[dict]:
        """
        将self.history转换为ShareGPT格式，每组对话带上reset时生成的system prompt。
        """
        sharegpt_conversations = []
        current_conversation = []
        system_prompt = None
        
        # 首先找到system prompt
        for item in self.history:
            if item.get("role") == "system":
                system_prompt = item.get("content", "")
                break
        
        # 然后处理对话内容
        for item in self.history:
            if item.get("role") == "system":
                continue
                
            if item.get("role") == "user":
                current_conversation.append({
                    "from": "human",
                    "value": str(item.get("content", "")).strip()
                })
            elif item.get("role") == "assistant":
                current_conversation.append({
                    "from": "gpt",
                    "value": str(item.get("content", "")).strip()
                })
        
        # 如果收集到了对话内容，添加到结果中
        if current_conversation:
            sharegpt_conversations.append({
                "conversations": current_conversation,
                "system": system_prompt or ""
            })
            
        return sharegpt_conversations

def process_single_section(section_sample: dict) -> List[dict]:
    """
    处理单个section样本并返回ShareGPT格式的数据
    """
    try:
        env = DeepResearchEnvChat()
        # 构建user query
        user_prompt = "User Query: " + section_sample["section_full_prompt"]
        
        # 获取所有自动发现的工具schemas
        schemas = env.agent.get_all_tool_schemas()

        # 构建系统提示
        tpl = Path(env.agent.prompts_dir) / "tool_use_short.txt"
        system_prompt_content = Template(tpl.read_text(encoding="utf-8")).render(
            AVAILABLE_TOOLS=json.dumps(schemas, ensure_ascii=False),
        )

        # 构建对话历史
        env.history = [
            {"role": "system", "content": system_prompt_content},
            {"role": "user", "content": user_prompt}
        ]
        
        # 执行对话过程
        done = False
        while not done:
            # 使用模型生成动作
            action = env.agent.chat(
                usr_prompt=user_prompt,
                tools=str(schemas),
                save_history=False,
                model="gpt-4o",
                messages=env.history
            )
            
            if hasattr(action, 'content'):
                action = action.content
                
            # 执行动作
            obs, reward, done, info = env.step(action)
        
        return env.convert_history_to_sharegpt_format()
    except Exception as e:
        print(f"处理section时出错: {str(e)}")
        return []

def main(num_sections: int = None):
    """
    处理section样本并生成ShareGPT格式的对话数据
    Args:
        num_sections: 要处理的section数量，如果为None则处理所有section
    """
    # 初始化环境获取所有section样本
    env = DeepResearchEnvChat()
    section_samples = env.section_level_samples
    
    if not section_samples:
        print("未找到section样本")
        return
    
    # 如果指定了数量，则只处理指定数量的section
    if num_sections is not None:
        section_samples = section_samples[:num_sections]
    
    print(f"开始处理 {len(section_samples)} 个section")
    
    # 使用ThreadPoolExecutor进行并行处理
    all_conversations = []
    with ThreadPoolExecutor(max_workers=25) as executor:
        # 提交所有任务
        future_to_section = {
            executor.submit(process_single_section, sample): i 
            for i, sample in enumerate(section_samples)
        }
        
        # 使用tqdm显示进度
        with tqdm(total=len(section_samples), desc="处理section对话") as pbar:
            for future in as_completed(future_to_section):
                section_idx = future_to_section[future]
                try:
                    result = future.result()
                    all_conversations.extend(result)
                except Exception as e:
                    print(f"处理section {section_idx} 时发生错误: {str(e)}")
                pbar.update(1)
    
    # 确保输出目录存在
    output_dir = Path("conversation_histories")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存合并后的结果
    output_file = output_dir / "all_sections_sharegpt.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_conversations, f, ensure_ascii=False, indent=2)
    
    print(f"\n处理完成！共处理 {len(section_samples)} 个section")
    print(f"合并后的对话数量: {len(all_conversations)}")
    print(f"结果已保存到: {output_file}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='处理section样本并生成ShareGPT格式的对话数据')
    parser.add_argument('--num_sections', type=int, default=None, 
                      help='要处理的section数量，如果不指定则处理所有section')
    args = parser.parse_args()
    main(args.num_sections)


# 运行命令示例

# python src/criticsearch/sharegpt_sft_data_gen.py --num_sections 2