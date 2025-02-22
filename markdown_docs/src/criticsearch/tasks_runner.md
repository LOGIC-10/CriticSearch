## FunctionDef run_tasks(tasks, max_iterations, output_file)
**run_tasks**: The function of run_tasks is to handle multiple tasks, run them iteratively, and log conversation history.

**parameters**: The parameters of this Function.
· tasks: list - A list of task strings (questions) to process.
· max_iterations: int - Maximum number of iterations for each task (default is 10).
· output_file: Path | str - Path to save the conversation history in sharegpt format (default is "conversation_history_sharegpt.jsonl").

**Code Description**: The run_tasks function is designed to manage the execution of a series of tasks, iterating through each task and performing operations to generate responses while logging the conversation history. The function accepts a list of tasks, a maximum number of iterations for processing each task, and a file path for saving the conversation history.

For each task in the provided list, the function invokes the main function, which is responsible for processing the task and generating responses. The main function is called with the current task and the specified maximum number of iterations. This function is integral to the overall architecture, as it utilizes the BaseAgent class to manage conversations and interactions.

After executing the main function for a task, the run_tasks function retrieves the conversation data from the BaseAgent's conversation manager. It then writes this data to the specified output file using the write method of the conversation manager. This ensures that the conversation history is preserved in a structured format, allowing for future reference or analysis.

The run_tasks function is called by other components in the project, such as the main execution flow in the src/criticsearch/__main__.py file and potentially other scripts that require batch processing of tasks. This establishes a clear pathway for task management and response generation within the intelligent agent framework.

**Note**: When using this function, ensure that the tasks provided are well-defined and relevant to the capabilities of the underlying agent. Additionally, be mindful of the output file path, as the function appends data to the file, which may grow in size over time. If the file contains corrupt or non-JSON data, the function may start with an empty list, potentially overwriting previous content.
