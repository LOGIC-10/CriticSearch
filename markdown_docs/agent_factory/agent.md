## ClassDef BaseAgent
**BaseAgent**: The function of BaseAgent is to serve as a foundational class for handling chat interactions and processing tasks using a specified language model.

**attributes**: The attributes of this Class.
· config: A configuration object that holds various settings for the agent, including model specifications and prompt folder paths.  
· model: The name of the default language model to be used for chat interactions, initialized to "gpt-4o-mini".  
· env: An instance of the Environment class, which is configured to load templates from a specified folder path.  
· sys_prompt: A string that holds the system prompt for the chat interactions, initialized as an empty string.  
· repeat_turns: An integer that defines the number of turns to repeat in the chat, initialized to 10.  
· original_task: A variable to store the original task received by the agent.

**Code Description**: The BaseAgent class is designed to facilitate interactions with a language model through chat functionalities. Upon initialization, it reads the configuration settings, including the default model and the path for prompt templates. The class provides several methods to interact with the model and process tasks.

The `common_chat` method takes a user query as input and calls the language model using the specified system prompt and user prompt. This method serves as the primary interface for generating responses based on user input.

The `chat_with_template` method allows for dynamic prompt generation by rendering a template with provided data. It utilizes the Jinja2 templating engine to create a customized prompt before passing it to the `common_chat` method for processing.

The `receive_task` method is used to accept and store an original task, which can be further processed or utilized in chat interactions.

The `extract_and_validate_yaml` method is responsible for extracting YAML content from a model's response. It uses regular expressions to find content wrapped in ```yaml``` tags and attempts to parse it using the PyYAML library. If successful, it returns the YAML content in a standardized format; otherwise, it handles errors gracefully by returning None.

**Note**: When using the BaseAgent class, ensure that the configuration file is correctly set up with the necessary parameters, including the prompt folder path and the default model. Additionally, proper error handling should be implemented when dealing with YAML content to avoid runtime exceptions.

**Output Example**: A possible return value from the `common_chat` method could be a string response from the language model, such as: "Hello! How can I assist you today?" If the `extract_and_validate_yaml` method is called with a valid model response containing YAML, it might return a formatted YAML string like:
```yaml
key1: value1
key2: value2
```
### FunctionDef __init__(self)
**__init__**: The function of __init__ is to initialize an instance of the BaseAgent class by setting up its configuration and environment.

**parameters**: The parameters of this Function.
· None

**Code Description**: The __init__ method is a constructor for the BaseAgent class. It is called when an instance of the class is created. The method performs several key operations:

1. It invokes the read_config function to load configuration settings from a YAML file. This function returns a dictionary containing various configuration parameters, which is stored in the instance variable self.config.

2. The method retrieves the value associated with the key 'default_model' from the configuration dictionary. If this key is not present, it defaults to the string "gpt-4o-mini". This value is stored in the instance variable self.model, which likely represents the model that the agent will use for its operations.

3. The method initializes an Environment object from the Jinja2 templating library. This object is configured with a loader that points to the directory specified by the 'prompt_folder_path' key in the configuration dictionary. This allows the agent to dynamically load prompt templates from the specified folder.

4. The instance variable self.sys_prompt is initialized as an empty string, which may be used later to store system prompts or messages.

5. Finally, the method sets self.repeat_turns to 10, which could indicate the number of times the agent is allowed to repeat certain actions or interactions during its operation.

Overall, the __init__ method establishes the foundational settings and components necessary for the BaseAgent to function effectively. It relies on the read_config function to ensure that the agent is configured according to the specified settings in the YAML file, thus enabling flexibility and customization in its behavior.

**Note**: It is crucial to ensure that the YAML configuration file is accessible and correctly formatted. Any issues with file access or parsing may result in runtime errors, preventing the BaseAgent from initializing properly.
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
