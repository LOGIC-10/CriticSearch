import json
import argparse
import traceback        
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from criticsearch.base_agent import BaseAgent
from criticsearch.config import settings
from criticsearch.main import process_single_task


def execute_multiple_tasks(
    tasks: list,
    output_file: Path | str = "conversation_history_sharegpt.jsonl",
    file_name: str = None,
    conv_dir: Path | str = "conversation_histories",
):
    """
    顺序执行多个写作任务，并为每个任务保存对话历史。

    先清空会话管理器，然后调用 process_single_task 完成单个任务。
    完成后将对话历史保存到 conv_dir/<前缀>_<timestamp>_conversation.json。

    Args:
        tasks (list[str]): 待执行的写作指令列表。
        output_file (Path|str): （未使用）保留以兼容上一版接口。
        file_name (str|None): 如果指定，则将其作为前缀；否则使用任务文本生成前缀。
        conv_dir (Path|str): 保存对话历史文件的目录，按需自动创建。

    Returns:
        None
    """
    conv_dir = Path(conv_dir)
    conv_dir.mkdir(parents=True, exist_ok=True)

    for task in tasks:
        try:
            BaseAgent.conversation_manager.clear_history()
            records = process_single_task(task, file_name=file_name)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[ERROR] skip task `{task}` due to invalid JSON file `{file_name}`: {e}")
            continue
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = Path(file_name).stem if file_name else task.replace(" ", "_")[:50]
        out_path = conv_dir / f"{prefix}_{ts}_conversation.json"
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        print(f"[INFO] saved conversation to {out_path}")


