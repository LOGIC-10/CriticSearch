from pathlib import Path

from criticsearch.base_agent import BaseAgent
from criticsearch.config import settings
from criticsearch.main import process_single_task


def execute_multiple_tasks(
    tasks: list,
    max_iterations: int = 10,
    output_file: Path | str = "conversation_history_sharegpt.jsonl",
):
    """
    Function to execute multiple tasks, process them iteratively, and log conversation history.

    Parameters:
    - tasks (list): List of task strings (questions) to process.
    - max_iterations (int): Maximum number of iterations for each task.
    - output_file (Path | str): Path to save the conversation history in ShareGPT format.
    """

    for task in tasks:
        # Execute a single task
        process_single_task(task, max_iterations)

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
    Entry point to start executing predefined tasks.
    """
    tasks = [
        "Write a report about 2024_Syrian_opposition_offensives event",
    ]
    MAX_ITERATION = 2
    try:
        # Execute multiple tasks with the specified number of iterations
        execute_multiple_tasks(tasks, MAX_ITERATION)
    except KeyboardInterrupt:
        print("Execution interrupted by the user.")


if __name__ == "__main__":
    start_task_execution()
