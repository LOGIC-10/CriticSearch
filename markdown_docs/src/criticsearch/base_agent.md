## ClassDef BaseAgent
**BaseAgent**: The function of BaseAgent is to serve as a foundational class for implementing an intelligent agent that can manage conversations, perform searches, and interact with various tools.

**attributes**: The attributes of this Class.
· queryDB: A set to store unique queries made by the agent during its operation.  
· tool_registry: An instance of ToolRegistry that manages the schemas for tools used by the agent.  
· user_question: A string that holds the current question posed by the user.  
· conversation_manager: An instance of ConversationManager responsible for maintaining the history of the conversation.  
· prompts_dir: A string that specifies the directory path where template prompt files are stored.  
· citationDB: A list of dictionaries that contains search queries and their corresponding results, specifically those praised by a critic.  
· search_aggregator: An instance of SearchAggregator that facilitates search operations.  
· search_aggregator_schema: A schema representation of the search aggregator tool, retrieved from the tool registry.  
· content_scraper: An instance of ContentScraper that handles web scraping tasks.  
· content_scraper_schema: A schema representation of the content scraper tool, retrieved from the tool registry.  
· repeat_turns: An integer that defines the number of times the agent will repeat its search and interaction process.

**Code Description**: The BaseAgent class is designed to provide a structured framework for building intelligent agents that can engage in conversations, perform searches, and utilize various tools effectively. Upon initialization, the class sets up several key components, including the conversation manager, tool registry, and search aggregator. 

The conversation manager is responsible for tracking the history of interactions, while the tool registry allows the agent to manage and retrieve schemas for different tools it may use. The citationDB is specifically designed to store search results that have received positive feedback from a critic, ensuring that the agent can reference high-quality information.

The class provides several methods for loading templates, rendering them with data, and managing conversations. The `common_chat` method is overloaded to handle different types of user prompts, allowing for flexible interactions. The `update_answer` method enables the agent to refine its responses based on previous answers and feedback from critics.

Additionally, the `search_and_browse` method integrates both search and web scraping functionalities, allowing the agent to gather information from various sources and present it to the user. The `model_confident` method checks the agent's confidence in its responses, guiding its decision-making process on whether to provide an answer or seek additional information.

The BaseAgent class is utilized in various parts of the project, including the CriticAgent, which extends its functionality to generate critiques based on the agent's responses. The main function in the project initializes an instance of BaseAgent to handle user tasks, demonstrating its role as a central component in the overall architecture.

**Note**: It is essential to ensure that the tool registry is populated with the necessary schemas for the tools being used, as the agent relies on these schemas for proper functionality. Additionally, the citationDB should be managed carefully to maintain the quality of information referenced by the agent.

**Output Example**: A possible appearance of the code's return value when performing a search might look like this:
```json
{
  "search_results": [
    {
      "document_id": "12345",
      "url": "https://example.com/article",
      "title": "Understanding the Challenges Faced by Google in 2019",
      "content": "In 2019, Google faced several challenges including..."
    }
  ],
  "conversation_history": [
    {"role": "user", "content": "What challenges did Google face in 2019?"},
    {"role": "assistant", "content": "Google faced several challenges including..."}
  ]
}
```
### FunctionDef __init__(self)
**__init__**: The function of __init__ is to initialize an instance of the BaseAgent class, setting up necessary directories, databases, and tools for the agent's operation.

**parameters**: The parameters of this Function.
· None

**Code Description**: The __init__ method is the constructor for the BaseAgent class. It is responsible for initializing various components that the agent will use during its operation. 

1. **Directory Setup**: The method begins by determining the base directory of the current script using `os.path.dirname(os.path.abspath(__file__))`. This directory is essential for locating resources related to the agent, specifically the prompts directory, which is constructed by joining the base directory with the string "prompts".

2. **Citation Database Initialization**: The `citationDB` attribute is initialized as a list containing a single dictionary. This dictionary is designed to store search queries as keys and their corresponding results as values. The comment indicates that only search results praised by a critic will be included in this database. Each entry in the citationDB is structured to hold a unique document identifier along with its associated metadata, such as URL, title, and content.

3. **Search Aggregator Setup**: An instance of the `SearchAggregator` class is created and assigned to the `search_aggregator` attribute. This component is responsible for managing search queries across multiple search engines.