def execute_from_mapping(
    mapping_file: Path | str,
    concurrent: bool,
    workers: int,
    limit: int | None = None,
    conv_dir: Path | str = "conversation_histories",
):
    """
    从 instruction_mapping.json 批量调度写作任务，支持顺序或并发执行。

    根据 mapping_file 加载 {file_name: instruction} 映射表，可指定 limit
    只执行前 N 条。对于每一对 (file_name, instruction)，先清空会话管理器，
    再调用 process_single_task 完成写作；完成后将对话历史保存到
    conv_dir/<file_stem>_<timestamp>_conversation.json。

    Args:
        mapping_file (Path|str): instruction_mapping.json 文件路径。
        concurrent (bool): 是否并发执行所有任务。
        workers (int): 并发模式下的最大线程数。
        limit (int|None): 限制最多执行的条目数，None 表示不限制。
        conv_dir (Path|str): 保存对话历史的目录。

    Returns:
        None
    """
    # 并发时禁止在 process_single_task 中启动 Rich Live 渲染
    if concurrent:
        from criticsearch.config import settings
        setattr(settings, "disable_progress", True)

    conv_dir = Path(conv_dir)
    conv_dir.mkdir(parents=True, exist_ok=True)

    # 在这里单独处理 mapping.json 的 parse 错误
    try:
        mapping = json.loads(Path(mapping_file).read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"[ERROR] 无法解析映射文件 {mapping_file}: {e}")
        return

    items = list(mapping.items())
    if limit:
        items = items[:limit]

    def run(pair):
        file_name, task = pair
        try:
            BaseAgent.conversation_manager.clear_history()
            # 真正跑写作主流程
            records = process_single_task(task, file_name=file_name)
        except FileNotFoundError as e:
            # GT JSON 不存在，才跳过
            print(f"[ERROR] skip `{file_name}`: 文件不存在: {e}")
            traceback.print_exc()                            # 打印详细堆栈
            return
        except Exception as e:
            # 其余所有异常都打印但不当作“无效 JSON”跳过
            print(f"[ERROR] task `{file_name}` 执行失败: {e}")
            traceback.print_exc()                            # 打印详细堆栈
            return

        # 到这里说明 process_single_task 正常返回了 records
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = Path(file_name).stem + f"_{ts}_conversation.json"
        out_path = conv_dir / out
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        print(f"[INFO] saved {file_name} → {out_path}")

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
    CLI 入口：解析命令行参数并调度执行。

    支持单任务模式和映射文件批量模式。可通过 --from-mapping 切换，
    并通过 --concurrent、--workers 控制并发，--limit 控制条目数，
    --conv-dir 指定对话历史保存目录。

    CLI 参数:
        tasks (positional): 不指定 --from-mapping 时，作为单任务列表。
        -f, --file-name: 单任务模式下的 GT JSON 文件名。
        -o, --output-file: 单任务模式下的历史保存文件，兼容旧版。
        --from-mapping: 批量模式开关。
        --mapping-file: 指定映射文件路径，默认 reportbench/instruction_mapping.json。
        --concurrent: 批量模式下并发执行任务。
        -w, --workers: 并发时线程数，默认 5。
        --limit: 批量时最多执行条目数，默认无限制。
        --conv-dir: 对话历史保存目录，默认 conversation_histories。

    Returns:
        None
    """
    parser = argparse.ArgumentParser(description="批量执行 CriticSearch 任务")
    parser.add_argument("tasks", nargs="*", help="要执行的任务列表；不传时使用默认")
    parser.add_argument("-f", "--file-name", type=str, default=None,
                        help="单任务模式下的 GT JSON 文件名")
    parser.add_argument("-o", "--output-file", type=Path,
                        default="conversation_history_sharegpt.jsonl",
                        help="单任务模式下的历史保存文件")
    parser.add_argument("--from-mapping", action="store_true",
                        help="从映射文件批量执行任务")
    parser.add_argument("--mapping-file", type=Path,
                        default=Path(__file__).parent / "reportbench" / "instruction_mapping.json",
                        help="instruction_mapping.json 路径")
    parser.add_argument("--concurrent", action="store_true",
                        help="批量模式下并发执行任务")
    parser.add_argument("-w", "--workers", type=int, default=5,
                        help="并发时的线程数")
    parser.add_argument("--limit", type=int, default=None,
                        help="批量执行时最多执行条目数")
    parser.add_argument("--conv-dir", type=Path, default=Path("conversation_histories"),
                        help="对话历史保存目录")
    args = parser.parse_args()

    if args.from_mapping:
        mf = args.mapping_file
        if not mf.is_absolute():
            args.mapping_file = Path(__file__).parent / mf
    # ——————————————————————————————————————————————————————————

    try:
        if args.from_mapping:
            execute_from_mapping(
                mapping_file=args.mapping_file,
                concurrent=args.concurrent,
                workers=args.workers,
                limit=args.limit,
                conv_dir=args.conv_dir,
            )
        else:
            tasks = args.tasks or [
                "write an 2024 Syrian opposition_offensives comprehensive report",
            ]
            execute_multiple_tasks(
                tasks,
                args.output_file,
                file_name=args.file_name,
                conv_dir=args.conv_dir,
            )
    except KeyboardInterrupt:
        print("Execution interrupted by the user.")


if __name__ == "__main__":
    start_task_execution()

# Usage example:
"""
1. 单任务模式（默认 GT JSON）：
criticsearch "给我写一份2024年叙利亚反对派进攻战役概述"

2. 单任务模式 + 自定义 GT JSON：
criticsearch "写一个报告讨论一下2024_Belgian_federal_election事件,要求详细全面" -f 2024_Belgian_federal_election.json

3. 多任务顺序执行：
criticsearch "任务A描述" "任务B描述" --conv-dir my_history_dir

4. 从映射文件顺序批量执行：
criticsearch --from-mapping --mapping-file reportbench/instruction_mapping.json

5. 并发模式 + 指定线程数：
criticsearch --from-mapping --concurrent -w 10

6. 并发模式 + 限制条目数：
criticsearch --from-mapping --concurrent --workers 30 --limit 30

7. 自定义对话历史保存目录：
criticsearch --from-mapping --concurrent --limit 10 --conv-dir ./logs

8. Python 模块方式直接运行（绕过 console‑script）：
python -m criticsearch.tasks_runner --from-mapping --concurrent -w 5
"""