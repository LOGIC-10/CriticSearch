## ClassDef BaseAgent
**BaseAgent**: The function of BaseAgent is to serve as a foundational class for intelligent agents, providing essential functionalities for managing conversations, handling templates, and integrating various tools for search and content scraping.

**attributes**: The attributes of this Class.
· queryDB: A set to store queries made by the agent, ensuring uniqueness and facilitating tracking of search queries.  
· tool_registry: An instance of ToolRegistry that manages the schemas for tools used by the agent.  
· user_question: A string that holds the current question posed by the user.  
· conversation_manager: An instance of ConversationManager responsible for managing the conversation history.  
· citationDB: A list of dictionaries that stores search queries and their corresponding results, specifically those praised by critics.  
· search_aggregator: An instance of SearchAggregator that aggregates search results from various sources.  
· search_aggregator_schema: A schema for the search aggregator tool, retrieved or created from the tool registry.  
· content_scraper: An instance of ContentScraper that extracts content from web pages.  
· content_scraper_schema: A schema for the content scraper tool, retrieved or created from the tool registry.  
· repeat_turns: An integer that indicates the number of times the agent should repeat its search or response process.

**Code Description**: The BaseAgent class is designed to facilitate the operation of intelligent agents by providing a structured approach to managing user interactions and integrating various tools for enhanced functionality. Upon initialization, the class sets up its environment by determining the directory of the current script and establishing paths for template files. It initializes several key components, including a conversation manager to track the history of interactions, a tool registry to manage schemas for tools, and a citation database to store relevant search results.

The class includes methods for loading and rendering templates, which are essential for generating dynamic responses based on user input. The `chat_with_template` and `chat_with_tools` methods allow the agent to interact with users and tools by rendering prompts and managing the conversation flow. The `common_chat` method serves as a core function that handles communication with the language model, allowing for flexible interactions based on user prompts and available tools.

Additionally, the BaseAgent class provides methods for updating answers based on user feedback, checking the model's confidence in its responses, and scraping web content from search results. The `search_and_browse` method integrates search functionality with web scraping, enabling the agent to gather and process information effectively.

The BaseAgent is utilized by other classes, such as CriticAgent, which extends its capabilities to focus on generating critiques of responses. The CriticAgent leverages the functionalities provided by BaseAgent to manage conversations and interact with the language model, demonstrating the foundational role of BaseAgent in the overall architecture of the project.

**Note**: It is important to ensure that the templates used for rendering responses are correctly formatted and accessible, as the BaseAgent relies on these templates for generating dynamic content. Additionally, proper management of the conversation history and tool schemas is crucial for maintaining the integrity and efficiency of the agent's operations.