4. **Tool Schema Creation**: The method retrieves or creates schemas for the search aggregator and content scraper tools using the `get_or_create_tool_schema` method from the `tool_registry`. This method ensures that the schemas for these tools are registered and available for use in the agent's operations. The schemas are stored in `search_aggregator_schema` and `content_scraper_schema` attributes, respectively.

5. **Content Scraper Initialization**: An instance of the `ContentScraper` class is created and assigned to the `content_scraper` attribute. This component is responsible for scraping content from specified URLs.

6. **Updating Available Tools**: The method updates the `available_tools` attribute of the `conversation_manager` class variable in BaseAgent to include the schemas for both the content scraper and the search aggregator. This allows the agent to utilize these tools during interactions.

7. **Repeat Turns Configuration**: Finally, the `repeat_turns` attribute is initialized to 10, which likely indicates the number of times the agent can repeat a search or interaction before stopping.

The __init__ method is crucial for setting up the BaseAgent instance with all necessary components and configurations, ensuring that it is ready to perform its intended functions effectively.

**Note**: When using this method, it is important to ensure that the required directories and tools are correctly set up in the environment. Additionally, the proper functioning of the search aggregator and content scraper depends on the availability of their respective configurations and API keys.
***
### FunctionDef load_template(self, filename)
## Function: `load_template`

### Overview:
The `load_template` function is responsible for loading a template file from a predefined directory and returning its contents as a string. This method is particularly useful for retrieving text-based templates that can be rendered or processed further in the application.

### Method Signature:
```python
def load_template(self, filename)
```

### Parameters:
- **`filename`** (str): The name of the template file to be loaded. This should be a valid filename present within the specified prompts directory.

### Returns:
- **str**: The content of the template file as a string.

### Raises:
- **FileNotFoundError**: If the specified template file does not exist in the prompts directory, this error is raised with a descriptive message indicating the missing file.

### Detailed Description:
The `load_template` function performs the following steps:
1. It constructs the full file path by combining the predefined prompts directory (`self.prompts_dir`) with the provided `filename`.
2. It checks if the file exists at the constructed path.
3. If the file does not exist, it raises a `FileNotFoundError` with a detailed message about the missing file.
4. If the file is found, it opens the file in read mode, reads its content, and returns the content as a string.

This function ensures that template files are loaded correctly, and if a template file is missing, the user is informed with a clear error message.

### Example Usage:
```python
template_content = self.load_template("example_template.txt")
```

In this example, the function loads the content of `example_template.txt` from the predefined directory and stores it in the `template_content` variable for further use.
***
### FunctionDef render_template(self, template_str, data)
**render_template**: The function of render_template is to render a template using string formatting.

**parameters**: The parameters of this Function.
· template_str: Template content as a string.  
· data: Dictionary of variables to replace in the template.  

**Code Description**: The render_template function is designed to take a string representation of a template and a dictionary of data, which contains key-value pairs that will be used to replace placeholders in the template. The function utilizes the Template class to create a template object from the provided template string. It then calls the render method on this template object, unpacking the data dictionary to replace the placeholders with the corresponding values. The result is a fully rendered string that incorporates the provided data.

This function is called by various methods within the project, specifically in the ReportBenchmark and ReportEvaluation classes. For instance, in the attempt method of the ReportBenchmark class, render_template is used to create a prompt for a chat interaction by loading a specific template and populating it with relevant data such as wiki_text and UserQuery. Similarly, in the run_factualqa method, it renders a template for FactualQA evaluation, incorporating user queries and ground truth data. The rendered output is then used to generate responses from a common chat function, which is a critical part of the application's functionality.

In the ReportEvaluation class, methods like examinees_outline_generation and evaluate_factualqa also leverage render_template to prepare prompts for generating outlines and evaluating factual questions, respectively. Each of these methods relies on the rendered output to facilitate interactions with the chat system, ensuring that the responses are contextually relevant and tailored to the specific queries being addressed.

**Note**: It is important to ensure that the data dictionary passed to the render_template function contains all necessary keys that correspond to placeholders in the template string. Failure to provide the correct keys may result in rendering errors or incomplete output.

**Output Example**: An example of the rendered output might look like this:

