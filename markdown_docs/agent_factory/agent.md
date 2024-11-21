## ClassDef BaseAgent
**BaseAgent**: The function of BaseAgent is to serve as the foundational agent for performing tasks related to querying and processing information with a model, as well as managing related configurations and data structures.

**attributes**:
· `config`: A configuration object containing various settings loaded from a configuration file.  
· `model`: A string specifying the default model to be used for interactions (defaults to "gpt-4o-mini").  
· `env`: An Environment object initialized with a file system loader pointing to the prompt folder path defined in the configuration.  
· `queryDB`: A set that stores queries. This set is used to hold each unique query issued by the agent.  
· `citationDB`: A list of dictionaries, where each dictionary represents a query and its associated citation data (only queries praised by the critic are included).  
· `sys_prompt`: A string holding the system-level prompt used for guiding interactions with the model.  
· `repeat_turns`: An integer specifying the maximum number of turns for repeating a task or conversation (defaults to 10).  
· `original_task`: A placeholder for the original task that will be processed by the agent.

**Code Description**:  
The `BaseAgent` class provides the essential functionality for interacting with an AI model and handling related tasks. It begins by initializing various attributes, such as loading configuration details, setting the default model to "gpt-4o-mini", and setting up a file-based environment for loading prompts. The agent also maintains a set `queryDB` to track all issued queries and a `citationDB` for storing search results with associated citations, ensuring that only specific search results are included (those deemed worthy by a critic).  

The `common_chat` method facilitates interaction with the model by taking a query and invoking a model with a predefined system prompt. The method `chat_with_template` is more flexible, allowing for dynamic generation of prompts from a provided template. It first renders the template using data passed to it and then passes the generated prompt to `common_chat`.  

The `receive_task` method stores the task passed to the agent, ensuring the agent can process it later. The `extract_and_validate_yaml` method is a utility for extracting and validating YAML-formatted data from the response returned by the model. It searches for a YAML block in the response and attempts to parse it, returning the valid YAML content in a human-readable format if the extraction is successful. If no valid YAML is found or an error occurs during parsing, the method returns `None`.  

**Note**:  
- The agent requires a properly structured configuration file to initialize correctly. 
- The `citationDB` is a critical component for maintaining the quality of search results.
- The `repeat_turns` parameter limits the number of times an agent will reattempt a task.
- `extract_and_validate_yaml` uses regular expressions to extract YAML content and relies on Python's `yaml` library for parsing.

**Output Example**:  
For `common_chat`, a mock response might be:
```json
{
  "response": "The challenges faced by Google in 2019 included increasing competition, regulatory pressures, and internal company restructuring."
}
```
For `extract_and_validate_yaml`, a valid YAML block returned might look like:
```yaml
model: gpt-4o-mini
config:
  timeout: 30
  retries: 3
```
### FunctionDef __init__(self)
**__init__**: The function of __init__ is to initialize an instance of the BaseAgent class with configuration settings and data structures for managing queries and citations.

**parameters**: The parameters of this Function.
· There are no parameters for this function.

**Code Description**: The __init__ function is a constructor for the BaseAgent class. It is responsible for setting up the initial state of an instance when it is created. The function performs the following actions:

1. It calls the `read_config()` function to load configuration settings, which are stored in the `self.config` attribute. This configuration is essential for the agent's operation, as it contains various settings that dictate how the agent behaves.

2. The `self.model` attribute is initialized with the value of the 'default_model' key from the configuration. If this key is not present, it defaults to "gpt-4o-mini". This model will likely be used for generating responses or processing queries.

3. The `self.env` attribute is initialized as an instance of the `Environment` class, which is configured with a `FileSystemLoader`. The loader is set to the path specified by the 'prompt_folder_path' key in the configuration. This environment is likely used for loading templates or prompts that the agent will utilize.

4. The `self.queryDB` attribute is initialized as an empty set. This set is intended to store unique queries that the agent will process. Using a set ensures that each query is distinct and prevents duplicates.

5. The `self.citationDB` attribute is initialized with a list containing a single dictionary. This dictionary is structured to hold search questions as keys, with corresponding values that are themselves dictionaries. Each value dictionary contains a "document_id" key, which is a unique identifier for a document, along with placeholders for "url", "title", and "content". This structure is designed to store search results that have received positive feedback from critics.

6. The `self.sys_prompt` attribute is initialized as an empty string. This prompt may be used to guide the agent's responses or behavior during interactions.

7. The `self.repeat_turns` attribute is set to 10, indicating the number of times the agent may repeat a certain action or query during its operation.