**Output Example**: A possible appearance of the code's return value when rendering a template might look like this:
```json
{
  "response": "Based on the search results, Google faced several challenges in 2019, including increased competition and regulatory scrutiny."
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
**load_template**: The function of load_template is to load a template file from the prompts directory.

**parameters**: The parameters of this Function.
· filename: The name of the template file to load.

**Code Description**: The load_template function is designed to retrieve the content of a specified template file from a predefined directory, referred to as prompts_dir. The function takes a single parameter, filename, which represents the name of the template file to be loaded.

The function constructs the full file path by joining the prompts_dir with the provided filename using the os.path.join method. It then checks if the constructed file path exists using os.path.exists. If the file does not exist, a FileNotFoundError is raised, providing a clear error message indicating that the specified template file could not be found in the prompts directory.

If the file exists, the function proceeds to open the file in read mode with UTF-8 encoding. It reads the content of the file and returns it as a string. This functionality is essential for the BaseAgent class, as it allows the agent to dynamically load templates that are used for generating prompts and responses in various interactions.

The load_template function is called by several other methods within the BaseAgent class, including chat_with_template, chat_with_tools, and update_answer. These methods rely on load_template to fetch the appropriate template files needed for rendering prompts based on user queries and other contextual data. For example, in the chat_with_template method, load_template is used to retrieve the template specified by template_name, which is then rendered with the provided template_data to create a prompt for the chat model.

**Note**: It is crucial to ensure that the filename passed to the load_template function corresponds to an existing template file in the prompts directory. Failure to do so will result in a FileNotFoundError, which will halt the execution of the calling function until the issue is resolved.

**Output Example**: A possible return value from the load_template function could be a string containing the content of the template file, such as:
```
"Hello, {{ user_name }}! How can I assist you today?"
```
***
### FunctionDef render_template(self, template_str, data)
**render_template**: The function of render_template is to render a template using string formatting.

**parameters**: The parameters of this Function.
· template_str: Template content as a string.  
· data: Dictionary of variables to replace in the template.  

**Code Description**: The render_template function is designed to take a template string and a dictionary of data, and then produce a formatted string by replacing placeholders in the template with corresponding values from the data dictionary. It utilizes the Template class to create a template object from the provided template string. The method then calls the render function on this template object, unpacking the data dictionary to replace the placeholders with actual values.

This function is called by several other methods within the BaseAgent class, including chat_with_template, chat_with_tools, and update_answer. Each of these methods relies on render_template to generate a prompt that is sent to a conversational model. For instance, in chat_with_template, the method first loads a template based on the template_name provided, then uses render_template to format this template with the provided template_data before passing the rendered prompt to the common_chat method for interaction with the model. Similarly, chat_with_tools and update_answer also use render_template to prepare prompts that incorporate dynamic data, ensuring that the responses generated by the model are contextually relevant and tailored to the specific interaction.

The render_template function is crucial for maintaining the flexibility and adaptability of the agent's responses, allowing it to generate contextually appropriate prompts based on varying inputs.

**Note**: It is essential to ensure that the template_str provided is correctly formatted and that the data dictionary contains all necessary keys corresponding to the placeholders in the template. Failure to do so may result in runtime errors during the rendering process.

**Output Example**: A possible return value from the render_template function could be a string such as "Hello, John! Your balance is $100." if the template_str was "Hello, {name}! Your balance is ${balance}." and the data dictionary was {"name": "John", "balance": 100}.
***
### FunctionDef chat_with_template(self, template_name, template_data, model)
**chat_with_template**: The function of chat_with_template is to provide a unified method for rendering templates and facilitating chat interactions with a conversational model.

**parameters**: The parameters of this Function.
· template_name: The name of the template file to be used for rendering the prompt.  
· template_data: A dictionary containing the data that will be used to populate the template.  
· model: An optional parameter that allows for overriding the default model used for the chat interaction.

**Code Description**: The chat_with_template function is a method within the BaseAgent class that serves as a comprehensive utility for managing interactions with a conversational model through template rendering. This function first loads a specified template file using the load_template method, which retrieves the content of the template from a predefined directory. The template_name parameter is passed to load_template to identify the correct file.

Once the template is loaded, the function utilizes the render_template method to format the template content by replacing placeholders with actual values from the template_data dictionary. This step is crucial as it ensures that the prompt sent to the conversational model is contextually relevant and tailored to the user's input.

After rendering the prompt, chat_with_template calls the common_chat method, passing the rendered prompt along with the specified model (or the default model if none is provided). The common_chat method is responsible for sending the prompt to the conversational model and retrieving the generated response.

The chat_with_template function is invoked in various contexts within the project, such as in the process_single_task function, where it is used to assess the confidence of the agent and to generate responses based on user queries. For example, it is called to create prompts for evaluating the agent's confidence level and for generating direct responses to user tasks. Additionally, it is utilized in the ReportVerifier class to verify questions against factual data, demonstrating its versatility and importance in ensuring accurate and context-aware interactions with the conversational model.

**Note**: It is essential to ensure that the template_name provided corresponds to an existing template file in the prompts directory, and that the template_data dictionary contains all necessary keys for rendering. Failure to do so may result in errors during the template loading or rendering process.

**Output Example**: A possible return value from the chat_with_template function could be a string such as:
```
"Hello, John! How can I assist you today?"
```
***
### FunctionDef chat_with_tools(self, template_name, template_data, tools, model)
### `chat_with_tools` Method Documentation

#### Description
The `chat_with_tools` method is a helper function within the `BaseAgent` class designed to facilitate communication with external tools during a conversation. This method is responsible for loading a template, rendering it with the provided data, and initiating a chat with specified tools using the rendered prompt. It abstracts the process of preparing a prompt from a template and interacting with the tools in a standardized manner.

#### Parameters
- **template_name** (`str`): The name of the template file to be loaded. This template defines the structure of the prompt to be used in the conversation.
- **template_data** (`dict`): A dictionary containing the data that will be used to render the template. The dictionary's keys correspond to placeholders in the template, and the values are inserted into the template during the rendering process.
- **tools** (`List`): A list of tools that will be used in the chat interaction. These tools may include models, external APIs, or other utilities that assist in processing the conversation.
- **model** (`str`, optional): The model to be used for the chat interaction. If not provided, the method will default to using the model specified in the application's settings.

#### Return Type
- **ChatCompletionMessage**: The method returns a `ChatCompletionMessage` object that represents the result of the chat interaction. This message encapsulates the response from the tools based on the rendered prompt.

#### Functionality Overview
1. **Template Loading**: The method first loads the specified template using the `load_template` function. This function retrieves the content of the template file from a predefined directory.
2. **Template Rendering**: After loading the template, it is rendered with the provided `template_data` using the `render_template` function. This process replaces placeholders in the template with actual data from the `template_data` dictionary.
3. **Chat Interaction**: Finally, the rendered prompt is passed to the `common_chat` method along with the provided tools and model. The `common_chat` method handles the interaction with the tools, generating the response based on the prompt.

#### Usage Example
```python
response = agent.chat_with_tools(
    template_name="user_query_template.txt",
    template_data={"user_name": "John", "query": "What is the weather like today?"},
    tools=[weather_tool],
    model="gpt-4"
)
```

#### Related Functions
- **`load_template`**: Loads a template file based on the `template_name` provided.
- **`render_template`**: Renders the template with the provided data, substituting placeholders with actual values.
- **`common_chat`**: Handles the chat interaction with the specified tools and model, using the rendered prompt.

#### Notes
- Ensure that the template file specified in `template_name` exists in the appropriate directory, as the method will raise an error if the file cannot be found.
- If no model is specified, the method will default to the model set in the application's settings.
***
### FunctionDef common_chat(self, usr_prompt, tools)
**common_chat**: The function of common_chat is to facilitate communication with a conversational model by sending a user prompt and optionally utilizing specific tools.

**parameters**: The parameters of this Function.
· usr_prompt: A list containing the prompt or message that the user wants to send to the conversational model.  
· tools: An optional parameter that can be set to None or a list of tools that may be used during the chat interaction.

**Code Description**: The common_chat function is a method within the BaseAgent class designed to interact with a conversational model, processing user prompts and potentially utilizing additional tools to enhance the interaction. This function takes in a user prompt, which is expected to be a list, and an optional tools parameter that can specify any tools to be employed during the chat.

The common_chat function is invoked by several other methods within the BaseAgent class, showcasing its central role in the communication process. For instance, the chat_with_template method utilizes common_chat to send a rendered prompt generated from a specified template and associated data. Similarly, the chat_with_tools method also calls common_chat, passing a rendered prompt along with a list of tools to facilitate a more enriched interaction.

In the context of the update_answer function, common_chat is called to refine the agent's response based on new information and feedback. This highlights the function's importance in ensuring that the agent's replies are not only relevant but also informed by the latest data and user interactions.

The model_confident function also relies on common_chat to assess the confidence level of the model regarding a specific user query. By sending a rendered prompt that includes the user's question, common_chat helps determine whether the model is confident enough to provide a direct answer or if further actions are necessary.

Furthermore, the web_scrape_results function employs common_chat to interact with a web scraper, sending a prompt that includes the user's question and initial search results. This demonstrates the versatility of common_chat in handling various types of interactions, from general conversation to specific tasks like web scraping.

Overall, common_chat serves as a fundamental method within the BaseAgent class, enabling seamless communication with the conversational model and supporting various functionalities that enhance the agent's capabilities.

**Note**: It is essential to ensure that the usr_prompt parameter is well-formed and relevant to the context of the conversation. Additionally, the tools parameter should be appropriately defined if used, as it can influence the interaction with the model.
***
### FunctionDef common_chat(self, usr_prompt, tools)
**common_chat**: The function of common_chat is to facilitate communication with a chat model by sending a user prompt and receiving a response.

**parameters**: The parameters of this Function.
· usr_prompt: A string representing the prompt or message from the user that is to be sent to the chat model.  
· tools: A list of tools that may be utilized during the chat interaction, which can enhance the model's response capabilities.

**Code Description**: The common_chat function is a core method within the BaseAgent class that serves as an interface for interacting with a chat model. It takes two parameters: `usr_prompt`, which is the input message from the user, and `tools`, which is an optional list of tools that can be employed to assist in generating a more informed response.

The function is designed to send the user prompt to the chat model and retrieve a response, encapsulating the interaction logic necessary for effective communication. This function is pivotal in various methods throughout the BaseAgent class, where it is invoked to handle user queries and generate responses based on templates and rendered prompts.

For instance, the common_chat function is called within the chat_with_template method, where it receives a rendered prompt created from a specific template and associated data. This allows the agent to provide contextually relevant responses based on user input. Similarly, in the chat_with_tools method, common_chat is utilized to send a rendered prompt along with a list of tools, enabling the agent to leverage additional functionalities during the chat interaction.

Moreover, the common_chat function is also employed in other methods such as update_answer, model_confident, web_scrape_results, and search_and_browse, demonstrating its versatility and central role in the agent's operations. Each of these methods relies on common_chat to communicate with the chat model, ensuring that the agent can effectively process user queries, update responses based on new information, and interact with external tools.

**Note**: It is essential to ensure that the `usr_prompt` parameter is well-formed and relevant to the context of the conversation. Additionally, the `tools` parameter should be appropriately populated with valid tools to enhance the response generation process when applicable. Proper error handling should also be implemented to manage cases where the chat model does not return a valid response.
***
### FunctionDef common_chat(self, usr_prompt, tools)
**common_chat**: The function of common_chat is to facilitate communication with a conversational model by sending a user prompt and receiving a response.

**parameters**: The parameters of this Function.
· usr_prompt: A string that represents the prompt or question provided by the user to the conversational model.  
· tools: An optional parameter that can be used to specify any tools that may be required for the chat interaction. The default value is None.

**Code Description**: The common_chat function is a method within the BaseAgent class that serves as a core component for interacting with a conversational model. This function takes a user-defined prompt (usr_prompt) and an optional tools parameter to facilitate the communication process. The primary role of common_chat is to send the rendered prompt to the model and retrieve the generated response.

This function is called by several other methods within the BaseAgent class, including chat_with_template, chat_with_tools, update_answer, model_confident, web_scrape_results, and search_and_browse. Each of these methods utilizes common_chat to handle the interaction with the conversational model, ensuring that the prompts generated from various contexts are processed consistently.

For instance, in the chat_with_template method, common_chat is invoked after rendering a template with specific data. The rendered prompt is passed to common_chat, which then communicates with the model to obtain a chat response. Similarly, in chat_with_tools, the rendered prompt is sent alongside any specified tools, allowing for a more dynamic interaction based on the user's needs.

The update_answer method relies on common_chat to refine the agent's response by sending a newly constructed prompt that incorporates user feedback and search results. The model_confident method uses common_chat to assess the model's confidence level regarding a user query, while web_scrape_results and search_and_browse leverage common_chat to interact with the model for web scraping and searching tasks.

Overall, common_chat acts as a bridge between the user prompts generated by various methods and the conversational model, ensuring that the interaction is seamless and effective.

**Note**: It is important to ensure that the usr_prompt parameter is well-formed and relevant to the context of the conversation to receive an accurate response from the model. Additionally, the tools parameter should be used judiciously to enhance the functionality of the chat interaction when necessary.
***
### FunctionDef common_chat(self, usr_prompt, tools, role, model)
**common_chat**: The function of common_chat is to facilitate interaction with a language model by processing user prompts and returning generated responses.

**parameters**: The parameters of this Function.
· usr_prompt: A string or list representing the user's prompt to the model, which serves as the basis for generating a response.  
· tools: An optional list of tools that the model can utilize during the interaction. If not provided, it defaults to None.  
· role: A string indicating the role of the entity interacting with the model, defaulting to "assistant".  
· model: A string specifying the model to be used for generating the response, defaulting to the model defined in the settings.

**Code Description**: The common_chat function is a method within the BaseAgent class that serves as a bridge for communication between the user and a language model. It begins by invoking the call_llm function, which interacts with the language model API to generate a response based on the provided user prompt (usr_prompt). The model parameter allows for flexibility in specifying which model to use, while the tools parameter enables the use of additional functionalities during the interaction.

Upon receiving the response from the call_llm function, the common_chat function checks if any tools were specified. If tools are present, the function returns the model's response directly. If no tools are specified, it appends the model's response to the conversation history using the append_to_history method from the ConversationManager class. This method records the response along with the specified role, ensuring that the conversation flow is maintained.

The common_chat function is called by various methods within the BaseAgent class, such as chat_with_template and chat_with_tools. These methods utilize common_chat to handle user prompts that have been processed through templates or require the use of specific tools. Additionally, it is invoked in the update_answer and model_confident methods, where it plays a crucial role in refining the agent's responses based on user queries and feedback.

In summary, common_chat is essential for managing interactions with the language model, ensuring that user prompts are effectively processed and responses are accurately recorded in the conversation history. This functionality is vital for applications that rely on conversational agents, as it provides a structured approach to dialogue management.

**Note**: It is important to ensure that the usr_prompt parameter is well-formed and relevant to the context of the conversation. The tools parameter should only be used if supported by the model, and the role parameter should accurately reflect the entity's role in the conversation to avoid any inconsistencies.

**Output Example**: A possible return value from the common_chat function could be a string such as "The capital of France is Paris." This output reflects the model's generated response based on the user's prompt.
***
### FunctionDef update_answer(self, query, previous_answer, search_results, critic_feedback)
**update_answer**: The function of update_answer is to refine the agent's response based on user feedback, previous answers, and search results.

**parameters**: The parameters of this Function.
· query: A string representing the user's current question or prompt that needs to be addressed.  
· previous_answer: A string containing the agent's last response to the user's query, which serves as a reference for improvement.  
· search_results: A string or structured data containing the results obtained from a search operation that may provide additional context or information relevant to the query.  
· critic_feedback: A string containing feedback from a critic agent, which may include suggestions or evaluations of the previous answer.

**Code Description**: The update_answer function is a method within the BaseAgent class designed to enhance the quality of the agent's responses by integrating new information and feedback. This function takes four parameters: `query`, `previous_answer`, `search_results`, and `critic_feedback`. 

The function begins by organizing these parameters into a dictionary called `data`, which serves as a structured format for the information that will be utilized in generating a new response. The next step involves loading a template for the update process by calling the load_template method with the filename "agent_update_answer.txt". This template is crucial as it provides a predefined structure for the prompt that will be sent to the conversational model.

Once the template is loaded, the function renders it using the render_template method, passing in the `data` dictionary. This step replaces placeholders in the template with actual values from the provided parameters, creating a contextually relevant prompt.

The rendered prompt is then sent to the common_chat method, which facilitates communication with the conversational model. This method processes the prompt and returns a response based on the updated context, effectively allowing the agent to generate a more informed and relevant answer.

The update_answer function is called within the main function of the project, specifically during the iterative process of refining the agent's responses based on feedback from a critic agent. After the initial response is generated, the update_answer method is invoked to incorporate new search results and feedback, ensuring that the agent's final output is polished and aligned with user expectations.

**Note**: It is important to ensure that the parameters passed to the update_answer function are well-formed and relevant to the context of the conversation. The effectiveness of the function relies on the quality of the previous answer, search results, and critic feedback provided.

**Output Example**: A possible return value from the update_answer function could be a string such as "Based on the latest search results and your feedback, the updated answer is: The capital of France is Paris."
***
### FunctionDef model_confident(self, query)
**model_confident**: The function of model_confident is to check whether the model is confident in its response to the current user query.

**parameters**: The parameters of this Function.
· query: A string representing the user's question that needs to be evaluated for the model's confidence.

**Code Description**: The model_confident function is a method within the BaseAgent class that assesses the confidence level of the model regarding a specific user query. It takes a single parameter, query, which is the user's question. The function begins by creating a data dictionary that includes the user's question under the key "user_question". 

Next, it calls the load_template method to retrieve a template from the prompts directory, specifically the "agent_confidence.txt" file. This template is used to formulate a prompt that will be sent to the conversational model. The rendered prompt is generated by passing the loaded template and the data dictionary to the render_template method, which replaces placeholders in the template with actual values from the data dictionary.

Once the rendered prompt is prepared, the function invokes the common_chat method, passing the rendered prompt as the usr_prompt parameter. This method facilitates communication with the conversational model, sending the prompt and receiving a response that indicates the model's confidence level regarding the user's query.

The model_confident function is called within the main function of the project, specifically during the first iteration of a loop that processes user tasks. After initializing the task, the model_confident function is invoked to determine if the model is confident enough to provide a direct answer to the user's question. If the model indicates confidence, the common_chat method is called again to retrieve the answer. Conversely, if the model is not confident, the function initiates a search process to gather more information before attempting to answer the query.

This function plays a critical role in ensuring that the agent only provides answers when it is confident in the information, thereby enhancing the reliability of the responses generated by the conversational model.

**Note**: It is essential to ensure that the query parameter passed to the model_confident function is well-formed and relevant to the context of the conversation. This will help in obtaining an accurate assessment of the model's confidence level.

**Output Example**: A possible return value from the model_confident function could be a string indicating the model's confidence level, such as:
```
"Confidence: true"
```
***
### FunctionDef web_scrape_results(self, search_results)
**web_scrape_results**: The function of web_scrape_results is to extract web content from search results using a web scraper.

**parameters**: The parameters of this Function.
· search_results: A string representing the initial search results to scrape from.

**Code Description**: The web_scrape_results function is a method within the BaseAgent class that facilitates the extraction of web content based on initial search results provided as input. The function begins by loading a template for the web scraper using the load_template method, which retrieves the content of a specified template file from the prompts directory. This template is then rendered with the user question and the initial search results using the render_template method, which formats the template string by replacing placeholders with actual values from the provided data.

Following the preparation of the rendered prompt, the function interacts with a conversational model through the common_chat method, sending the rendered prompt along with any necessary tools defined in the content_scraper_schema. The response from this interaction is analyzed to determine if any tool calls were made. If no tool calls are present, the function returns the content of the response directly.

In cases where tool calls are included in the response, the function appends these calls to the conversation history using the append_tool_call_to_history method. It then initializes an empty string to accumulate the final web scraping results. For each tool call, the function extracts the URLs from the arguments and invokes the content scraper's scrape method asynchronously to retrieve the content from the specified URLs. The results of these scraping operations are logged into the conversation history using the append_tool_call_result_to_history method.

The web_scrape_results function is called within the search_and_browse method of the BaseAgent class, which orchestrates a two-step process of searching for information and subsequently scraping content based on the search results. This highlights the function's role in enhancing the agent's ability to provide accurate and relevant responses by leveraging real-time data from web sources.

**Note**: It is essential to ensure that the search_results parameter is well-formed and contains relevant queries for the scraping process to function effectively. Additionally, proper error handling should be implemented to manage cases where the scraping operations do not yield results.

**Output Example**: A possible return value from the web_scrape_results function could be a string formatted as follows:
```
"Here are the results from your search: 1. Title: Example Article, URL: http://example.com/article1, Content: This is a summary of the article. 2. Title: Another Example, URL: http://example.com/article2, Content: This is another summary."
```
***
### FunctionDef search_and_browse(self, rendered_prompt)
**search_and_browse**: The function of search_and_browse is to perform a search based on a user-provided prompt and subsequently scrape web content from the search results.

**parameters**: The parameters of this Function.
· rendered_prompt: A string that contains the user prompt formatted for the search operation.

**Code Description**: The search_and_browse function is a method within the BaseAgent class that orchestrates a two-step process: first, it conducts a search using a conversational model based on the provided user prompt, and second, it scrapes web content from the results of that search. 

The function begins by invoking the common_chat method, passing the rendered_prompt and a schema of tools (search_aggregator_schema) that may be utilized during the search interaction. The response from this method, search_with_tool_response, contains the results of the search operation.

If the search_with_tool_response indicates that no tool calls were made (i.e., tool_calls is None), the function returns the content of the response directly. This allows for immediate feedback to the user without further processing.

In cases where tool calls are present, the function appends these calls to the conversation history using the append_tool_call_to_history method from the ConversationManager class. This ensures that all interactions with external tools are logged for future reference.

The function then initializes an empty string, final_search_results, to accumulate the results from each tool call. It iterates through the tool calls, extracting the search query from the tool call's arguments. For each query, it invokes the search method from the SearchAggregator class asynchronously to perform the actual search. The results are awaited, and a brief sleep is introduced to manage rate limits.

After obtaining the search results, the function logs the results into the conversation history using the append_tool_call_result_to_history method. It also updates the query database with the executed query using the update method from the queryDB.

Finally, the function compiles all the search results into the final_search_results string and returns the results after processing them through the web_scrape_results method. This method is responsible for extracting relevant web content based on the search results, enhancing the overall response provided to the user.

The search_and_browse function is called within the process_single_task function, where it is utilized to refine the agent's responses based on user feedback and additional search queries. This highlights its role in ensuring that the agent can provide accurate and relevant information by leveraging real-time data from web sources.

**Note**: It is important to ensure that the rendered_prompt parameter is well-formed and relevant to the context of the search. Proper error handling should be implemented to manage cases where the search operation does not yield valid results.

**Output Example**: A possible return value from the search_and_browse function could be a string formatted as follows:
```
"Here are the results from your search: 1. Title: Latest Tech Innovations, URL: http://example.com/latest-tech, Content: Discover the newest advancements in technology. 2. Title: AI in Healthcare, URL: http://example.com/ai-healthcare, Content: Explore how AI is transforming the healthcare industry."
```
***
### FunctionDef receive_task(self, task)
**receive_task**: The function of receive_task is to accept and store the original task provided to the agent.

**parameters**: The parameters of this Function.
· task: The original task that is being received and stored by the agent.

**Code Description**: The receive_task function is a method defined within the BaseAgent class. Its primary purpose is to accept a task input, which is expected to be a string or a structured object representing the task details. Upon invocation, the function assigns the input task to the instance variable original_task, effectively storing it for later use within the agent's operations.

This function plays a critical role in the workflow of the BaseAgent, as it serves as the initial point of interaction where the agent receives the task it needs to process. The stored task can later be utilized in various methods of the BaseAgent, such as when generating responses or conducting searches based on the task's requirements.

The receive_task function is called by the CriticAgent within the process_single_task function located in the src/criticsearch/main.py file. In this context, the CriticAgent is responsible for evaluating the task and the responses generated by the common agent. By invoking receive_task, the CriticAgent ensures that it has access to the original task, which is essential for providing accurate feedback and evaluations based on the task's context.

**Note**: It is important to ensure that the task parameter passed to receive_task is well-structured and relevant to the agent's capabilities, as this will directly influence the effectiveness of the agent's subsequent operations.
***
### FunctionDef extract_and_validate_yaml(self, model_response)
**extract_and_validate_yaml**: The function of extract_and_validate_yaml is to extract YAML content from a given string and validate its format.

**parameters**: The parameters of this Function.
· model_response: A string containing the response from a model, which is expected to include YAML content wrapped in specific delimiters.

**Code Description**: The extract_and_validate_yaml function is a method within the BaseAgent class that processes a string input, searching for YAML content encapsulated within triple backticks (```yaml```). The function utilizes regular expressions to identify and extract the relevant portion of the string. If the expected YAML content is not found, the function returns None, indicating a failure to extract valid content.

Once the YAML content is extracted, the function attempts to parse it using the yaml.safe_load method. This method is designed to safely parse YAML strings into Python objects. If the parsing is successful, the function returns a formatted YAML string using yaml.dump, which can be utilized for further processing or output. However, if a yaml.YAMLError occurs during parsing, the function catches this exception, prints an error message indicating the invalid content, and returns None.

The extract_and_validate_yaml function is called by other methods within the project, such as the critic method in the CriticAgent class. In this context, it is used to validate and extract YAML feedback from the model's response after generating a critique based on user input and agent responses. The successful extraction and validation of YAML content are crucial for the flow of information between the CriticAgent and the BaseAgent, as it directly influences the feedback mechanism and the overall interaction quality.

**Note**: It is essential to ensure that the model_response string contains valid YAML content wrapped in the correct delimiters. If the content is not valid YAML, the function will return None, which may disrupt the expected flow of the application.

**Output Example**: A possible return value from the extract_and_validate_yaml function could be a YAML formatted string such as:

```yaml
feedback: "The agent's answer is comprehensive but lacks specific examples."
suggestions:
  - "Include more detailed explanations."
  - "Provide references to support claims."
