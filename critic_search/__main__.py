from .run_tasks import run_tasks

# Example usage:
if __name__ == "__main__":
    tasks = [
        """Which interdisciplinary scholar, renowned for their contributions to both artificial intelligence and neuroethics, currently holds a faculty position in the Department of Cognitive Science at a university, and has co-authored a seminal paper on the ethical implications of AI in medical decision-making?""",
        """What are the ethical considerations surrounding the use of AI in autonomous vehicles, and how might this affect regulatory frameworks?"""
    ]
    MAX_ITERATION = 5
    output_file = "conversation_history_sharegpt.jsonl"

    # Run the tasks with the specified number of iterations
    run_tasks(tasks, MAX_ITERATION, output_file)
