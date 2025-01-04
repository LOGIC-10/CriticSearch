# tasks_runner.py
from .log import logger


def run_tasks(tasks, max_iterations=10):
    """
    Run multiple tasks iteratively.

    Args:
        tasks (list of str): List of tasks (questions) to process.
        max_iterations (int): Maximum number of iterations for each task.
    """
    if not tasks:
        logger.error("No tasks provided. Please specify at least one task.")
        return

    from .main import main

    for task in tasks:
        main(task, max_iterations)
        logger.success(f"Task '{task}' completed successfully.")

        # Example for logging conversation history (optional)
        # conversation_data = BaseAgent.conversation_manager.model_dump(
        #     context={"sharegpt": True}
        # )
        # BaseAgent.conversation_manager.write(
        #     data=conversation_data,
        #     path=output_file,
        # )
