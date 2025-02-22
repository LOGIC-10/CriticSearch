import json
import re
import time
from concurrent.futures import ThreadPoolExecutor

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
    return (
        response.get("results", [])[0].get("raw_content", "")
        if response.get("results")
        else ""
    )


def read_json_file(
    file_path="/Users/logic/Documents/CodeSpace/CriticSearch/Deep Research detection_0214.json",
):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
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
    pattern_browse = re.compile(r"\nRead(?: more from)?\s*(https?://[^\s\[\]()]+)")

    actions = []
    thinking = text

    # 查找所有search匹配
    for match in pattern_search.finditer(text):
        actions.append({"type": "search", "content": match.group(1).strip()})
        thinking = text[: match.start()].strip()

    # 查找所有browse匹配
    for match in pattern_browse.finditer(text):
        url = match.group(1).strip()
        if "[" not in url and "]" not in url and "(" not in url and ")" not in url:
            actions.append({"type": "browse", "content": url})
            thinking = text[: match.start()].strip()

    return {"thinking": thinking.strip(), "action": actions if actions else None}


def process_single_activity(activity):
    """Helper function to process a single activity"""
    processed = process_activity(activity)
    if processed.get("action"):
        for action in processed["action"]:
            if action["type"] == "search":
                action["result"] = tavily_search(action["content"])
            elif action["type"] == "browse":
                action["result"] = tavily_extract(action["content"])
    return processed


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

            # 使用线程池并行处理activities
            with ThreadPoolExecutor(max_workers=20) as executor:
                processed_activities = list(
                    executor.map(process_single_activity, item["Activity"])
                )

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
for item_list in data[:1]:
    processed_item = process_activities(item_list)
    processed_data.append(processed_item)

# 保存处理后的JSON
input_path = (
    "/Users/logic/Documents/CodeSpace/CriticSearch/Deep Research detection_0214.json"
)
base_name = input_path.rsplit(".", 1)[0]
output_path = f"{base_name}_Processed_all.json"

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(processed_data, f, indent=4, ensure_ascii=False)

print(f"Processed data saved to: {output_path}")
