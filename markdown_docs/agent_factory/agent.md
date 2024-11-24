## ClassDef BaseAgent
**BaseAgent**: The function of BaseAgent is to serve as a foundational class for managing queries, performing searches, and interacting with a language model.

**attributes**: The attributes of this Class.
· config: Configuration settings read from a configuration file.
· model: The model used for language processing, defaulting to "gpt-4o-mini".
· env: An instance of Environment for loading templates from the specified prompt folder.
· queryDB: A set to store unique queries.
· citationDB: A list of dictionaries that contains search queries and their corresponding results, specifically those praised by critics.
· sys_prompt: A system prompt used for guiding the language model's responses.
· repeat_turns: A parameter that defines the number of times a query can be repeated.
· history: A list that keeps track of the conversation history between the user and the assistant.

**Code Description**: The BaseAgent class is designed to facilitate the interaction between a user and a language model while managing search queries and results. Upon initialization, it reads configuration settings, sets up the model, and prepares the environment for template rendering. The class maintains a database of queries and citations, allowing it to store and retrieve relevant information efficiently.

The `search_query` method takes a query string as input, utilizes the SearchAggregator to perform a search, and returns a structured response containing the query, response time, and search results. The `parallel_search` method allows for concurrent execution of multiple search queries, collecting results as they complete. The `format_parallel_search_to_string` method formats the results of parallel searches into a readable string format.

The `common_chat` method interacts with the language model using a user-provided query and stores the conversation history. The `clear_history` method resets the conversation history. The `update_answer` method refines previous answers based on new search results and feedback. The `model_confident` method checks the model's confidence in its response to a given query, while `initialize_search` prepares the model for a search task.

The `chat_with_template` method renders a prompt template with provided data and initiates a chat with the language model. The `receive_task` method captures the original task for processing. Finally, the `extract_and_validate_yaml` method extracts YAML content from a model response, validating its structure and returning it in a safe format.

**Note**: It is essential to ensure that the configuration file is correctly set up and that the necessary templates are available in the specified prompt folder for the class to function properly. Additionally, error handling is implemented in the parallel search method to manage exceptions that may arise during query execution.

**Output Example**: A possible return value from the `search_query` method could look like this:
{
    "query": "Why do we say Google was facing challenges in 2019?",
    "response_time": "0.45 seconds",
    "results": [
        {
            "title": "Google's Challenges in 2019",
            "url": "https://example.com/google-challenges-2019",
            "content": "In 2019, Google faced several challenges including regulatory scrutiny and competition."
        },
        {
            "title": "The Year Google Struggled",
            "url": "https://example.com/year-google-struggled",
            "content": "Various factors contributed to Google's struggles in 2019, including..."
        }
    ]
}
### FunctionDef __init__(self)
**__init__**: The function of __init__ is to initialize an instance of the BaseAgent class, setting up its configuration and necessary attributes.

**parameters**: The parameters of this Function.
· There are no parameters for this function.

**Code Description**: The __init__ function is a constructor for the BaseAgent class. It is responsible for initializing the instance variables that will be used throughout the class. 

1. **self.config**: This variable is assigned the result of the `read_config()` function, which presumably reads configuration settings from a file or other source. This configuration is essential for the operation of the agent, as it dictates how the agent will behave.

2. **self.model**: This variable retrieves the 'default_model' value from the configuration dictionary. If this key does not exist, it defaults to "gpt-4o-mini". This model will likely be used for generating responses or processing queries.

3. **self.env**: This variable creates an instance of the Environment class, using FileSystemLoader to load templates from a directory specified by the 'prompt_folder_path' key in the configuration. This setup suggests that the agent may utilize templates for generating prompts or responses.

4. **self.queryDB**: This is initialized as an empty set. It is intended to store unique queries that the agent will handle. Using a set ensures that each query is distinct and prevents duplicates.

5. **self.citationDB**: This variable is initialized as a list containing a single dictionary. The dictionary is structured to hold queries as keys, with each key mapping to a document_id that contains metadata about the document, such as its URL, title, and content. The comment indicates that only search results praised by critics will be included in this database.

6. **self.sys_prompt**: This is initialized as an empty string. It likely serves as a system prompt that can be modified or set later in the class's methods.

7. **self.repeat_turns**: This variable is set to 10, which may represent the number of times the agent will repeat a certain action or query during its operation.

8. **self.history**: This is initialized as an empty list. It is intended to keep track of the history of interactions or queries processed by the agent.

