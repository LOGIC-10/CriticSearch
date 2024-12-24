from datasets import load_dataset
from critic_search.run_tasks import run_tasks

train_ds = load_dataset("google/boolq", split="train")

tasks = train_ds["question"][:2]

# # Run the tasks with max_iterations and specify the output file
run_tasks(tasks, max_iterations=10, output_file="sharegpt_eval.json")
