import json
from critic_search.llm_service import call_llm  # new import
from critic_search.config import settings           # new import if needed

# Filter out entries in "results" where raw_content is null/empty
def filter_results(data):
    data["results"] = [r for r in data.get("results", []) if r.get("raw_content")]
    return data

# Modified generate_markdown function per requested format
def generate_markdown(data):
    lines = []
    # Images section
    lines.append("# images \n")
    images = data.get("images", [])
    for idx, image in enumerate(images, start=1):
        desc = image.get("description") or "N/A"
        url = image.get("url") or "N/A"
        lines.append(f"[{idx}] DESCRIPTION: {desc}")
        lines.append(f"URL: {url}\n")
    # Search Results section
    lines.append("# Search Result\n")
    for idx, result in enumerate(data.get("results", []), start=1):
        title = result.get("title") or "N/A"
        url = result.get("url") or "N/A"
        raw = result.get("raw_content") or "N/A"
        lines.append(f"[{idx}]:TITLE: {title}")
        lines.append(f"URL: {url}")
        lines.append(f"CONTENT: {raw}\n")
    return "\n".join(lines)

if __name__ == "__main__":
    # 读取 JSON 文件
    with open('tavily_response_example.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    # 过滤掉 raw_content 为空的结果
    filtered_data = filter_results(data)
    # 生成 Markdown 字符串
    markdown_str = generate_markdown(filtered_data)
    # 输出结果
    # print(markdown_str)

    # Build final prompt including the query and markdown string
    query = data.get("query", "N/A")
    final_prompt = f"Query: {query}\n\n{markdown_str}"

    # Call LLM to get an answer based on the final prompt
    llm_response = call_llm(
        model=settings.default_model,
        usr_prompt=final_prompt,
        config=settings,
        tools=None,
        tool_choice="auto",
    )
    answer = llm_response.content if hasattr(llm_response, "content") else llm_response
    print("\nLLM Answer:\n")
    print(answer)