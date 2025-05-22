import json
import os
import uuid
import argparse

# 工具名映射
TOOL_MAP = {
    "SEARCH": "search",
    "TAKING_NOTES": "taking_notes",
    "BROWSE": "browse"
}
TOOL_USE_SET = set(TOOL_MAP.keys())
WRITE_ACTION_SET = {"START_WRITING"}

def get_tool_name(action):
    if not action:
        return ""
    return TOOL_MAP.get(str(action).strip().upper(), str(action).strip().lower())

def gen_fake_taking_notes_result(count):
    note_ids = [str(uuid.uuid4()) for _ in range(count)]
    result = {
        "status": "ok",
        "note_ids": note_ids
    }
    xml = f"<tool_use_result><name>taking_notes</name><result>{json.dumps(result, ensure_ascii=False)}</result></tool_use_result>"
    return xml

def is_human_or_observation(entry):
    return entry["from"] == "human" or entry["from"] == "observation"

def is_gpt_or_function_call(entry):
    return entry["from"] == "gpt" or entry["from"] == "function_call"

def fix_conversation(conv):
    fixed = []
    idx = 0
    for entry in conv:
        if idx % 2 == 0:  # 奇数位，应该是human/observation
            if is_human_or_observation(entry):
                fixed.append(entry)
            else:
                # 插入空白human
                fixed.append({"from": "human", "value": ""})
                fixed.append(entry)
                idx += 1
        else:  # 偶数位，应该是gpt/function_call
            if is_gpt_or_function_call(entry):
                fixed.append(entry)
            else:
                # 插入空白gpt
                fixed.append({"from": "gpt", "value": ""})
                fixed.append(entry)
                idx += 1
        idx += 1
    # 如果最后一条是gpt/function_call，补一个空human
    if len(fixed) % 2 != 0 and is_gpt_or_function_call(fixed[-1]):
        fixed.append({"from": "human", "value": ""})
    return fixed

def is_valid_conversation(conv):
    # 至少有一对human-gpt交替
    if len(conv) < 2:
        return False
    for i in range(0, len(conv)-1, 2):
        if is_human_or_observation(conv[i]) and is_gpt_or_function_call(conv[i+1]):
            return True
    return False

