import json
import uuid  # 已有导入
from pathlib import Path
from jinja2 import Template
from .base_agent import BaseAgent
from .tools.tool_registry import ToolRegistry
from .utils import extract_tag_content
from .tools.note_manager import set_session, taking_notes, retrieve_notes  # 新增导入笔记工具
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

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
        # 捕获 JSON 解析及工具执行过程中所有错误，反馈给模型
        try:
            args = json.loads(args_str)
            # 执行工具调用
            result = registry.invoke_tool(tool_name, args)
        except json.JSONDecodeError as e:
            error_xml = (
                f"<tool_error>"
                f"<name>{tool_name}</name>"
                f"<message>JSON解析失败：{e}</message>"
                f"<arguments>{args_str}</arguments>"
                f"</tool_error>"
            )
            history.append({"role": "user", "content": error_xml})
            continue
        except Exception as e:
            error_xml = (
                f"<tool_error>"
                f"<name>{tool_name}</name>"
                f"<message>工具执行失败：{e}</message>"
                f"<arguments>{args_str}</arguments>"
                f"</tool_error>"
            )
            history.append({"role": "user", "content": error_xml})
            continue

        # 正常情况下，将工具输出以 XML 形式反馈给模型
        output_xml = (
            f"<tool_output>"
            f"<name>{tool_name}</name>"
            f"<result>{json.dumps(result, ensure_ascii=False)}</result>"
            f"</tool_output>"
        )
        history.append({"role": "user", "content": output_xml})

    return history


def main():
    parser = argparse.ArgumentParser(description="Run XML-based tool use workflow")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--query", "-q", help="Single user query to process")
    group.add_argument("--queries", "-Q", nargs="+", help="Multiple user queries to process concurrently")
    parser.add_argument("--workers", "-w", type=int, default=1, help="Max concurrent workers")
    parser.add_argument("--count", "-c", type=int, default=1, help="Number of identical runs (ignored if --queries)")
    args = parser.parse_args()

    # 决定要并发的 queries 列表
    if args.queries:
        queries = args.queries
    else:
        queries = [args.query] * args.count

    if len(queries) > 1:
        max_workers = min(args.workers, len(queries))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # future -> 原始 query
            futures = {executor.submit(run_workflow, q): q for q in queries}
            all_histories: dict[str, list] = {}
            for fut in as_completed(futures):
                q = futures[fut]
                all_histories[q] = fut.result()

        # 1) 输出每个 query 的完整 history
        print(json.dumps(all_histories, ensure_ascii=False, indent=2))
        # 2) 收集每个 query 的最后一次 assistant 回答
        final_answers = {q: history[-1]["content"] for q, history in all_histories.items()}
        print("===== 最终模型回答对比 =====")
        print(json.dumps(final_answers, ensure_ascii=False, indent=2))

    else:
        history = run_workflow(queries[0])
        print(json.dumps(history, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()


### use example
"""
python -m criticsearch.workflow --query "请你从网上搜索黄金最新的新闻并且记一下笔记，要求一定要使用记笔记的工具然后你还需要retrieve一下笔记检查一下保存的是否正确。如果正确再检索一下贸易战的新闻并且记笔记同时检索笔记看是否加入了新的笔记，需要全部进行验证。" --count 5 --workers 2

python -m criticsearch.workflow \
  --queries \
    "请你搜索AI技术的最新进展并且记一下笔记，然后retrieve一下笔记检查是否正确。检查后自己核实你检索回来的笔记和你自己记录的笔记是不是完全一致的然后告诉我结果" \
    "请你检索比特币价格走势并且记一下笔记，然后retrieve一下笔记检查是否正确。检查后自己核实你检索回来的笔记和你自己记录的笔记是不是完全一致的然后告诉我结果" \
    "请你查询全球气候变化最新报告并且记一下笔记，然后retrieve一下笔记检查是否正确。检查后自己核实你检索回来的笔记和你自己记录的笔记是不是完全一致的然后告诉我结果" \
    "请你搜索量子计算应用前景并且记一下笔记，然后retrieve一下笔记检查是否正确。检查后自己核实你检索回来的笔记和你自己记录的笔记是不是完全一致的然后告诉我结果" \
    "请你调研电动汽车市场分析并且记一下笔记，然后retrieve一下笔记检查是否正确。检查后自己核实你检索回来的笔记和你自己记录的笔记是不是完全一致的然后告诉我结果" \
  --workers 5

python -m criticsearch.workflow --query "请你调研电动汽车市场分析并且记一下笔记，然后retrieve一下笔记检查是否正确。检查后自己核实你检索回来的笔记和你自己记录的笔记是不是完全一致的然后告诉我结果" 

"""