If the template_str is "Hello, {{ UserQuery }}! Here is your information: {{ wiki_text }}." and the data is {"UserQuery": "What is AI?", "wiki_text": "AI stands for Artificial Intelligence."}, the output would be:

"Hello, What is AI?! Here is your information: AI stands for Artificial Intelligence."
***
### FunctionDef common_chat(self, usr_prompt, tools)
**common_chat**: The function of common_chat is to facilitate a conversation with the model by sending user prompts and receiving responses.

**parameters**: The parameters of this Function.
· usr_prompt: A list containing the user prompt that is to be sent to the model for processing.
· tools: An optional parameter that can be set to None, which may be used to specify any tools that the model can utilize during the conversation.

**Code Description**: The common_chat function is designed to interact with a conversational model, taking a user prompt as input and returning a response in the form of a ChatCompletionMessage. This function is integral to the operation of various components within the project, as it serves as the primary means of communication with the model. It is invoked by several methods across different classes, such as attempt in ReportBenchmark, run_factualqa, examinees_outline_generation, evaluate_factualqa, and extract_student_tree_structure in the ReportEvaluation class, as well as update_answer and model_confident in the BaseAgent class.

In each of these instances, common_chat is called with a rendered prompt that is generated based on specific templates and user data. For example, in the attempt method, the function is called after loading and rendering a template for fact extraction, ensuring that the model receives a well-structured query. Similarly, in the run_factualqa method, the function is used to evaluate factual questions by passing a prompt that includes user queries and ground truth data.

The common_chat function is also utilized in the context of updating answers and checking model confidence, where it processes prompts that include previous answers and user feedback. This highlights its role in maintaining an ongoing dialogue with the model, allowing for iterative improvements based on user interactions and feedback.

**Note**: It is important to ensure that the usr_prompt parameter is properly formatted and contains relevant information for the model to generate an appropriate response. Additionally, while the tools parameter is optional, its inclusion may enhance the model's capabilities depending on the context of the conversation.
***
### FunctionDef common_chat(self, usr_prompt, tools)
**common_chat**: The function of common_chat is to facilitate a chat interaction by processing a user prompt and potentially utilizing additional tools.

**parameters**: The parameters of this Function.
· usr_prompt: A string representing the user's prompt that initiates the chat interaction.
· tools: A list of tools that may be used during the chat interaction.

**Code Description**: The common_chat function is designed to handle chat interactions within the BaseAgent class. It takes a user prompt (usr_prompt) as input, which is a string that contains the user's query or message. Additionally, it accepts a list of tools that can be employed during the chat process. The function is expected to return a ChatCompletionMessage, which encapsulates the response generated from the chat interaction.

This function plays a crucial role in various methods across the project, serving as a core component for generating responses based on user queries. For instance, in the ReportBenchmark class, the common_chat function is invoked in methods such as run_fact_extraction and run_factualqa. In these contexts, it processes prompts that are dynamically created from templates and user data, ensuring that the responses are contextually relevant and accurate.

Moreover, the common_chat function is also utilized in the ReportEvaluation class, specifically in methods like examinees_outline_generation and evaluate_factualqa. Here, it aids in generating outlines and evaluations based on student reports and user queries, demonstrating its versatility in handling different types of interactions.

In the context of the BaseAgent class, the common_chat function is called by other methods such as update_answer and model_confident. These methods leverage common_chat to obtain responses that are then used to update previous answers or assess the model's confidence in its responses.

Overall, the common_chat function serves as a foundational element in the communication framework of the project, enabling seamless interactions between users and the system while ensuring that the responses are generated based on the provided prompts and tools.

**Note**: It is important to ensure that the usr_prompt is well-formed and relevant to the context of the conversation to receive meaningful responses. Additionally, the tools parameter should be populated with appropriate tools that can enhance the chat interaction if needed.
***
### FunctionDef common_chat(self, usr_prompt, tools)
**common_chat**: The function of common_chat is to facilitate a conversation with the user by processing a given prompt and returning a response.

**parameters**: The parameters of this Function.
· usr_prompt: A string that contains the user's prompt or query that needs to be processed.
· tools: An optional parameter that can be set to None, which may be used to specify additional tools for processing the prompt.

