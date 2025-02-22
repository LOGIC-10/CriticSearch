from criticsearch.tasks_runner import run_tasks

# Example usage:
if __name__ == "__main__":
    tasks = [
        "How will the introduction of central bank digital currencies (CBDCs) impact the traditional banking system and financial stability in the next five years?",
        # "What are the potential benefits and challenges of using AI-driven predictive maintenance in the manufacturing industry, and how can companies effectively implement such systems?"
    ]
    MAX_ITERATION = 20
    output_file = "conversation_history_sharegpt.jsonl"

    # Run the tasks with the specified number of iterations
    run_tasks(tasks, MAX_ITERATION, output_file)
