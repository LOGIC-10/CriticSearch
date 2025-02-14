import json
import re

from tavily import TavilyClient


def tavily_search(query, api_key="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"):
    """
    Perform a Tavily search query
    # Example usage: results = tavily_search("Who is Leo Messi?")
    """
    tavily_client = TavilyClient(api_key=api_key)
    response = tavily_client.search(query, include_raw_content=True)
    return response.get("results", [])

def tavily_extract(url, api_key="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"):
    """
    Extract content from a URL using Tavily
    # Example usage: content = tavily_extract("https://en.wikipedia.org/wiki/Artificial_intelligence")
    """
    tavily_client = TavilyClient(api_key=api_key)
    response = tavily_client.extract(url)
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



# 处理Activity列表
def process_activities(activities):
    if not isinstance(activities, list):
        return activities
    
    result = []
    for item in activities:
        # 如果是Activity键的字典项
        if isinstance(item, dict) and "Activity" in item:
            # 处理Activity列表中的每一项
            processed = [process_activity(activity) for activity in item["Activity"]]
            item["Activity"] = processed
        result.append(item)
    return result

data = read_json_file()
if data is None:
    exit()

# 选取包含Activity列表部分并处理
activity_list = data[1]
processed_activities = process_activities(activity_list)

print(json.dumps(processed_activities, indent=4, ensure_ascii=False))