def convert_to_sharegpt(input_file_path):
    """
    将对话历史转换为ShareGPT格式
    
    Args:
        input_file_path (str): 输入JSON文件路径
        
    Returns:
        list: 转换后的对话列表，每个元素是一个包含conversations键的字典
    """
    with open(input_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    conversations = []
    current_dialog = []
    last_tool_name = None
    first_human = True

    for item in data:
        # 处理 from: human 的 value（原始用户输入）
        if item.get("from") == "human" and item.get("value"):
            if first_human:
                # 第一个用户输入直接保留原始内容
                current_dialog.append({"from": "human", "value": str(item['value']).strip()})
                first_human = False
            else:
                xml = f"<tool_use_result>\n  <name>user</name>\n  <result>{str(item['value']).strip()}</result>\n</tool_use_result>"
                current_dialog.append({"from": "human", "value": xml})
            last_tool_name = None
        # 处理 action_content
        if "action" in item and "action_content" in item and item["action_content"]:
            action_upper = str(item["action"]).strip().upper()
            arguments = str(item["action_content"])
            # 工具调用
            if action_upper in TOOL_USE_SET:
                tool_name = get_tool_name(action_upper)
                xml = f"<tool_use>\n  <name>{tool_name}</name>\n  <arguments>{arguments.strip()}</arguments>\n</tool_use>"
                if "thought" in item and item["thought"]:
                    value = str(item["thought"]).strip() + "\n" + xml
                else:
                    value = xml
                current_dialog.append({"from": "gpt", "value": value})
                # 如果是taking_notes，插入一个假的human结果，note_ids数量与action_content长度一致
                if tool_name == "taking_notes":
                    try:
                        ac = item["action_content"]
                        count = len(ac) if isinstance(ac, list) else 1
                    except Exception:
                        count = 1
                    fake_result = gen_fake_taking_notes_result(count)
                    current_dialog.append({"from": "human", "value": fake_result})
                last_tool_name = tool_name
            # 写作型
            elif action_upper in WRITE_ACTION_SET:
                answer = f"<answer>{arguments.strip()}</answer>"
                if "thought" in item and item["thought"]:
                    value = str(item["thought"]).strip() + "\n" + answer
                else:
                    value = answer
                current_dialog.append({"from": "gpt", "value": value})
                last_tool_name = None
            # 其它action跳过
            else:
                continue
        # 处理 action_result
        if "action_result" in item and item["action_result"]:
            name = last_tool_name if last_tool_name else "user"
            xml = f"<tool_use_result>\n  <name>{name}</name>\n  <result>{str(item['action_result']).strip()}</result>\n</tool_use_result>"
            current_dialog.append({"from": "human", "value": xml})
            last_tool_name = None
        # 处理原始gpt自然语言回答（非工具调用）
        if item.get("from") == "gpt" and not item.get("action_content") and item.get("value"):
            answer = f"<answer>{str(item['value']).strip()}</answer>"
            current_dialog.append({"from": "gpt", "value": answer})

    if current_dialog:
        # 修正交替格式
        fixed_dialog = fix_conversation(current_dialog)
        if is_valid_conversation(fixed_dialog):
            conversations.append({"conversations": fixed_dialog})
            
    return conversations

def split_conversations_by_answer(conversations):
    """
    根据<answer>标签将对话列表分割成多个子对话列表
    
    Args:
        conversations (list): 原始的对话列表，每个元素是一个包含conversations键的字典
        
    Returns:
        list: 分割后的多个对话列表，每个列表包含到<answer>标签为止的对话内容，格式为：
        [
            {
                "conversations": [...],
            },
            ...
        ]
    """
    if not conversations:
        return []
        
    result_conversations = []
    
    for conv_dict in conversations:
        conv_list = conv_dict.get("conversations", [])
        temp_list = []
        
        for item in conv_list:
            temp_list.append(item)
            # 检查当前项是否包含<answer>标签
            if item.get("from") == "gpt" and "<answer>" in item.get("value", ""):
                # 找到<answer>标签，将当前累积的对话添加到结果中
                if temp_list:
                    result_conversations.append({
                        "conversations": temp_list,
                    })
                    temp_list = []
        
        # 如果还有剩余的对话项，也添加到结果中
        if temp_list:
            result_conversations.append({
                "conversations": temp_list,
            })
    
    return result_conversations

def process_all_json_files(input_dir="conversation_histories"):
    """
    处理指定目录下所有的JSON文件，并将结果合并
    
    Args:
        input_dir (str): 输入目录路径
        
    Returns:
        list: 所有文件处理结果的合并列表
    """
    all_conversations = []
    
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 如果当前目录就是conversation_histories，直接使用当前目录
    if os.path.basename(script_dir) == "conversation_histories":
        full_input_dir = script_dir
    else:
        full_input_dir = os.path.join(script_dir, input_dir)
    
    print(f"处理目录：{full_input_dir}")
    
    # 遍历目录下的所有文件
    for filename in os.listdir(full_input_dir):
        if filename.endswith('.json'):
            input_path = os.path.join(full_input_dir, filename)
            try:
                # 处理单个文件
                conversations = convert_to_sharegpt(input_path)
                # 分割对话
                split_conversations = split_conversations_by_answer(conversations)
                # 将结果添加到总列表中
                all_conversations.extend(split_conversations)
                print(f"成功处理文件：{filename}")
            except Exception as e:
                print(f"处理文件 {filename} 时出错：{str(e)}")
                continue
    
    return all_conversations

def main():
    parser = argparse.ArgumentParser(description="Convert conversation history to ShareGPT format.")
    parser.add_argument('-i', '--input', type=str, default="2024_Botswana_general_election_20250503_051147_conversation.json", help="Input JSON file path")
    parser.add_argument('-o', '--output', type=str, default="output_sharegpt.json", help="Output JSON file path")
    parser.add_argument('--process-all', action='store_true', help="处理conversation_histories目录下的所有JSON文件")
    args = parser.parse_args()

    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))

    if args.process_all:
        # 处理所有文件
        all_conversations = process_all_json_files()
        output_path = os.path.join(script_dir, args.output)
    else:
        # 处理单个文件
        input_path = os.path.join(script_dir, args.input)
        conversations = convert_to_sharegpt(input_path)
        all_conversations = split_conversations_by_answer(conversations)
        output_path = os.path.join(script_dir, args.output)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_conversations, f, ensure_ascii=False, indent=2)

    print(f"转换完成，输出文件：{output_path}")

if __name__ == "__main__":
    main()

'''
用法示例：

# 处理单个文件
python conversation_histories/convert_to_sharegpt.py -i input.json -o output.json

# 处理conversation_histories目录下的所有JSON文件
python conversation_histories/convert_to_sharegpt.py --process-all -o output.json

参数说明：
  -i/--input     指定输入的原始对话json文件路径（可选，默认见脚本）
  -o/--output    指定输出的ShareGPT格式json文件路径（可选，默认output_sharegpt.json）
  --process-all  处理conversation_histories目录下的所有JSON文件
'''