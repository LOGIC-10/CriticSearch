
import json

def traverse(data, level=0):
    indent = "    " * level
    if isinstance(data, dict):
        if "title" in data:
            print(indent + data["title"])
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                traverse(value, level + 1)
    elif isinstance(data, list):
        for item in data:
            traverse(item, level)

if __name__ == "__main__":
    # 读取 JSON 文件
    with open('wikitext.json', 'r', encoding='utf-8') as f:
        content = json.load(f)
    # 开始遍历输出
    traverse(content)