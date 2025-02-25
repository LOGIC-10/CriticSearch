## ClassDef ModelManager
**ModelManager**: The function of ModelManager is to manage model configurations and clients, enabling the creation of OpenAI API clients and retrieval of model-specific configurations.

**attributes**:
- config: Stores the configuration object containing model configurations and other settings.
- clients: A dictionary that holds initialized client objects indexed by model names.

**Code Description**:  
The `ModelManager` class is designed to handle the management of model configurations and the creation of API clients that interact with OpenAI’s services.

- **`__init__(self, config)`**:  
  The constructor initializes the `ModelManager` with the given `config` parameter, which contains the settings for the models, such as API keys, URLs, and other relevant configurations. It also initializes an empty `clients` dictionary that will store the client instances corresponding to each model.

- **`get_model_config(self, model_name=None)`**:  
  This method retrieves the configuration for a specific model. If no model name is provided, it defaults to the first model in the configuration. The function raises an error if no models are found or if the specified model name is not available in the configuration. It returns the configuration dictionary for the selected model.

- **`create_client(self, model_name=None)`**:  
  This method is responsible for creating and returning a client object. It checks if the client for the specified model already exists in the `clients` dictionary. If not, it retrieves the configuration for the model using `get_model_config`, and initializes an OpenAI client (using the `OpenAI` class, which is not shown in the provided code but is assumed to be a predefined class or function) with the relevant settings like the API key, base URL, timeout, and retry parameters. Once created, the client is stored in the `clients` dictionary for reuse.

From a functional perspective, the `ModelManager` class is used by the `call_llm` function in the project. The `call_llm` function interacts with `ModelManager` to:
1. Instantiate a `ModelManager` object using the provided configuration.
2. Create a client for the specified model (or default to the first model if no model name is provided).
3. Retrieve the configuration for the selected model.
4. Use the configuration and client to make API calls to OpenAI’s services and process the responses.

The `ModelManager` acts as a central utility that abstracts away the complexity of managing multiple models and their configurations. By using this class, the system can easily handle different model configurations and create clients for various models dynamically.

**Note**:
- The `config` passed into the `ModelManager` should contain a "models" key that maps model names to their respective configurations.
- If a model is not found in the configuration, a `ValueError` will be raised, so proper error handling should be considered when using this class.
- The OpenAI client is created with a default timeout of 120 seconds and the possibility to customize retry settings, which are important for dealing with API reliability.

**Output Example**:  
When `create_client` is called with a model name like "gpt-4", the output will be an instance of an OpenAI client initialized with that model’s configuration, assuming that the configuration contains the appropriate API key and endpoint. The exact appearance of this client is dependent on the implementation of the OpenAI client, but it will allow making requests to OpenAI's API to process prompts and retrieve responses.
### FunctionDef __init__(self, config)
**__init__**: The function of __init__ is to initialize an instance of the class with a configuration and an empty client dictionary.

**parameters**: The parameters of this Function.
· config: A configuration object or data used to initialize the instance.

**Code Description**: 
The `__init__` function is the constructor method of the class, used to initialize an object of the class when it is instantiated. 
- The `config` parameter is passed into the constructor and assigned to the instance variable `self.config`. This suggests that the configuration data will be available throughout the lifetime of the object for further use. 
- The `clients` instance variable is initialized as an empty dictionary (`{}`). This implies that the object will eventually store client-related data or mappings in this dictionary during its lifecycle.

**Note**: 
- The `config` parameter should be provided when creating an instance of the class; its structure and contents will depend on the requirements of the class and the overall application.
- The `clients` dictionary is initialized as empty, and its population will likely occur later in the class methods.
***
### FunctionDef get_model_config(self, model_name)
**get_model_config**: The function of get_model_config is to retrieve the configuration settings for a specific model from the configuration file.

**parameters**:
· model_name: A string representing the name of the model. If not provided, the first model in the configuration is selected.

**Code Description**:  
The `get_model_config` function is responsible for fetching the configuration for a specified model from the configuration dictionary stored in the `self.config` attribute. 

1. The function starts by retrieving the "models" section of the configuration using `self.config.get("models", {})`. If no models are found, a `ValueError` is raised with the message "No models found in configuration."
   
2. If the `model_name` parameter is not provided, the function selects the first available model by using `next(iter(models.keys()))`.

3. The function checks if the `model_name` exists in the models configuration. If it is not found, a `ValueError` is raised indicating the model is not in the configuration, and it provides a list of available models.

4. If the model is found, the function retrieves its configuration from the `models` dictionary and returns it.

The function is used by other components in the project to ensure that the correct configuration for a model is retrieved. For example, in the `create_client` method, it is used to get the configuration of a specific model when creating an OpenAI client. It is also utilized in the `call_llm` function, where it is used to get the model configuration to set up parameters for making API calls.

**Note**:  
- The function raises errors if the models section is missing or if the specified model is not found in the configuration.
- The function defaults to the first model in the configuration if no model name is provided.

