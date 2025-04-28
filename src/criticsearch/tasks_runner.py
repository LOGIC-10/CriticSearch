import argparse
from pathlib import Path

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
    args = parser.parse_args()

    # 如果没传 tasks，就使用默认列表
    tasks = args.tasks or [
        "write an 2024 Syrian opposition_offensives comprehensive report",
    ]

    try:
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
# 不指定文件名，用默认 2024_Syrian_opposition_offensives.json
criticsearch "给我写一份2024年叙利亚反对派进攻战役概述" -n 5

# 指定文件名
criticsearch "给我写一份2024年叙利亚反对派进攻战役概述" -n 5 -f my_custom_data.json"""