**Note**: It is important to ensure that the configuration file is correctly set up and accessible, as the agent relies heavily on the parameters defined within it. Additionally, the structure of `citationDB` should be maintained to ensure that the agent can effectively manage and reference search results.
***
### FunctionDef common_chat(self, query)
**common_chat**: The function of common_chat is to facilitate communication with a language model by sending a user-defined query along with system prompts and configuration settings.

**parameters**: The parameters of this Function.
· query: A string that represents the user input or question that will be sent to the language model.

**Code Description**: The common_chat function is designed to interact with a language model (LLM) by calling the function `call_llm`. It takes a single parameter, `query`, which is expected to be a string. This string is typically the user's input that needs to be processed by the language model. The function constructs a call to `call_llm`, passing it several arguments: `model`, `sys_prompt`, `usr_prompt`, and `config`. Here, `model` refers to the specific language model being utilized, `sys_prompt` is a predefined system prompt that sets the context for the conversation, `usr_prompt` is the user query (in this case, the `query` parameter), and `config` contains additional configuration settings that may influence the behavior of the language model.

The common_chat function is called within the `chat_with_template` method of the BaseAgent class. In this context, `chat_with_template` prepares a prompt by rendering it with data provided in the `data` dictionary using a specified `prompt_template`. Once the prompt is rendered, it invokes `common_chat`, passing the rendered prompt as the query. The response from `common_chat` is then returned as the output of `chat_with_template`. This establishes a clear relationship where `chat_with_template` relies on `common_chat` to handle the actual communication with the language model after preparing the appropriate prompt.

**Note**: It is important to ensure that the `query` passed to common_chat is properly formatted and relevant to the context established by the system prompt to achieve meaningful responses from the language model.

**Output Example**: A possible return value from the common_chat function could be a string such as "Sure, I can help you with that! What specific information are you looking for?" This response would depend on the input query and the configuration of the language model.
***
### FunctionDef chat_with_template(self, data, prompt_template)
**chat_with_template**: The function of chat_with_template is to facilitate a conversation by rendering a prompt template with provided data and then communicating with a language model.

**parameters**: The parameters of this Function.
· data: A dictionary containing key-value pairs that will be used to populate the prompt template.
· prompt_template: An object that defines the structure of the prompt to be rendered, which will be filled with the values from the data dictionary.

**Code Description**: The chat_with_template method is designed to generate a dynamic prompt for a conversation based on the input data. It takes two parameters: `data`, which is a dictionary containing the necessary information to fill in the prompt template, and `prompt_template`, which is an object that specifies how the prompt should be structured. 

The method begins by rendering the prompt using the `render` method of the `prompt_template`, passing the unpacked `data` dictionary as keyword arguments. This results in a `rendered_prompt`, which is a string that represents the final prompt to be sent to the language model.

Following the rendering process, the method calls `common_chat`, passing the `rendered_prompt` as the `query` parameter. The `common_chat` function is responsible for sending this query to a language model, allowing for interaction based on the generated prompt. The response from `common_chat` is then returned as the output of the `chat_with_template` method.

This establishes a clear functional relationship where `chat_with_template` serves as a preparatory step that formats the input data into a suitable prompt, which is then processed by `common_chat` to obtain a response from the language model.

**Note**: It is essential to ensure that the `data` provided is complete and correctly structured to match the expectations of the `prompt_template`. This will ensure that the rendered prompt is coherent and relevant, leading to meaningful interactions with the language model.

**Output Example**: A possible return value from the chat_with_template function could be a string such as "Hello! How can I assist you today?" This response will depend on the specific data provided and the structure of the prompt template used.
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
· model_response: A string input that potentially contains YAML content wrapped in ```yaml``` markers.

**Code Description**: The extract_and_validate_yaml function begins by importing the regular expression module (re) to facilitate pattern matching. It uses a regular expression to search for content that is enclosed between ```yaml``` markers in the provided model_response string. The pattern `r'```yaml\n([\s\S]*?)\n```'` is designed to capture everything between the opening and closing markers, including newlines and whitespace.

If the search does not find a match, the function returns None, indicating that no valid YAML content was found. If a match is found, the captured content is stripped of leading and trailing whitespace. The function then attempts to parse this YAML content using the yaml.safe_load method from the PyYAML library. If the parsing is successful, it returns the YAML content formatted as a string using yaml.dump, with default_flow_style set to False for a more human-readable format.

In the event of a parsing error, the function catches the yaml.YAMLError exception, prints an error message indicating that the YAML content is invalid, and returns None.

**Note**: It is important to ensure that the input string contains valid YAML syntax wrapped in the specified markers. If the input does not conform to this structure, the function will return None without raising an error.

**Output Example**: If the input model_response is:
```
Here is some configuration:
```yaml
key: value
list:
  - item1
  - item2
```
```
The function would return:
```
key:
  value
list:
- item1
- item2
```
***
