from .run_tasks import run_tasks

# Example usage:
if __name__ == "__main__":
    tasks = [
        "Search for the information of a AI researcher Qinyu Luo",
    ]
    MAX_ITERATION = 10
    output_file = "conversation_history_sharegpt.jsonl"

    # Run the tasks with the specified number of iterations
    run_tasks(tasks, MAX_ITERATION, output_file)
