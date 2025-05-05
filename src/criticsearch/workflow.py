import json
import uuid  # 已有导入
from pathlib import Path
from jinja2 import Template
from .base_agent import BaseAgent
from .tools.tool_registry import ToolRegistry
from .utils import extract_tag_content
from .tools.note_manager import set_session, taking_notes, retrieve_notes  # 新增导入笔记工具

def run_workflow(user_query: str) -> list[dict]:
    # Initialize agent and registry
    agent = BaseAgent()
    registry = agent.tool_registry
    # 生成唯一session_id用于笔记绑定
    session_id = str(uuid.uuid4())
    # 设置当前Session ID到上下文
    set_session(session_id)

    # Register tools and generate schemas (包含搜索、爬取及笔记工具)
    tool_funcs = [
        agent.search_aggregator.search,
        agent.content_scraper.scrape,
        taking_notes,
        retrieve_notes,
    ]
    schemas = []
    for func in tool_funcs:
        schemas.extend(registry.get_or_create_tool_schema(func))

    # Load and render system prompt from XML tool_use template
    tpl_path = Path(agent.prompts_dir) / "tool_use.txt"
    tpl_str = tpl_path.read_text(encoding="utf-8")
    system_prompt = Template(tpl_str).render(
        AVAILABLE_TOOLS=json.dumps(schemas),
        USER_QUERY=user_query,
    )

    # Initialize chat history
    history = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query}
    ]

    # Iteratively handle tool calls: model emits <tool_use>, execute tool, feed result back
    while True:
        # Assistant suggests next action or final answer
        response = agent.chat(usr_prompt=history)
        history.append({"role": "assistant", "content": response})

        # Check if model wants to use a tool
        tool_use_xml = extract_tag_content(response, "tool_use")
        if not tool_use_xml:
            # no more tool calls; workflow ends
            break

        # Parse tool name and arguments
        tool_name = extract_tag_content(tool_use_xml, "name")
        args_str = extract_tag_content(tool_use_xml, "arguments")
        args = json.loads(args_str)

        # Invoke the tool and capture result
        result = registry.invoke_tool(tool_name, args)

        # Append tool result to history for next turn
        tool_result_xml = (
            f"<tool_use_result>"
            f"<name>{tool_name}</name>"
            f"<result>{json.dumps(result, ensure_ascii=False, indent=2)}</result>"
            f"</tool_use_result>"
        )
        history.append({"role": "user", "content": tool_result_xml})

    return history


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run XML-based tool use workflow")
    parser.add_argument("--query", "-q", required=True, help="User query to process")
    args = parser.parse_args()
    history = run_workflow(args.query)
    print(json.dumps(history, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()


### use example
"""

python -m criticsearch.workflow --query "请你从网上搜索黄金最新的新闻并且记一下笔记，要求一定要使用记笔记的工具然后你还需要retrieve一下笔记检查一下保存的是否正确。如果正确再检索一下贸易战的新闻并且记笔记同时检索笔记看是否加入了新的笔记，需要全部进行验证。"
"""