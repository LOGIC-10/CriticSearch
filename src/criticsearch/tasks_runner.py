import argparse
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from criticsearch.base_agent import BaseAgent
from criticsearch.config import settings
from criticsearch.main import process_single_task


def execute_multiple_tasks(
    tasks: list,
    max_iterations: int = 10,
    output_file: Path | str = "conversation_history_sharegpt.jsonl",
    file_name: str = None,
):
    """
    Function to execute multiple tasks, process them iteratively, and log conversation history.

    Parameters:
    - tasks (list): List of task strings (questions) to process.
    - max_iterations (int): Maximum number of iterations for each task.
    - output_file (Path | str): Path to save the conversation history in ShareGPT format.
    - file_name (str): Optional file name to load GT JSON.
    """

    for task in tasks:
        # Execute a single task
        process_single_task(task, max_iterations, file_name)

        if settings.save_sharegpt:
            # TODO: When dealing with multiple tasks, we need to save different conversation histories to different files.
            conversation_data = BaseAgent.conversation_manager.model_dump(
                context={"sharegpt": True}
            )
            BaseAgent.conversation_manager.write(
                data=conversation_data,
                path=output_file,
            )


def execute_from_mapping(
    mapping_file: Path | str,
    max_iterations: int,
    concurrent: bool,
    workers: int,
    limit: int | None = None,
):
    """
    从 mapping_file 加载 {file_name: instruction}，
    并对每一对 (instruction, file_name) 调用 process_single_task。
    支持并发和限量。
    """
    mapping_path = Path(mapping_file)
    with mapping_path.open(encoding="utf-8") as f:
        mapping = json.load(f)

    items = list(mapping.items())
    if limit:
        items = items[:limit]

    def run(pair):
        file_name, task = pair
        print(f"[INFO] start task for {file_name}")
        process_single_task(task, max_iterations, file_name=file_name)

    if concurrent and workers > 1:
        with ThreadPoolExecutor(max_workers=workers) as exe:
            futures = {exe.submit(run, pair): pair for pair in items}
            for fut in as_completed(futures):
                fn, _ = futures[fut]
                try:
                    fut.result()
                    print(f"[INFO] done {fn}")
                except Exception as e:
                    print(f"[ERROR] {fn} failed: {e}")
    else:
        for pair in items:
            run(pair)


def start_task_execution():
    """
    Entry point to start executing predefined or CLI-specified tasks.
    """
    parser = argparse.ArgumentParser(description="批量执行 CriticSearch 任务")
    parser.add_argument(
        "tasks", nargs="*", help="要执行的任务列表；不传时使用默认列表"
    )
    parser.add_argument(
        "-n", "--max-iterations", type=int, default=2, help="每个任务的最大迭代次数"
    )
    parser.add_argument(
        "-f", "--file-name", type=str, default=None, help="指定要加载的 GT JSON 文件名"
    )
    parser.add_argument(
        "-o", "--output-file", type=Path, default="conversation_history_sharegpt.jsonl",
        help="保存 ShareGPT 历史的输出文件"
    )
    # 新增批量映射执行参数
    parser.add_argument(
        "--from-mapping", action="store_true",
        help="从 mapping 文件批量读取 instruction 和 file_name 并执行"
    )
    parser.add_argument(
        "--mapping-file", type=Path,
        default=Path(__file__).parent / "reportbench" / "instruction_mapping.json",
        help="指定 instruction_mapping.json 路径"
    )
    parser.add_argument(
        "--concurrent", action="store_true",
        help="是否并发执行批量写作任务"
    )
    parser.add_argument(
        "-w", "--workers", type=int, default=5,
        help="并发时的最大线程数"
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="只执行前 N 个映射条目"
    )
    args = parser.parse_args()

    try:
        if args.from_mapping:
            execute_from_mapping(
                mapping_file=args.mapping_file,
                max_iterations=args.max_iterations,
                concurrent=args.concurrent,
                workers=args.workers,
                limit=args.limit,
            )
        else:
            # 如果没传 tasks，就使用默认
            tasks = args.tasks or [
                "write an 2024 Syrian opposition_offensives comprehensive report",
            ]
            execute_multiple_tasks(
                tasks,
                args.max_iterations,
                args.output_file,
                file_name=args.file_name,
            )
    except KeyboardInterrupt:
        print("Execution interrupted by the user.")


if __name__ == "__main__":
    start_task_execution()


# Usage example:
"""
# 1. 单个任务执行（使用默认 GT JSON）
criticsearch "给我写一份2024年叙利亚反对派进攻战役概述" -n 5

# 2. 单个任务并指定 GT 文件
criticsearch "给我写一份2024年叙利亚反对派进攻战役概述" -n 5 -f custom_data.json

# 3. 多任务顺序执行（自定义任务列表）
criticsearch "任务一描述" "任务二描述" -n 4

# 4. 指定输出文件保存 ShareGPT 会话历史
criticsearch "任务描述" -n 2 -o my_history.jsonl

# 5. 从映射文件批量执行，顺序模式
criticsearch --from-mapping --mapping-file /path/to/instruction_mapping.json -n 3

# 6. 从映射文件批量执行，并发模式（5 线程）
criticsearch --from-mapping --concurrent -w 5 --mapping-file /path/to/instruction_mapping.json -n 3

# 7. 从映射文件批量执行，限量前 10 条，并发模式
criticsearch --from-mapping --concurrent -w 5 --limit 10

# 8. 使用默认映射文件路径，并发执行所有条目
criticsearch --from-mapping --concurrent -w 10 -n 2
"""