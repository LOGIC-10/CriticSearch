import json
import uuid
from pathlib import Path
from jinja2 import Template
from .base_agent import BaseAgent
from .tools.tool_registry import ToolRegistry
from .utils import extract_tag_content
from .tools.note_manager import set_session, taking_notes, retrieve_notes
from .reportbench.report_benchmark import ReportBenchmark
from .reportbench.verifier import ReportVerifier
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Dict  

class WorkflowExecutor:
    def __init__(self, user_query: str):
        # Initialize agent and registry
        self.agent = BaseAgent()
        self.registry = self.agent.tool_registry

        # 生成唯一 session_id 用于笔记绑定
        session_id = str(uuid.uuid4())
        set_session(session_id)

        # 注册工具并生成 schema
        tool_funcs = [
            self.agent.search_aggregator.search,
            self.agent.content_scraper.scrape,
            taking_notes,
            retrieve_notes,
        ]
        schemas = []
        for func in tool_funcs:
            schemas.extend(self.registry.get_or_create_tool_schema(func))

        # 加载并渲染 system prompt
        tpl_path = Path(self.agent.prompts_dir) / "tool_use.txt"
        tpl_str = tpl_path.read_text(encoding="utf-8")
        system_prompt = Template(tpl_str).render(
            AVAILABLE_TOOLS=json.dumps(schemas),
            USER_QUERY=user_query,
        )

        # 初始化对话历史、步数与轨迹
        self.history = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
        self._step_count = 0
        self._traj = []


    def step(self, action: str) -> Tuple[str, float, bool, Dict]:
        """
        执行一次 action：记录、工具解析与调用，并返回 (observation, reward, done, info)
        """
        self._step_count += 1
        self.history.append({"role": "assistant", "content": action})

        tool_xml = extract_tag_content(action, "tool_use")
        if not tool_xml:
            # 最终回答
            obs = action
            # evaluate reports for reward
            reward = 1 # TODO: 这里需要根据reportbenchmark当前section的extracted_facts考试来得到真实的acc（程序悖论）
            done = True
        else:
            # 解析工具调用
            tool_name = extract_tag_content(tool_xml, "name")
            arg_str = extract_tag_content(tool_xml, "arguments") or "{}"
            try:
                args = json.loads(arg_str)
            except json.JSONDecodeError:
                error_xml = (
                    f"<tool_use_result><name>{tool_name}</name>"
                    f"<error>arguments_not_json</error></tool_use_result>"
                )
                self.history.append({"role": "user", "content": error_xml})
                return error_xml, self.agent.cfg.invalid_penalty, False, {}

            # 执行工具
            try:
                result = self.registry.invoke_tool(tool_name, args)
                result_xml = (
                    f"<tool_use_result><name>{tool_name}</name>"
                    f"<result>{json.dumps(result, ensure_ascii=False)}</result>"
                    f"</tool_use_result>"
                )
                self.history.append({"role": "user", "content": result_xml})
                obs, reward, done = result, 0.0, False
            except Exception as exc:
                error_xml = (
                    f"<tool_use_result><name>{tool_name}</name>"
                    f"<error>{str(exc)}</error></tool_use_result>"
                )
                self.history.append({"role": "user", "content": error_xml})
                return error_xml, self.agent.cfg.invalid_penalty, False, {}

        # 记录轨迹
        self._traj.append({"a": action, "r": reward})
        obs_str = json.dumps(obs, ensure_ascii=False) if isinstance(obs, (dict, list)) else str(obs)
        self._last_obs = obs_str
        return self._last_obs, reward, done, {}

# ------------ run_workflow使用 WorkflowExecutor.step ------------
def run_workflow(user_query: str) -> list[dict]:
    runner = WorkflowExecutor(user_query)

    while True:
        # Assistant suggests next action或最终回答
        response = runner.agent.chat(usr_prompt=runner.history)
        obs, reward, done, _ = runner.step(response)
        if done:
            break

    return runner.history

def iterate_traj():
    """
    Evaluate a single section's factual accuracy as reward.
    """
    agent = BaseAgent()
    # For per-section evaluation, load mapping to find current JSON and prompt
    mapping_path = Path(__file__).parent / "reportbench" / "instruction_mapping.json"
    try:
        mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    except Exception:
        print(f"[WARN] Cannot load instruction mapping from {mapping_path}")
        return 0.0
    # find JSON file matching this user_query
    benchmark_dir = Path(__file__).parent / "reportbench" / "wiki_data"
    for fname, user_prompt in mapping.items(): # 我在这里遍历构建的所有的user prompt来运行不同的section trajectory
        
        candidate = benchmark_dir / fname
        if not candidate.exists():
            print(f"[WARN] JSON file {candidate} not found")
            continue

        # generate benchmark items for sections
        bench = ReportBenchmark(str(candidate), user_query=user_prompt)
        benchmark_items = bench.generate_benchmark_item(use_cache=True) #  benchmark_items是一个json list

        # 从这里开始构建 背景信息+section信息+之前写作段落信息的 context供模型参考来写当前的section，然后进行verify得到当前section的reward
        # 1) 背景信息 就是 user_query
        # 2) section信息 就是 section的title，section内容要模型自己写
        # 3) 之前写作段落信息 就是之前answer tag里面的内容，所有的拼接起来

        report = ''
        trajectory_list = []

        for section in benchmark_items:
            verifier = ReportVerifier(agent)
            section_title :str = section["path"]
            section_extracted_facts : List[dict] = section["extracted_facts"] # 有了模型的section answer和这里的extracted_facts就可以调用verifier来验证了
            
            # 调用step函数来得到section answer
            full_prompt = (
                user_prompt + "\n" +
                f"Now, based on the background information above, do not generate a complete report, but instead generate the content of the section I am requesting. The section you need to generate currently is: {section_title}\n" +
                (f"Here is the content of the previous section you wrote for you reference: {report}\n You should keep writing the current section based on what you have already wrote" if section != benchmark_items[0] else "")+
                "Use the tools immediately in your answer, no spamming, and do not use the tools in the middle of the answer. "

            )

            runner = WorkflowExecutor(full_prompt)
            # from IPython import embed; embed()
        
            while True:
                # Assistant suggests next action或最终回答
                response = runner.agent.chat(usr_prompt=runner.history)
                obs, reward, done, _ = runner.step(response)
                if done:
                    section_content = extract_tag_content(obs,"answer")
                    break   
            
            section_reward = verifier.verify_section(section_content, section_extracted_facts)

            # 逐渐拼接每个section的内容作为前文写作的背景
            report += f"Section: {section_title}\n"
            report += f"\n{section_content}\n"

            trajectory_list.append({
                "full_prompt": full_prompt,
                "section_content": section_content,
                "section_traj": runner._traj,
                "section_reward": section_reward,
            })
            # 每产生一个 section 的轨迹就立刻产出
            yield trajectory_list

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

# if __name__ == "__main__":
#     # main()
#     iterate_traj()

if __name__ == "__main__":
    import json
    # 尝试最多只打印 2 条 trajectory_list
    count = 0
    for traj in iterate_traj():
        print(json.dumps(traj, ensure_ascii=False, indent=2))
        count += 1
        if count >= 2:
            break

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