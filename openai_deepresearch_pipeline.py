import json
import re
import time  # 添加time模块导入
from tavily import TavilyClient


def tavily_search(query, api_key="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"):
    """
    Perform a Tavily search query
    # Example usage: results = tavily_search("Who is Leo Messi?")
    """
    print(f"Searching: {query}")
    tavily_client = TavilyClient(api_key=api_key)
    response = tavily_client.search(query, include_raw_content=True)
    time.sleep(0.1)  # 添加0.5秒延时
    return response.get("results", [])

def tavily_extract(url, api_key="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"):
    """
    Extract content from a URL using Tavily
    # Example usage: content = tavily_extract("https://en.wikipedia.org/wiki/Artificial_intelligence")
    """
    print(f"Extracting: {url}")
    tavily_client = TavilyClient(api_key=api_key)
    response = tavily_client.extract(url)
    time.sleep(0.1)  # 添加延时
    return response.get("results", [])[0].get("raw_content", "") if response.get("results") else ""


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
    # 修改read模式，只匹配以http或https开头的URL
    pattern_browse = re.compile(r"\nRead(?: more from)?\s*(https?://[^\s\[\]()]+)")
    
    match = pattern_search.search(text)
    if match:
        thinking = text[:match.start()].strip()
        return {"thinking": thinking, "action": {"type": "search", "content": match.group(1).strip()}}
    
    match = pattern_browse.search(text)
    if match:
        url = match.group(1).strip()
        # 确保URL不包含Markdown语法
        if '[' not in url and ']' not in url and '(' not in url and ')' not in url:
            thinking = text[:match.start()].strip()
            return {"thinking": thinking, "action": {"type": "browse", "content": url}}
    
    # 未匹配到或URL格式不符合要求, 全部内容作为thinking
    return {"thinking": text.strip(), "action": None}



# 处理Activity列表
def process_activities(activities):
    if not isinstance(activities, list):
        return activities
    
    final_result = []
    deep_research = None
    
    for item in activities:
        # 如果是Deep Research项,先保存起来
        if isinstance(item, dict) and "Deep Research" in item:
            deep_research = item
            continue
            
        # 处理其他项(包括Activity)
        if isinstance(item, dict) and "Activity" in item:
            processed_activities = []
            
            # 处理第一个activity
            if item["Activity"]:
                first_activity = process_activity(item["Activity"][0])
                # 确保第一项为search类型并执行搜索
                if first_activity.get("action") is None:
                    first_activity["action"] = {
                        "type": "search",
                        "content": first_activity["thinking"]
                    }
                first_activity["action"]["result"] = tavily_search(first_activity["action"]["content"])
                processed_activities.append(first_activity)
            
                # 处理剩余的activities
                for activity in item["Activity"][1:]:
                    processed = process_activity(activity)
                    if processed.get("action") and processed["action"].get("type"):
                        action = processed["action"]
                        if action["type"] == "search":
                            action["result"] = tavily_search(action["content"])
                        elif action["type"] == "browse":
                            action["result"] = tavily_extract(action["content"])
                    processed_activities.append(processed)
                    
            item["Activity"] = processed_activities
        final_result.append(item)
    
    # 最后添加Deep Research
    if deep_research:
        final_result.append(deep_research)
    
    return final_result

data = read_json_file()
if data is None:
    exit()

# 处理data中的所有元素
processed_data = []
for item_list in data:
    processed_item = process_activities(item_list)
    processed_data.append(processed_item)

# 保存处理后的JSON
input_path = "/Users/logic/Documents/CodeSpace/CriticSearch/Deep Research detection_0214.json"
base_name = input_path.rsplit('.', 1)[0]
output_path = f"{base_name}_Processed_all.json"

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(processed_data, f, indent=4, ensure_ascii=False)

print(f"Processed data saved to: {output_path}")




