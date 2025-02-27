from criticsearch.tasks_runner import run_tasks

# Example usage:
if __name__ == "__main__":
    tasks = [
        "Write a report about 2024_Syrian_opposition_offensives event",
    ]
    MAX_ITERATION = 20
    output_file = "conversation_history_sharegpt.jsonl"

    # Run the tasks with the specified number of iterations
    run_tasks(tasks, MAX_ITERATION, output_file)