```
***
### FunctionDef extract_and_validate_json(self, model_response)
**extract_and_validate_json**: The function of extract_and_validate_json is to extract JSON data from a given string and validate its correctness.

**parameters**: The parameters of this Function.
· model_response: A string that may contain JSON data, potentially wrapped in specific formatting.

**Code Description**: The extract_and_validate_json function is designed to process a string input, model_response, which is expected to contain JSON data. The function first attempts to locate JSON content that is enclosed within ```json``` code blocks using a regular expression. If such a block is found, it extracts the content and removes any leading or trailing whitespace. If no such block is found, it assumes that the entire input string is the JSON content and trims any whitespace accordingly.

Once the JSON content is identified, the function attempts to parse it using the json.loads method. If the parsing is successful, the parsed JSON object is returned. However, if a json.JSONDecodeError occurs during parsing, indicating that the content is not valid JSON, the function prints an error message detailing the issue and returns None.

This function is called within the context of the BaseAgent class, specifically in methods such as process_single_task and main. In these methods, extract_and_validate_json is used to validate the structure of outlines generated from user queries or model responses. By ensuring that the outlines are valid JSON, the function plays a crucial role in maintaining the integrity of the data being processed, which is essential for subsequent operations such as flattening the outline and generating content for various sections.

**Note**: It is important to ensure that the input string is formatted correctly to avoid JSON parsing errors. The function will return None if the input does not contain valid JSON, which should be handled appropriately by the calling functions to prevent further issues in the workflow.

**Output Example**: A possible return value of the function could be a dictionary representing the parsed JSON, such as:
{
    "sections": [
        {
            "title": "Introduction",
            "content": "This is the introduction section."
        },
        {
            "title": "Conclusion",
            "content": "This is the conclusion section."
        }
    ]
}
***
