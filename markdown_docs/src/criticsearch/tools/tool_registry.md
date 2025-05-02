## ClassDef ToolRegistry
# ToolRegistry Class Documentation

## Overview

The `ToolRegistry` class is designed to manage a collection of tools using their function names as keys. It allows for efficient retrieval and creation of tool schemas, supporting seamless tool management by providing methods to register new tools and retrieve or create schemas for existing ones. This registry facilitates easy access and reuse of tools in different contexts.

## Attributes

- **_tools** (`Dict[str, dict]`): A dictionary that stores tool schemas, where the keys are function names (as strings) and the values are the corresponding schemas. This registry helps track and manage tool schemas for various functions.

## Methods

### `__init__(self) -> None`
Initializes an empty registry for storing tool schemas.

- **Description**: This method sets up the initial state of the `ToolRegistry` class by creating an empty dictionary to hold the tool schemas. Each tool is stored with its function name as the key.

- **Attributes**: 
  - `_tools`: An empty dictionary that will later store tool schemas.

---

### `get_or_create_tool_schema(self, *target_functions: Callable) -> List[Dict]`
Retrieves or creates tool schemas for the given functions.

- **Arguments**:
  - `*target_functions` (`Callable`): One or more functions for which schemas are to be retrieved or created.

- **Returns**:
  - `List[Dict]`: A list of schemas corresponding to the provided functions. If a schema does not exist for a function, it will be created and added to the registry.

- **Description**: This method checks if the schema for a given function is already registered. If the schema is not found, it will use the `Tool.create_schema_from_function` method to generate and register a new schema. The resulting schemas are then returned in a list.

---

### `register_tool(self, name: str, func: Callable, description: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]`
Manually registers a new tool with its associated function and schema.

- **Arguments**:
  - `name` (`str`): The name of the tool (either the function name or an identifier for a function call).
  - `func` (`Callable`): The actual Python function that performs the tool's task.
  - `description` (`str`): A description of the tool's functionality.
  - `parameters` (`Dict[str, Any]`, optional): A dictionary representing the function's parameters in JSON schema format. If not provided, it will be automatically generated from the function's signature.

- **Returns**:
  - `Dict[str, Any]`: The schema of the registered tool, in a format compatible with OpenAI function calls or tool specifications.

