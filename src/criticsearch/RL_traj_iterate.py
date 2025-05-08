import json
from pathlib import Path
from typing import List

from criticsearch.base_agent import BaseAgent
from criticsearch.workflow import WorkflowExecutor
from criticsearch.reportbench.report_benchmark import ReportBenchmark
from criticsearch.reportbench.verifier import ReportVerifier
from criticsearch.utils import extract_tag_content

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
    for fname, user_prompt in mapping.items():
        candidate = benchmark_dir / fname
        if not candidate.exists():
            print(f"[WARN] JSON file {candidate} not found")
            continue

        bench = ReportBenchmark(str(candidate), user_query=user_prompt)
        benchmark_items = bench.generate_benchmark_item(use_cache=True)

        report = ''
        trajectory_list = []

        for section in benchmark_items:
            verifier = ReportVerifier(agent)
            section_title :str = section["path"]
            section_extracted_facts : List[dict] = section["extracted_facts"]
            
            full_prompt = (
                user_prompt + "\n" +
                f"Now, based on the background information above, do not generate a complete report, but instead generate the content of the section I am requesting. The section you need to generate currently is: {section_title}\n" +
                (f"Here is the content of the previous section you wrote for you reference: {report}\n You should keep writing the current section based on what you have already wrote" if section != benchmark_items[0] else "")+
                "Use the tools immediately in your answer, no spamming, and do not use the tools in the middle of the answer. "
            )

            runner = WorkflowExecutor(full_prompt)
        
            while True:
                response = runner.agent.chat(usr_prompt=runner.history)
                obs, reward, done, _ = runner.step(response)
                if done:
                    section_content = extract_tag_content(obs,"answer")
                    break   
            
            section_reward = verifier.verify_section(section_content, section_extracted_facts)

            report += f"Section: {section_title}\n"
            report += f"\n{section_content}\n"

            trajectory_list.append({
                "full_prompt": full_prompt,
                "section_content": section_content,
                "section_traj": runner._traj,
                "section_reward": section_reward,
            })
            yield trajectory_list

if __name__ == "__main__":
    # 尝试最多只打印 2 条 trajectory_list
    count = 0
    for traj in iterate_traj():
        print(json.dumps(traj, ensure_ascii=False, indent=2))
        count += 1
        if count >= 2:
            break


