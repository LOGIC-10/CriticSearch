## ClassDef ToolRegistry
**ToolRegistry**: The function of ToolRegistry is to manage tools by storing and retrieving their schemas based on function names.

**attributes**: The attributes of this Class.
· _tools: A dictionary mapping function names to their respective schemas.  
· _funcs: A dictionary mapping function names to their actual callable functions.  

**Code Description**: The ToolRegistry class serves as a centralized registry for managing tools, allowing for the retrieval and creation of schemas associated with specific functions. Upon initialization, it sets up two private dictionaries: `_tools`, which holds the schemas of the tools indexed by their function names, and `_funcs`, which stores the actual callable functions corresponding to those names.

The primary method, `get_or_create_tool_schema`, accepts one or more functions as arguments. It checks if a schema for each function is already registered. If not, it creates a new schema using the `Tool.create_schema_from_function` method and logs the creation process. This method returns a list of schemas corresponding to the provided functions, ensuring that tools can be reused efficiently without the need for redundant schema creation.

Another important method, `register_tool`, allows for the manual registration of tools. It requires the tool's name, the function that implements the tool, a description, and optional parameters. If parameters are not provided, it automatically generates them from the function's signature. This method updates the `_tools` and `_funcs` dictionaries with the new tool's schema and logs the registration.

The `invoke_tool` method enables the invocation of a registered tool by its name, passing the specified arguments to the corresponding function. If the function is not found in the registry, it raises a KeyError. This method also handles asynchronous function calls, ensuring that if the invoked function returns an awaitable, it is executed properly.

The ToolRegistry class is utilized within the BaseAgent class, which serves as a foundational component for intelligent agents. The BaseAgent creates an instance of ToolRegistry to manage tool schemas, allowing it to retrieve and register tools as needed during its operations. This relationship is crucial as it enables the BaseAgent to leverage various tools for executing tasks, managing conversation history, and performing searches.

**Note**: It is essential to ensure that tools are properly registered before invoking them to avoid KeyErrors. Additionally, when registering tools, providing accurate descriptions and parameters will enhance the usability and clarity of the tool schemas.

**Output Example**: A possible appearance of the code's return value when invoking a registered tool might look like this:
```json
{
  "result": "Tool executed successfully.",
  "tool_name": "example_tool",
  "arguments": {
    "arg1": "value1",
    "arg2": "value2"
  }
}
```
### FunctionDef __init__(self)
**__init__**: The function of __init__ is to initialize an empty registry for storing tool schemas and associated callable functions.

**parameters**: This function does not accept any parameters.

**Code Description**: 
The `__init__` method is the constructor for the class it is a part of. It is responsible for initializing two attributes when an instance of the class is created:
1. **_tools**: A dictionary that is intended to store tool schemas. Each entry in this dictionary maps a tool's name (as a string) to its corresponding schema, which is stored as a dictionary.
2. **_funcs**: A dictionary that holds callable functions. Each entry in this dictionary maps a tool's name (as a string) to its associated callable function.

These attributes, `_tools` and `_funcs`, are both initialized as empty dictionaries. The `_tools` dictionary will later store mappings between tool names and their schemas, and the `_funcs` dictionary will store mappings between tool names and their callable functions.

**Note**: 
- The method does not take any parameters as it only sets up the initial state of the class instance.
- The two dictionaries, `_tools` and `_funcs`, are essential for the subsequent operation of the class, which likely involves storing and managing tool-related information and callable functions.

***
### FunctionDef get_or_create_tool_schema(self)
## `get_or_create_tool_schema` Function Documentation

### Description

The `get_or_create_tool_schema` function is responsible for retrieving or creating tool schemas for one or more given functions. If a schema for a function is not already registered, the function will create a new schema using the `Tool.create_schema_from_function` method and add it to the registry. This ensures that the tool schema for each function is available for use within the system.

### Parameters

- `*target_functions` (`Callable`): One or more functions for which schemas are to be retrieved or created. Each function is expected to be callable.

### Returns

- `List[Dict]`: A list of dictionaries, each representing the schema corresponding to one of the provided functions. These schemas are either retrieved from the registry or newly created.

### Behavior

- For each function in the `target_functions` argument:
  1. The function's name is extracted.
  2. If the function’s schema is not already registered (i.e., not present in the internal `_tools` dictionary), a new schema is created using the `Tool.create_schema_from_function` method.
  3. The newly created schema is added to the `_tools` registry and the function is registered in the `_funcs` dictionary.
  4. A log message is generated indicating the creation of the new tool schema, using the `printer.log` method.
  5. The schema for the function is appended to the result list.

### Example Usage

