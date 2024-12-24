from .base_agent import BaseAgent
from .main import main
from pathlib import Path

def run_tasks(tasks: list, max_iterations: int = 10, output_file: Path | str = "conversation_history_sharegpt.jsonl"):
    """
    Function to handle multiple tasks, run them iteratively, and log conversation history.

    Parameters:
    - tasks (list): List of task strings (questions) to process.
    - max_iterations (int): Maximum number of iterations for each task.
    - output_file (Path | str): Path to save the conversation history in sharegpt format.
    """

    for task in tasks:
        # Run the main function for each task
        main(task, max_iterations)

        # Log conversation history after each task
        conversation_data = BaseAgent.conversation_manager.model_dump(context={"sharegpt": True})
        BaseAgent.conversation_manager.write(
            data=conversation_data,
            path=output_file,
        )