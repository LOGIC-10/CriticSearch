## FunctionDef setup_logger
**setup_logger**: The function of setup_logger is to configure and return a logger instance for logging messages related to the agent.

**parameters**: The parameters of this Function.
· parameter1: None

**Code Description**: The setup_logger function initializes a logger specifically named 'AgentLogger'. It sets the logging level to INFO, which means that the logger will capture all messages at the INFO level and above (e.g., WARNING, ERROR, CRITICAL). The function then creates a console handler (ch) that also has its logging level set to INFO. This handler is responsible for outputting log messages to the console. The console handler is added to the logger, allowing it to display log messages in the terminal or command prompt. Finally, the logger instance is returned for use in other parts of the application.

**Note**: It is important to ensure that the logging configuration is set up before any logging calls are made in the application. This function does not take any parameters and should be called at the beginning of the program to establish the logging framework.

**Output Example**: A possible appearance of the code's return value when logging an INFO message might look like this in the console:
```
INFO:AgentLogger:This is an informational message.
```
## FunctionDef main
**main**: The function of main is to execute a series of iterations that involve evaluating a task, generating responses, and refining search plans based on agent interactions and feedback.

**parameters**: The parameters of this Function.
· None

**Code Description**: The main function orchestrates a loop that runs for a predefined number of iterations, specified by the constant MAX_ITERATION. In each iteration, it logs the current iteration number with a formatted message. During the first iteration, it checks the confidence of a model related to a specific task (TASK). If the model is confident, it generates a response using the common agent's chat function. If the model is not confident, it initializes a search plan, extracts search queries, performs a parallel search, and formats the results for logging. The search results are then used to create a prompt for the common agent to generate an answer.

In subsequent iterations, the function updates the agent's answer based on the previous answer, search results, and feedback from a critic agent. The critic agent evaluates the common agent's response and provides feedback, which is logged. The function then generates a new search plan based on the common agent's answer and the critic's feedback, updates the query database with new search queries, and performs another parallel search to gather updated results. Each significant step is logged with formatted messages to provide clarity on the process and outcomes.

**Note**: It is important to ensure that the constants and external functions (like common_agent and CriticAgent) are properly defined and initialized before invoking the main function. The logging framework must also be configured to capture the output effectively.