**Note**: It is important to ensure that the configuration file is correctly set up and accessible, as the agent's behavior heavily relies on the parameters defined within it. Additionally, the structure of the citationDB should be maintained to ensure proper retrieval and storage of search results.
***
### FunctionDef search_query(self, query)
**search_query**: The function of search_query is to perform a search operation based on a given query and return structured results.

**parameters**: The parameters of this Function.
· query: A string representing the search term that needs to be queried.

**Code Description**: The search_query function is designed to facilitate the process of searching for information based on a specified query. Upon invocation, it initializes an instance of the SearchAggregator class, which is responsible for handling the search operation. The function then calls the search method of the aggregator, passing the query as an argument. This method returns a response that contains various details about the search results.

The function extracts relevant information from the response, specifically the title, URL, and content of each result. It constructs a list of dictionaries, where each dictionary corresponds to an individual search result. Each dictionary contains three keys: "title", "url", and "content", which hold the respective values retrieved from the response.

Finally, the search_query function returns a structured dictionary that includes the original query, the response time from the search operation, and the list of results. This structured output allows for easy access to the search results and their associated metadata.

The search_query function is called by the parallel_search function, which simulates a parallel search for multiple queries. In this context, parallel_search utilizes the search_query function to handle each individual query concurrently. This relationship enhances the efficiency of the search process, allowing multiple queries to be processed simultaneously and their results to be aggregated.

**Note**: It is important to ensure that the query passed to the search_query function is properly formatted and relevant to the search context. Additionally, the function assumes that the SearchAggregator class is correctly implemented and capable of handling the search requests as expected.

**Output Example**: A possible appearance of the code's return value could be as follows:
{
    "query": "example search",
    "response_time": 120,
    "results": [
        {
            "title": "Example Title 1",
            "url": "http://example.com/1",
            "content": "This is an example content for the first result."
        },
        {
            "title": "Example Title 2",
            "url": "http://example.com/2",
            "content": "This is an example content for the second result."
        }
    ]
}
***
### FunctionDef parallel_search(self, queries)
**parallel_search**: The function of parallel_search is to perform concurrent searches for multiple queries and return their results.

**parameters**: The parameters of this Function.
· queries: A list of strings, where each string represents a search term that needs to be queried.

**Code Description**: The parallel_search function is designed to enhance the efficiency of searching by executing multiple search queries concurrently. It utilizes the ThreadPoolExecutor from the concurrent.futures module to manage a pool of threads, allowing for simultaneous execution of the search_query function for each query in the provided list.

Upon invocation, the function creates an instance of ThreadPoolExecutor, which is responsible for managing the threads. It then submits each query to the executor using the search_query method, creating a mapping of futures to their corresponding queries. This mapping allows the function to track which future corresponds to which query.

As the futures complete, the function iterates over them using the as_completed method. For each completed future, it retrieves the associated query and attempts to obtain the result. If the search_query function executes successfully, the result is appended to the results list. In the event of an exception during the execution of a query, an error message is printed, indicating which query generated the exception and the nature of the error.

Finally, the function returns a list of results, where each result corresponds to the output of the search_query function for each query. This design allows for efficient handling of multiple search requests, significantly reducing the total time required to process all queries compared to executing them sequentially.

The parallel_search function directly relies on the search_query function to perform the actual search operation for each individual query. This relationship allows for a modular approach, where the parallel_search function orchestrates the concurrent execution while delegating the specific search logic to the search_query function.

**Note**: It is important to ensure that the queries passed to the parallel_search function are properly formatted and relevant to the search context. Additionally, the function assumes that the search_query function is implemented correctly and can handle the search requests as expected.

**Output Example**: A possible appearance of the code's return value could be as follows:
[
    {
        "query": "example search 1",
        "response_time": 100,
        "results": [
            {
                "title": "Example Title 1",
                "url": "http://example.com/1",
                "content": "This is an example content for the first result."
            }
        ]
    },
    {
        "query": "example search 2",
        "response_time": 150,
        "results": [
            {
                "title": "Example Title 2",
                "url": "http://example.com/2",
                "content": "This is an example content for the second result."
            }
        ]
    }
]
***
### FunctionDef format_parallel_search_to_string(self, data_list)
**format_parallel_search_to_string**: The function of format_parallel_search_to_string is to format a list of search queries and their corresponding results into a structured string representation.