**Code Description**: The common_chat function is designed to handle user interactions by taking a user prompt as input and generating a response. It is a core component of the BaseAgent class, which serves as a foundational element for various agents in the project. The function is invoked in multiple contexts throughout the project, primarily within methods that require interaction with the user or the processing of user queries.

For instance, in the ReportBenchmark class, the common_chat function is called within the run_fact_extraction and run_factualqa methods. In these cases, it processes a rendered template prompt that includes user queries and relevant data, returning a response that is expected to be in a specific format (e.g., JSON). If the response is not in the expected format or is empty, exceptions are raised to handle these scenarios appropriately.

Similarly, in the ReportEvaluation class, methods such as examinees_outline_generation and evaluate_factualqa also utilize common_chat to generate responses based on user queries. The responses from common_chat are critical for further processing and evaluation, as they often serve as input for subsequent logic or decision-making steps.

The function is also utilized in the update_answer and model_confident methods of the BaseAgent class, where it processes prompts related to updating answers based on user feedback and checking the model's confidence in its responses.

Overall, common_chat acts as a communication bridge between the user and the agent, ensuring that user queries are effectively processed and that the agents can respond appropriately based on the context provided.

**Note**: When using the common_chat function, it is essential to ensure that the usr_prompt is well-formed and that any expected tools are correctly specified if applicable. Proper error handling should be implemented to manage cases where the response does not meet the expected criteria.
***
### FunctionDef common_chat(self, usr_prompt, tools, role)
**common_chat**: The function of common_chat is to facilitate interaction with a language model by sending user prompts and managing the conversation history.

**parameters**: The parameters of this Function.
· usr_prompt: A string or list representing the user's prompt to the language model.
· tools: An optional list of tools that can be utilized during the interaction.
· role: A string indicating the role of the entity sending the message, defaulting to "assistant".

**Code Description**: The common_chat function is designed to interact with a language model by sending a user-defined prompt and processing the response. It first calls the call_llm function, which handles the communication with the language model API. This function takes the model specified in the settings, the user prompt, and any tools that may be needed for the interaction.

If tools are provided, the function returns the model's response directly without appending it to the conversation history. However, if no tools are specified, the response content is appended to the conversation history managed by the BaseAgent's conversation_manager, using the specified role (defaulting to "assistant"). The function ultimately returns the content of the model's response.

The common_chat function is called by various methods throughout the project, including:
- In the attempt method of the ReportBenchmark class, where it generates a prompt based on a template and user query, then retrieves a response from the language model.
- In the run_factualqa method, where it similarly generates a prompt for factual question answering and retrieves the model's response.
- In the examinees_outline_generation and evaluate_factualqa methods, where it generates prompts for outline generation and factual question evaluation, respectively.
- In the update_answer and model_confident methods, where it is used to update answers based on user queries and to check the model's confidence in its responses.
- In the search_and_browse method, where it interacts with tools for searching and browsing based on the rendered prompt.

This function plays a critical role in maintaining the flow of conversation and ensuring that responses from the language model are appropriately handled and recorded.

**Note**: It is important to ensure that the usr_prompt is well-formed and that the tools, if used, are compatible with the language model being called. The function's behavior may vary based on whether tools are provided or not, affecting how the response is processed and stored.

**Output Example**: A possible return value from the common_chat function could be a string such as "The capital of France is Paris." or a structured response from the language model, depending on the prompt and context provided.
***
### FunctionDef update_answer(self, query, previous_answer, search_results, critic_feedback)
**update_answer**: The function of update_answer is to update the agent's response based on a new query, previous answer, search results, and feedback from a critic.

**parameters**: The parameters of this Function.
· query: A string representing the new question or query that the agent needs to address.  
· previous_answer: A string containing the previous answer provided by the agent to the query.  
· search_results: A string or data structure that holds the results obtained from a search operation related to the query.  
· critic_feedback: A string containing feedback from a critic that may influence the update of the answer.

**Code Description**: The update_answer function is designed to refine the agent's response to a user query by incorporating new information and feedback. The function begins by organizing the input parameters into a dictionary named `data`, which includes the current query, the previous answer, the search results, and the critic's feedback. 

