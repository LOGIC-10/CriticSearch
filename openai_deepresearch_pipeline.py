import json
import re

def read_json_file(file_path="/Users/logic/Documents/CodeSpace/CriticSearch/Deep Research detection_0214.json"):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {file_path}")
        return None
    except Exception as e:
        print(f"Error reading file: {str(e)}")
        return None

# 定义处理单个activity文本的函数
def process_activity(text):
    # 定义正则：匹配换行后跟"Searched for"和"Read"或"Read more from"
    pattern_search = re.compile(r"\nSearched for\s*(.+)")
    pattern_browse = re.compile(r"\nRead(?: more from)?\s*(.+)")
    
    match = pattern_search.search(text)
    if match:
        thinking = text[:match.start()].strip()
        return {"thinking": thinking, "action": {"type": "search", "content": match.group(1).strip()}}
    match = pattern_browse.search(text)
    if match:
        thinking = text[:match.start()].strip()
        return {"thinking": thinking, "action": {"type": "browse", "content": match.group(1).strip()}}
    # 未匹配到, 即全部为thinking
    return {"thinking": text.strip(), "action": None}

# 递归处理结构（支持列表及字典），不包含默认行为逻辑
def process_item(item):
    if isinstance(item, list):
        return [process_item(sub) for sub in item]
    elif isinstance(item, dict):
        if "Query" in item:
            processed = process_activity(item["Query"])
            return {**item, **processed}
        else:
            return {k: process_item(v) for k, v in item.items()}
    elif isinstance(item, str):
        return process_activity(item)
    else:
        return item

# 针对Activity列表设置默认第一个包含Query的action为search
def set_default_search(activities):
    for elem in activities:
        if isinstance(elem, dict) and "Query" in elem:
            action = elem.get("action")
            if action is None:
                action = {}
            action["type"] = "search"
            elem["action"] = action
            break
    return activities

data = read_json_file()
if data is None:
    exit()

# 选取包含Activity列表部分（其它部分保持不变）
activity_list = data[1]
processed_activities = process_item(activity_list)
processed_activities = set_default_search(processed_activities)

print(json.dumps(processed_activities, indent=4, ensure_ascii=False))