**parameters**: The parameters of this Function.
· data_list: A list of dictionaries, where each dictionary contains a search query and its associated results.

**Code Description**: The format_parallel_search_to_string function takes a list of dictionaries as input, where each dictionary represents a search query and its results. The function initializes an empty list called `result` to store the formatted strings. It then iterates over each item in the `data_list`. For each item, it retrieves the "query" and "results" fields. The query is added to the result list, followed by a header for the search results. The function then iterates over the results, enumerating them to provide a numbered list. Each result is formatted to include the title, URL, and content, with separators for clarity. After processing all results for a query, an additional newline is appended to separate different queries. Finally, the function joins all elements in the `result` list into a single string, which is returned as the output.

**Note**: It is important to ensure that each item in the data_list contains the expected keys ("query" and "results") to avoid KeyError exceptions. The results should be structured as dictionaries containing "title", "url", and "content" keys.

**Output Example**: 
```
Query: How to learn Python?
Search Results:
--------------------------------------------------
[1]:
TITLE: Python for Beginners
URL: https://example.com/python-beginners
CONTENT: A comprehensive guide to start learning Python.
--------------------------------------------------

[2]:
TITLE: Advanced Python Techniques
URL: https://example.com/advanced-python
CONTENT: Explore advanced concepts in Python programming.
--------------------------------------------------
```
***
### FunctionDef common_chat(self, query)
**common_chat**: The function of common_chat is to facilitate interaction with a language model by sending a user query and storing the conversation history.

**parameters**: The parameters of this Function.
· query: A string representing the user's input or question that will be sent to the language model.

**Code Description**: The common_chat method is designed to handle user interactions with a language model. It takes a single parameter, `query`, which is the input from the user. The method begins by invoking the `call_llm` function, passing the model, system prompt, user prompt (the query), and configuration settings. This function is responsible for communicating with the language model and retrieving a response based on the provided inputs.

Once the response from the language model is obtained, the method updates the conversation history by appending two entries: one for the user's query and another for the assistant's response. This history is stored in the `self.history` list, which allows for tracking the dialogue over time.

The common_chat function is called by the chat_with_template method, which serves as a preparatory step for generating a dynamic prompt based on input data. In chat_with_template, the prompt is rendered using a template and the relevant data, resulting in a `rendered_prompt`. This rendered prompt is then passed to common_chat as the query parameter. The response from common_chat is returned as the output of chat_with_template, establishing a clear functional relationship between the two methods.

This design allows for a structured conversation flow, where chat_with_template formats the input into a suitable prompt, and common_chat processes this prompt to obtain a response from the language model, while also maintaining a history of the interaction.

**Note**: It is important to ensure that the query passed to common_chat is well-formed and relevant to the context of the conversation. This will enhance the quality of the response generated by the language model.

**Output Example**: A possible return value from the common_chat function could be a string such as "I'm here to help! What do you need assistance with?" This response will depend on the specific query provided and the context established in the conversation history.
***
### FunctionDef clear_history(self)
**clear_history**: The function of clear_history is to reset the history of the agent by clearing all stored entries.

**parameters**: The clear_history function does not take any parameters.

**Code Description**: The clear_history function is a method defined within the BaseAgent class. When invoked, it sets the instance variable `history` to an empty list. This effectively removes all previous entries stored in the `history`, allowing the agent to start fresh without any prior context or data. This function is particularly useful in scenarios where the agent needs to discard past interactions or data, ensuring that it operates without any influence from previous states. The simplicity of this function underscores its importance in maintaining the integrity of the agent's operational state.

**Note**: It is important to use the clear_history function judiciously, as invoking it will permanently erase all historical data associated with the agent. This action cannot be undone, so it should be called only when it is certain that the historical data is no longer needed.
***
### FunctionDef update_answer(self, query, previous_answer, search_results, critic_feedback)
**update_answer**: The function of update_answer is to generate an updated response based on user input, previous answers, search results, and feedback from a critic.

**parameters**: The parameters of this Function.
· query: A string representing the user's current question or request for information.
· previous_answer: A string containing the answer provided to the user prior to the current query.
· search_results: A list or collection of results obtained from a search operation relevant to the query.
· critic_feedback: A string that includes feedback or critiques provided by a critic regarding the previous answer.

**Code Description**: The update_answer method is designed to facilitate the process of refining and updating an answer based on new input and feedback. It takes four parameters: `query`, `previous_answer`, `search_results`, and `critic_feedback`, which collectively provide the context needed to generate a more accurate and relevant response.