Next, the function calls the load_template method to retrieve a specific template file named "agent_update_answer.txt". This template is expected to contain a structured format for generating a prompt that will be sent to the conversational model. The retrieved template is then rendered using the render_template method, which replaces placeholders in the template with the actual values from the `data` dictionary. This step ensures that the prompt is contextually relevant and tailored to the current interaction.

After rendering the prompt, the function invokes the common_chat method, passing the rendered prompt as an argument. This method facilitates communication with the language model, sending the prompt and receiving a response. The response generated by the common_chat method is then returned as the output of the update_answer function.

The update_answer function is called within the main function of the project, specifically during the iterative process of refining answers based on user queries and feedback from a critic agent. In the main function, after the initial answer is generated, the update_answer function is invoked to incorporate the latest search results and feedback from the critic. This iterative approach allows the agent to improve its responses over multiple iterations, ensuring that the final answer is well-informed and aligned with user expectations.

**Note**: It is essential to ensure that the parameters passed to the update_answer function are valid and appropriately formatted. The function relies on the successful loading of the template and the proper functioning of the common_chat method to generate an accurate response.

**Output Example**: A possible return value from the update_answer function could be a string such as "Based on the latest search results and feedback, the updated answer is: [new answer]." This output reflects the agent's refined response after considering the provided inputs.
***
### FunctionDef model_confident(self, query)
**model_confident**: The function of model_confident is to check whether the model is confident in its response to the current user query.

**parameters**: The parameters of this Function.
· query: A string representing the user's question that needs to be evaluated for model confidence.

**Code Description**: The model_confident function is designed to assess the confidence level of the model regarding a specific user query. It begins by constructing a data dictionary that includes the user's question under the key "user_question". The function then loads a confidence assessment template from a file named "agent_confidence.txt" using the load_template method. This template serves as a structured prompt for the model to evaluate its confidence.

Next, the function renders the loaded template by passing the data dictionary to the render_template method, which replaces any placeholders in the template with the corresponding values from the dictionary. The rendered prompt is then sent to the model through the common_chat method, which facilitates the interaction with the model and retrieves the response.

The response obtained from common_chat is returned as the output of the model_confident function. This output indicates the model's confidence level regarding the provided query.

The model_confident function is called within the main function of the project, specifically during the first iteration of a loop that manages multiple interactions with the model. In this context, it is used to determine whether the model is confident enough to provide an answer directly or if further actions, such as searching for additional information, are necessary. If the model is deemed confident, the common_chat function is invoked to obtain the answer. Conversely, if the model lacks confidence, the process involves generating a search prompt and retrieving supplementary data before answering the user.

**Note**: It is essential to ensure that the query parameter passed to the model_confident function is well-formed and relevant to the context of the conversation to receive an accurate confidence assessment.

**Output Example**: A possible return value from the model_confident function could be a string indicating the model's confidence level, such as "true" or "false", depending on the evaluation of the user query.
***
### FunctionDef search_and_browse(self, rendered_prompt)
**search_and_browse**: The function of search_and_browse is to perform a search and web scraping operation based on a rendered prompt, returning the final results as a string.

**parameters**: The parameters of this Function.
· rendered_prompt: A string that contains the prompt to be processed for searching and browsing.

**Code Description**: The search_and_browse function is a method within the BaseAgent class that orchestrates a two-step process: searching for information using a search aggregator and then scraping content from the web based on the search results. 

1. The function begins by invoking the common_chat method with the provided rendered_prompt and the search_aggregator_schema. This interaction initiates a search operation, and the response is logged for debugging purposes.

2. If the search_with_tool_response indicates that no tool calls were made, the function immediately returns the content of the response. This allows for quick exit when no further action is necessary.

3. If tool calls are present, the function appends these calls to the conversation history using the append_tool_call_to_history method. This ensures that all interactions with tools are recorded for future reference.

4. The function then initializes an empty string to accumulate the final search results. It iterates over each tool call, extracting the query from the tool call's arguments. For each query, it calls the search method of the search_aggregator to perform the search asynchronously.

5. After a brief pause to manage rate limits, the results from each search are appended to the conversation history using append_tool_call_result_to_history, and the query is updated in the query database.

6. Once all search results are collected, the function loads a web scraper template and renders it with the user's question and the initial search results. This rendered prompt is then sent to the common_chat method to interact with the content scraper.

