from criticsearch.tasks_runner import run_tasks

# Example usage:
if __name__ == "__main__":
    tasks = [
        "写一篇不少于2000字的报告，阐述美国和俄罗斯关系的最新变化"
    ]
    MAX_ITERATION = 20
    output_file = "conversation_history_sharegpt.jsonl"

    # Run the tasks with the specified number of iterations
    run_tasks(tasks, MAX_ITERATION, output_file)