**Output Example**:  
If the configuration for the model "gpt-3" contains the following settings:
```json
{
  "models": {
    "gpt-3": {
      "api_key": "your-api-key",
      "base_url": "https://api.openai.com/v1",
      "temperature": 0.7,
      "max_tokens": 150
    }
  }
}
```
Calling `get_model_config("gpt-3")` would return:
```python
{
  "api_key": "your-api-key",
  "base_url": "https://api.openai.com/v1",
  "temperature": 0.7,
  "max_tokens": 150
}
```
***
### FunctionDef create_client(self, model_name)
**create_client**: The function of create_client is to create and return an OpenAI client instance for a specified model.

**parameters**: The parameters of this Function.
· model_name: A string representing the name of the model for which the client is to be created. If not provided, the first model in the configuration is selected.

**Code Description**: The `create_client` function is responsible for instantiating and returning an OpenAI client based on the specified model name. The function first checks if a model name has been provided; if not, it defaults to the first model available in the configuration. 

The function then checks if a client for the specified model already exists in the `self.clients` dictionary. If it does, the existing client is returned, avoiding the overhead of creating a new instance. 

If the client does not exist, the function retrieves the model's configuration using the `get_model_config` method. This method fetches the necessary API key, base URL, timeout, and maximum retries for the model from the configuration settings. 

An instance of the OpenAI client is then created using the retrieved configuration parameters. This instance is stored in the `self.clients` dictionary for future use and is returned to the caller.

The `create_client` function is called by the `call_llm` function, which is responsible for making API calls to the OpenAI service. In `call_llm`, the `create_client` function is invoked to obtain the client needed to interact with the OpenAI API, ensuring that the correct configuration is used for the specified model. This establishes a direct relationship where `call_llm` relies on `create_client` to provide the necessary client instance for executing its operations.

**Note**: It is important to ensure that the model name provided is valid and exists in the configuration. If the model name is not found, the `get_model_config` method will raise an error, which will propagate back to the caller, potentially affecting the execution of the `call_llm` function.

**Output Example**: If the model name "gpt-3" is specified and the configuration is correctly set, the function would return an instance of the OpenAI client configured for "gpt-3". The returned client would be capable of making API calls to the OpenAI service with the specified parameters.
***
## FunctionDef call_llm(model, usr_prompt, config, tools)
## `call_llm` Function Documentation

### Purpose:
The `call_llm` function interacts with a language model API to generate responses based on a user-provided prompt. It handles communication with the OpenAI API or a similar service, utilizing a model configuration and client provided through the `ModelManager`.

### Parameters:
- **model** (`str`):  
  The name of the model to be used for generating the response (e.g., `"gpt-4"`). It is passed to the `ModelManager` to create the appropriate client.
  
- **usr_prompt** (`str | Iterable[ChatCompletionMessageParam]`):  
  The user prompt to send to the model. It can either be a single string message or an iterable of `ChatCompletionMessageParam` objects. The prompt is the basis of the model's response.

- **config** (`dict`):  
  A configuration dictionary used to initialize the `ModelManager`. It includes settings related to model configurations such as API keys, timeout settings, and retry parameters.

- **tools** (`List | None`, optional):  
  A list of tools that can be used by the model during the interaction. This is an optional parameter. If not provided, the function defaults to `None`.

### Returns:
- **ChatCompletionMessage**:  
  The generated response message from the model. This object contains the model's output based on the provided prompt.

### Functionality:
1. **Initialize ModelManager**:  
   A `ModelManager` instance is created using the provided configuration (`config`). This instance is responsible for managing model-specific settings and clients.

2. **Create Model Client**:  
   The `create_client` method of `ModelManager` is used to create a client for the specified model. If a client for the model does not already exist, it is initialized and stored.

3. **Configure Prompt**:  
   The `usr_prompt` is processed. If it is a string, it is converted into a message format. If it is already an iterable of `ChatCompletionMessageParam`, it is used as-is.

4. **API Request**:  
   The function sends the prompt to the OpenAI API (or a compatible service) via the client, using settings such as `temperature` and `max_tokens` from the model's configuration. If tools are provided, they are passed along with the request.

5. **Handle Response**:  
   The function extracts the response message from the API's result. If the model supports tools, it handles the response accordingly. If not, it reattempts the request without tools.

6. **Error Handling**:  
   The function raises specific exceptions in case of errors, including:
   - `APIConnectionError`: If there is an issue connecting to the API.
   - `ValueError`: If there is an issue with the configuration or model settings.
   - `BadRequestError`: If the model does not support tools (in which case, a retry without tools is performed).

### Example Usage:
```python
response = call_llm(
    model="gpt-4",
    usr_prompt="What is the capital of France?",
    config=config_dict
)
```

### Notes:
- The `model` parameter should correspond to a valid model name as specified in the configuration.
- The `config` dictionary must include all necessary settings for model initialization, including API keys and any model-specific options.
- The `tools` parameter is optional, and should only be used if supported by the model. If the model does not support tools, the function will handle this by retrying without them.
- Proper error handling should be implemented to manage exceptions such as connection failures or invalid configurations.
