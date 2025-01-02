from .log import logger
from .main import main


def run_tasks(
    tasks: list,
    max_iterations: int = 10,
):
    """
    Function to handle multiple tasks, run them iteratively, and log conversation history.

    Parameters:
    - tasks (list): List of task strings (questions) to process.
    - max_iterations (int): Maximum number of iterations for each task.
    """

    for task in tasks:
        main(task, max_iterations)

        logger.success(f"Task '{task}' completed successfully.")

        """
        # Log conversation history after each task in sharegpt format.
        conversation_data = BaseAgent.conversation_manager.model_dump(
            context={"sharegpt": True}
        )
        BaseAgent.conversation_manager.write(
            data=conversation_data,
            path=output_file,
        )
        """