7. Similar to the search step, if the web_scraper_response contains no tool calls, the function returns the content directly. If tool calls are present, they are appended to the conversation history.

8. The function then processes each tool call related to web scraping, extracting URLs from the arguments and calling the scrape method of the content scraper to gather content from these URLs.

9. The results from the scraping operation are also logged into the conversation history, and the final results are concatenated into a single string, which is returned at the end of the function.

The search_and_browse function is called within the main function of the project, specifically when the agent is not confident in its initial answer and needs to gather additional information through searching and scraping. This highlights its role in enhancing the agent's ability to provide accurate and relevant responses based on real-time data.

**Note**: It is essential to ensure that the rendered_prompt is well-formed and contains relevant queries for both the search and scraping processes to function effectively. Additionally, proper error handling should be implemented to manage cases where the search or scraping operations do not yield results.

**Output Example**: A possible return value of the search_and_browse function could be a string formatted as follows:
```
"Here are the results from your search: 1. Title: Example Article, URL: http://example.com/article1, Content: This is a summary of the article. 2. Title: Another Example, URL: http://example.com/article2, Content: This is another summary."
```
***
### FunctionDef receive_task(self, task)
**receive_task**: The function of receive_task is to accept and store the original task provided to the agent.

**parameters**: The parameters of this Function.
· task: The original task that needs to be received and stored by the agent.

**Code Description**: The receive_task function is a method of the BaseAgent class, designed to receive a task as input and store it in the instance variable original_task. This function is crucial for the operation of the agent, as it allows the agent to keep track of the task it is currently handling. When the function is called, it takes the task parameter and assigns it to the instance variable self.original_task, effectively saving the task for future reference or processing.

In the context of the project, the receive_task function is invoked by the CriticAgent within the main function of the application. Specifically, after the common agent generates an answer to the user's question, the CriticAgent receives the original task (TASK) using the receive_task method. This step is essential for the CriticAgent to evaluate the performance of the common agent based on the task it was given. By storing the original task, the CriticAgent can provide feedback and suggestions for improvement, thereby enhancing the overall interaction and effectiveness of the agents involved in the task processing.

**Note**: It is important to ensure that the task passed to the receive_task function is well-defined and relevant to the agent's capabilities, as this will directly influence the quality of the agent's performance and the feedback provided by the CriticAgent.
***
### FunctionDef extract_and_validate_yaml(self, model_response)
**extract_and_validate_yaml**: The function of extract_and_validate_yaml is to extract YAML content from a string and validate it.

**parameters**: The parameters of this Function.
· model_response: A string containing the response from a model which may include YAML content wrapped in code block markers.

**Code Description**: 
The function `extract_and_validate_yaml` is designed to extract YAML data from a given string, `model_response`, and return it in a structured format if valid. It performs the following steps:

1. **Regular Expression Matching**: The function begins by using a regular expression to search for content between triple backticks ` ```yaml ` and ` ``` `, which is expected to be YAML content. The regular expression `r"```yaml\n([\s\S]*?)\n```"` is used to identify the YAML content enclosed within the code block. If no match is found, it returns `None`.

2. **YAML Parsing**: Once the YAML content is extracted, the function attempts to parse it using `yaml.safe_load`. This function safely loads the YAML content into a Python dictionary or data structure. If the content is not valid YAML, a `yaml.YAMLError` is caught and the error message is printed, returning `None`.

3. **Formatting and Returning**: If the YAML content is successfully parsed, it is re-serialized into a YAML formatted string using `yaml.dump`, and the result is returned. This output is presented in a human-readable YAML format, with the default flow style set to `False`.

In the context of the broader project, this function is typically used in situations where model responses or other content need to be processed for YAML data. For example, in the `critic` method of the `CriticAgent` class, this function is called to extract and validate YAML content from a model response. Similarly, in the `main` function, it is used to process agent confidence data in YAML format.

**Note**: It is important to ensure that the model response contains valid YAML content, as invalid or improperly formatted YAML will cause the function to return `None` and may trigger error handling in the calling code.

**Output Example**: 
Given a valid `model_response` such as:

```
```yaml
confidence: true
```
```

The function would return:

```
confidence: true
```
***
