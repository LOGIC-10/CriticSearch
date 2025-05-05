import json
from pathlib import Path
from jinja2 import Template
from .base_agent import BaseAgent
from .tools.tool_registry import ToolRegistry
from .utils import extract_tag_content

def run_workflow(user_query: str) -> list[dict]:
    # Initialize agent and registry
    agent = BaseAgent()
    registry = agent.tool_registry

    # Register tools and generate schemas
    tool_funcs = [agent.search_aggregator.search, agent.content_scraper.scrape]
    schemas = []
    for func in tool_funcs:
        schemas.extend(registry.get_or_create_tool_schema(func))

    # Load and render system prompt from XML tool_use template
    tpl_path = Path(agent.prompts_dir) / "tool_use.txt"
    tpl_str = tpl_path.read_text(encoding="utf-8")
    system_prompt = Template(tpl_str).render(
        AVAILABLE_TOOLS=json.dumps(schemas),
        USER_QUERY=user_query
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

python -m criticsearch.workflow --query "你的问题"
"""