```python
tool_registry.get_or_create_tool_schema(func1, func2)
```

In this example, the function `get_or_create_tool_schema` will retrieve or create schemas for the functions `func1` and `func2`. The corresponding schemas will be returned in a list.

### Notes

- The function relies on the internal `_tools` and `_funcs` dictionaries to manage the function schemas and their corresponding callable functions.
- If a schema already exists for a function, it will simply be retrieved from the `_tools` registry without modification.
***
### FunctionDef register_tool(self, name, func, description, parameters)
### Function Documentation: `register_tool`

#### Description:
The `register_tool` function is responsible for manually registering a tool (either a Function Call or an MCP) into a registry. It creates a structured schema for the tool and stores it alongside its corresponding function. This function is a critical part of the tool management system, ensuring that tools can be easily registered and accessed in a standardized format.

#### Arguments:
- **name** (`str`): The name of the MCP tool or function. This serves as the identifier for the tool in the registry.
- **func** (`Callable`): The Python function that implements the tool's logic. This function will be executed when the tool is called.
- **description** (`str`): A textual description of the tool's purpose or functionality.
- **parameters** (`Dict[str, Any]`, optional): A dictionary representing the JSON schema for the function's parameters. If not provided, the schema will be automatically generated from the function signature.

#### Returns:
- **schema** (`Dict[str, Any]`): A dictionary representing the tool schema, formatted according to the OpenAI function call/Tool standard. This schema includes the tool's name, description, parameters, and type.

#### Functionality:
1. **Schema Creation**: 
   If the `parameters` argument is not provided, the function utilizes the `Tool.create_schema_from_function` method to generate a schema from the provided function (`func`). If the `parameters` are supplied, a schema is manually constructed with the provided values for `name`, `description`, and `parameters`.
   
2. **Tool Registration**: 
   The function registers the created schema in the internal registry (`self._tools`) under the provided `name`. Additionally, the function itself is stored in `self._funcs` under the same `name`.

3. **Logging**: 
   A log message is generated to confirm the registration of the tool, including the tool's name and its schema.

#### Example Usage:
```python
def sample_tool_function(param1: int, param2: str):
    """A sample tool function."""
    return f"Received {param1} and {param2}"

tool_registry.register_tool(
    name="sample_tool",
    func=sample_tool_function,
    description="A sample tool function that demonstrates tool registration.",
    parameters=None
)
```

In the above example, the `register_tool` function registers a new tool named `sample_tool`. The tool's schema is automatically created from the `sample_tool_function` signature, and the tool is added to the registry.

#### Important Notes:
- If `parameters` are not provided, the function relies on the `Tool.create_schema_from_function` method to automatically generate the schema based on the function's signature and docstring.
- The logging feature provides visibility into the tool registration process, helping to track the tools registered in the system.
- It is important to ensure that the `func` provided is a valid Python callable function and that its signature is well-defined for proper schema generation.
***
### FunctionDef invoke_tool(self, name, arguments)
**invoke_tool**: The function of invoke_tool is to invoke a registered tool by name with provided arguments and return its result.

**parameters**: The parameters of this Function.
· name: A string representing the name of the tool to be invoked.
· arguments: A dictionary containing the arguments to be passed to the tool.

**Code Description**: The invoke_tool function is designed to execute a tool that has been previously registered within the ToolRegistry class. It first retrieves the function associated with the provided tool name from the internal dictionary `_funcs`. If the tool name does not exist in the registry, it raises a KeyError, indicating that the requested tool is not available. 

Once the function is retrieved, it is called with the unpacked arguments provided in the `arguments` dictionary. The function checks if the result of the function call is an awaitable (i.e., a coroutine). If it is, the function uses `asyncio.run()` to execute the coroutine synchronously and return the result. If the result is not awaitable, it simply returns the result directly.

This function is called within the `step` method of the WorkflowExecutor class. In this context, the `step` method processes an action that may involve invoking a tool. It extracts the tool's name and arguments from the action string, then calls `invoke_tool` to execute the tool and handle its output. The results of the tool invocation are formatted into XML and appended to the history for tracking purposes. If any exceptions occur during the tool invocation, they are caught, and an error message is returned in a structured format.

**Note**: It is important to ensure that the tool name provided to invoke_tool corresponds to a registered tool; otherwise, a KeyError will be raised. Additionally, the arguments must be structured correctly as a dictionary to avoid runtime errors.

**Output Example**: An example of a possible return value from invoke_tool could be a dictionary representing the result of the tool's execution, such as:
```json
{
    "status": "success",
    "data": {
        "result": "Tool executed successfully"
    }
}
```
***