Within the method, a dictionary named `data` is constructed, which organizes the input parameters into key-value pairs. This dictionary serves as the foundation for generating a prompt that will be used in a chat interaction. The method then calls the `chat_with_template` function, passing the `data` dictionary along with a specific template for updating answers, which is retrieved using `self.env.get_template('agent_update_answer.txt')`.

The `chat_with_template` function is responsible for rendering the prompt template with the provided data and subsequently querying a language model to obtain a response. This interaction is crucial as it transforms the structured input data into a conversational format that the language model can process. The response generated by the language model is then returned as the `updated_answer`.

This design establishes a clear functional relationship where `update_answer` acts as a preparatory step that gathers and organizes input data, while `chat_with_template` processes this data to generate a coherent and contextually relevant response. The interaction ensures that the updated answer reflects the latest user query, previous context, search results, and feedback, thereby enhancing the overall quality of the response provided to the user.

**Note**: It is important to ensure that the input parameters are accurately populated and relevant to the context of the conversation. This will guarantee that the generated prompt is meaningful and leads to a more effective interaction with the language model.

**Output Example**: A possible return value from the update_answer function could be a string such as "Based on your previous feedback and the latest search results, here is the updated answer: [updated content]." This response will depend on the specific data provided and the context established in the conversation.
***
### FunctionDef model_confident(self, query)
**model_confident**: The function of model_confident is to check whether the model is confident in responding to the current query.

**parameters**: The parameters of this Function.
· query: A string representing the user's question or inquiry that needs to be evaluated for model confidence.

**Code Description**: The model_confident method is designed to assess the confidence level of the model in relation to a specific user query. It begins by constructing a data dictionary that includes the user's question under the key "user_question". This dictionary is then passed to the chat_with_template method, along with a template for generating a response, which is retrieved using the env.get_template method with the template name 'agent_confidence.txt'.

The chat_with_template method is responsible for rendering the prompt template with the provided data. It utilizes the render method of the template to create a coherent query that the language model can understand. The rendered prompt is subsequently sent to the common_chat method, which interacts with the language model to obtain a response. The response generated by the language model is then returned by the model_confident method.

This function is part of a broader architecture within the BaseAgent class, where it serves to facilitate interactions with the language model by determining the model's confidence in addressing specific queries. The model_confident method can be called in various contexts where understanding the model's confidence is crucial for decision-making or user interaction.

**Note**: It is essential to ensure that the query parameter accurately reflects the user's intent to enable the model to provide a meaningful and relevant confidence assessment.

**Output Example**: A possible return value from the model_confident function could be a string such as "The model is confident in answering your question: [response content]." The actual output will depend on the specific query and the corresponding template used in the interaction.
***
### FunctionDef initialize_search(self, query)
**initialize_search**: The function of initialize_search is to initiate a search process based on a user-provided query.

**parameters**: The parameters of this Function.
· query: A string representing the user's question or search query that will be processed to generate a response.

**Code Description**: The initialize_search method is designed to start a search operation by taking a user query as input. It constructs a data dictionary that includes the user's question under the key "user_question". This data dictionary is then passed to the chat_with_template method along with a specific prompt template, which is retrieved using the env.get_template method with the filename 'planner_agent_initial_search_plan.txt'.

The chat_with_template method is responsible for rendering the prompt template with the provided data and querying a language model to obtain a response. It prepares the input by substituting placeholders in the template with actual values from the data dictionary, creating a coherent query that the language model can understand. The rendered prompt is then sent to the common_chat method, which handles the interaction with the language model and returns the generated response.

The initialize_search method serves as a caller for chat_with_template, facilitating the interaction between the user’s query and the language model through a structured prompt. This modular approach allows for the reuse of the chat_with_template functionality across different methods within the BaseAgent class, ensuring consistency in how queries are processed and responses are generated.

**Note**: It is important to ensure that the query parameter is well-structured and relevant to the search context, as this will significantly influence the quality and relevance of the response generated by the language model.

**Output Example**: A possible return value from the initialize_search function could be a string such as "Based on your question, here is the initial search plan: [response content]." The actual output will depend on the specific query and the prompt template used in the interaction.
***
### FunctionDef chat_with_template(self, data, prompt_template)
**chat_with_template**: The function of chat_with_template is to facilitate a dynamic chat interaction by rendering a prompt template with provided data and querying a language model.