- **Description**: This method allows for the manual registration of a tool in the registry. It creates a schema for the provided function (either from the function's signature or the provided parameters) and adds it to the `_tools` registry. The schema is then returned for use in the system.

---

## Usage Example

```python
tool_registry = ToolRegistry()

# Register a tool manually
def sample_function(param1: str, param2: int):
    return f"Received {param1} and {param2}"

tool_schema = tool_registry.register_tool(
    name="sample_tool",
    func=sample_function,
    description="A sample tool for demonstration purposes"
)

# Retrieve or create schemas for a function
schemas = tool_registry.get_or_create_tool_schema(sample_function)
```

## Conclusion

The `ToolRegistry` class provides an essential service for managing and organizing tool schemas within an application. By supporting the automatic creation and retrieval of tool schemas, as well as manual registration, it simplifies the integration and management of various tools in a consistent manner.
### FunctionDef __init__(self)
**__init__**: The function of __init__ is to initialize an empty registry for storing tool schemas.

**parameters**: The parameters of this Function.
· There are no parameters for this function.

**Code Description**: The __init__ function is a constructor method that is called when an instance of the ToolRegistry class is created. This function initializes an instance variable named _tools, which is a dictionary. The purpose of this dictionary is to map function names (as strings) to their respective schemas (as dictionaries). By initializing _tools as an empty dictionary, the function sets up a clean state for the ToolRegistry instance, allowing it to store tool schemas that can be added later. This design ensures that the registry starts without any pre-existing data, providing a fresh environment for subsequent operations.

**Note**: It is important to understand that this function does not take any parameters and does not return any value. It solely serves the purpose of setting up the initial state of the ToolRegistry instance. Users should ensure that the _tools dictionary is populated with valid tool schemas through other methods provided in the ToolRegistry class after the instance is initialized.
***
### FunctionDef get_or_create_tool_schema(self)
## Method: `get_or_create_tool_schema`

### Description:
The `get_or_create_tool_schema` method retrieves or creates tool schemas for the given functions. If the schema for a function is not already registered, it will be created using the `Tool.create_schema_from_function` method and added to the registry. This ensures that the necessary tool schemas are available for the provided functions.

### Parameters:
- `*target_functions` (Callable): One or more functions for which schemas are to be retrieved or created. The parameter accepts a variable number of function arguments.

### Returns:
- `List[Dict]`: A list of schemas corresponding to the provided functions. Each schema is returned as a dictionary.

### Behavior:
1. The method iterates through each provided function in `target_functions`.
2. For each function, it checks if its schema already exists in the registry (using the function's name).
3. If the schema is not registered:
   - The schema is created by calling `Tool.create_schema_from_function` with the target function.
   - The schema is added to the registry.
   - A log message is printed indicating the creation of the schema.
4. Finally, the method returns a list of schemas corresponding to the provided functions, whether they were newly created or retrieved from the registry.

### Example Usage:
```python
tool_registry = ToolRegistry()
schemas = tool_registry.get_or_create_tool_schema(function1, function2)
```

### Notes:
- The method leverages the `Tool.create_schema_from_function` to generate the schema when necessary.
- Logging of schema creation is handled by the `printer.log` function, providing feedback on the schema creation process.
***
### FunctionDef register_tool(self, name, func, description, parameters)
**register_tool**: The function of register_tool is to manually register a tool (Function Call or MCP) by providing its name, execution function, description, and optional parameters.

**parameters**: The parameters of this Function.
· name: A string representing the name of the MCP tool or function.  
· func: A Callable that is the actual Python function executing the tool.  
· description: A string that describes the tool.  
· parameters: An optional dictionary representing the function parameters in JSON Schema format. If not provided, it will be automatically generated from the func signature.

**Code Description**: The register_tool function is designed to facilitate the manual registration of tools within the ToolRegistry class. It accepts four parameters: `name`, `func`, `description`, and an optional `parameters`. The primary purpose of this function is to create a structured schema for the tool being registered.

When the function is called, it first checks if the `parameters` argument is provided. If it is not provided, the function utilizes the `Tool.create_schema_from_function(func)` method to generate a schema based on the provided function's signature and documentation. This method extracts the function's name, description, and parameter details, ensuring that the schema is comprehensive and accurately reflects the function's capabilities.

If the `parameters` argument is supplied, the function constructs a schema dictionary that includes the `name`, `description`, and the provided `parameters`, along with a type set to "function". This structured schema is then stored in the `_tools` dictionary of the ToolRegistry instance, using the `name` as the key.

The function also logs the registration process using the `printer.log` method, which outputs a styled log message to the console, indicating that the tool has been successfully registered along with its schema. This logging is crucial for tracking the registration of tools and ensuring that developers can monitor the tools available within the registry.

Finally, the function returns the constructed schema, which is formatted to comply with the OpenAI function call/Tool format. This return value can be utilized by other components of the system that require access to the registered tool's metadata.

**Note**: It is important to ensure that the `func` parameter is a well-defined Python function with appropriate documentation, as the schema generation relies on the function's signature and docstring. Additionally, the `name` parameter must be unique within the ToolRegistry to avoid overwriting existing tool registrations.

**Output Example**: A possible return value from the register_tool function might look like this:
```json
{
  "name": "example_tool",
  "description": "This tool serves as an example.",
  "parameters": {
    "type": "object",
    "properties": {
      "param1": {
        "type": "int",
        "description": "An integer parameter."
      },
      "param2": {
        "type": "str",
        "description": "A string parameter."
      }
    },
    "required": ["param1"],
    "additionalProperties": false
  },
  "type": "function"
}
```
***