**parameters**: The parameters of this Function.
· data: A dictionary containing key-value pairs that will be used to populate the prompt template.
· prompt_template: A template object that defines the structure of the prompt to be rendered.

**Code Description**: The chat_with_template method is designed to create a conversational prompt based on the input data provided in the form of a dictionary. It utilizes a prompt template to format this data into a coherent query that can be understood by a language model. The method begins by rendering the prompt template with the data using the `render` method, which substitutes the placeholders in the template with actual values from the data dictionary. The resulting string, referred to as `rendered_prompt`, is then passed to the common_chat method as the query parameter.

The common_chat method is responsible for sending this rendered prompt to the language model and managing the conversation history. It takes the rendered prompt and communicates with the language model to obtain a response, which is then returned to the caller of chat_with_template. This establishes a clear functional relationship where chat_with_template prepares the input for the language model, while common_chat handles the interaction and response retrieval.

The chat_with_template function is called by other methods within the BaseAgent class, such as update_answer, model_confident, and initialize_search. Each of these methods prepares specific data relevant to their context and invokes chat_with_template to generate a response based on that data. For instance, in update_answer, the method constructs a data dictionary that includes the user's current query, previous answers, search results, and feedback, and then calls chat_with_template with this data and a corresponding template for updating answers. Similarly, model_confident and initialize_search also prepare their respective data and templates before invoking chat_with_template.

This design allows for a modular and reusable approach to generating prompts and interacting with the language model, ensuring that various components of the agent can leverage the same underlying functionality for chat interactions.

**Note**: It is crucial to ensure that the data dictionary accurately reflects the necessary context for the prompt template to generate meaningful and relevant queries. Properly structured input will enhance the quality of the responses generated by the language model.

**Output Example**: A possible return value from the chat_with_template function could be a string such as "Based on the information provided, here is the response to your query: [response content]." The actual output will depend on the specific data and prompt template used in the interaction.
***
### FunctionDef receive_task(self, task)
**receive_task**: The function of receive_task is to accept and store the original task provided to the agent.

**parameters**: The parameters of this Function.
· task: This parameter represents the original task that is being received by the agent. It is expected to be of any data type that encapsulates the task details.

**Code Description**: The receive_task function is designed to accept a task as input and assign it to the instance variable original_task. This function serves as a method for the BaseAgent class, allowing it to receive tasks that it will process or manage later. When the function is called, it takes the provided task and directly assigns it to the instance variable self.original_task. This action effectively stores the task within the agent's context, making it accessible for further operations or processing within the agent's lifecycle.

**Note**: It is important to ensure that the task being passed to this function is properly formatted and contains all necessary information required for the agent to perform its intended operations. Additionally, this function does not perform any validation or processing on the task; it simply stores it. Therefore, any necessary checks or transformations should be handled before invoking this method.
***
### FunctionDef extract_and_validate_yaml(self, model_response)
**extract_and_validate_yaml**: The function of extract_and_validate_yaml is to extract YAML content from a given string and validate its syntax.

**parameters**: The parameters of this Function.
· model_response: A string containing the model response that may include YAML content wrapped in ```yaml``` tags.

**Code Description**: The extract_and_validate_yaml function begins by importing the regular expression module, `re`. It then uses a regular expression to search for content enclosed between ```yaml``` tags within the provided `model_response` string. The pattern `r'```yaml\n([\s\S]*?)\n```'` is used to match any characters (including newlines) that appear between the opening and closing YAML tags. If no match is found, the function returns `None`, indicating that there is no valid YAML content present.

If a match is found, the function retrieves the matched content, strips any leading or trailing whitespace, and attempts to parse it as YAML using `yaml.safe_load()`. This method is designed to safely parse YAML content, preventing the execution of arbitrary code. If the parsing is successful, the function returns the YAML content formatted as a string using `yaml.dump()`, which converts the parsed YAML back into a string representation with a default flow style of `False`.

In the event of a parsing error, the function catches the `yaml.YAMLError` exception, prints an error message indicating that the YAML content is invalid, and returns `None`.

**Note**: It is important to ensure that the input string contains properly formatted YAML content within the specified tags. If the YAML is malformed or if the tags are missing, the function will not return a valid output.

**Output Example**: If the input `model_response` is:
```
Here is some configuration:
```yaml
key1: value1
key2:
  - item1
  - item2
```
```
The function would return:
```
key1: value1
key2:
- item1
- item2
```
***
