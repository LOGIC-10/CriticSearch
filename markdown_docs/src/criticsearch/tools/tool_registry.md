## ClassDef ToolRegistry
**ToolRegistry**: The function of ToolRegistry is to manage tools by using their function names as keys, allowing easy retrieval and creation of schemas for those tools.

**Attributes**:
- **_tools**: A dictionary that maps function names (as strings) to their respective tool schemas. It is initialized as an empty dictionary and is used to store the schemas of tools for quick access and reuse.

**Code Description**:  
The `ToolRegistry` class is designed to manage the registration and retrieval of tool schemas based on function names. It allows the creation of new schemas for tools if they are not already registered. The primary use case of this class is within systems that work with a variety of tools, where each tool is associated with a function, and its schema needs to be retrieved or generated.

- **`__init__`**: This method initializes an empty registry (`_tools`) for storing tool schemas. The registry is a dictionary where keys are the names of functions (as strings) and values are the schemas related to those functions. The class starts with no schemas stored.

- **`get_or_create_tool_schema`**: This method accepts one or more function references (`target_functions`) as arguments. For each function provided, it checks whether the schema for that function already exists in the `_tools` dictionary. If a schema does not exist for the function, the method creates it using a class method `Tool.create_schema_from_function` and then stores it in the `_tools` dictionary. After the schema is retrieved or created, it is added to a list and returned. This method ensures that schemas are not repeatedly created for the same functions, promoting efficiency and reuse.

    - **Arguments**:
      - `*target_functions`: One or more functions whose schemas need to be retrieved or created.
    - **Returns**: A list of dictionaries representing the schemas of the provided functions.

In the context of the larger project, the `ToolRegistry` class is used in the `BaseAgent` class (found in `src/criticsearch/base_agent.py`). Specifically, instances of `ToolRegistry` are used to manage the schemas for different tools within the agent, such as `search_aggregator` and `content_scraper`. When initializing these tools, `BaseAgent` calls `get_or_create_tool_schema` to retrieve or create the schemas associated with their functions. These schemas are essential for the tools to be correctly used in subsequent operations, such as when the agent interacts with external services or processes data.

The `ToolRegistry` class plays a crucial role in ensuring that the agent can consistently access the correct schema for its tools, avoiding the need to repeatedly recreate schemas and thus improving efficiency.

**Note**:  
- The `Tool.create_schema_from_function` method (referenced in `get_or_create_tool_schema`) is expected to be responsible for creating a schema from a function. This method should handle the specifics of schema creation and may include validation or other processing steps.
- The `_tools` dictionary is managed entirely within the `ToolRegistry` class. Users of this class do not need to directly modify this attribute.
- This class assumes that function names are unique and can be used as reliable keys for storing schemas.

**Output Example**:  
When calling `get_or_create_tool_schema` with the `search` function of `search_aggregator` and the `scrape` function of `content_scraper`, a possible return value could look like this:

```python
[
    {
        "function_name": "search",
        "schema_details": { ... }  # Detailed schema information for the 'search' function
    },
    {
        "function_name": "scrape",
        "schema_details": { ... }  # Detailed schema information for the 'scrape' function
    }
]
```
### FunctionDef __init__(self)
**__init__**: The function of __init__ is to initialize an empty registry for storing tool schemas.

**parameters**: The parameters of this Function.
· There are no parameters for this function.

**Code Description**: The __init__ function is a constructor method that is called when an instance of the ToolRegistry class is created. This function initializes an instance variable named _tools, which is a dictionary. The purpose of this dictionary is to map function names (as strings) to their respective schemas (as dictionaries). By initializing _tools as an empty dictionary, the function sets up a clean state for the ToolRegistry instance, allowing it to store tool schemas that can be added later. This design ensures that the registry starts without any pre-existing data, providing a fresh environment for subsequent operations.

**Note**: It is important to understand that this function does not take any parameters and does not return any value. It solely serves the purpose of setting up the initial state of the ToolRegistry instance. Users should ensure that the _tools dictionary is populated with valid tool schemas through other methods provided in the ToolRegistry class after the instance is initialized.
***
### FunctionDef get_or_create_tool_schema(self)
**get_or_create_tool_schema**: The function of get_or_create_tool_schema is to retrieve or create tool schemas for specified functions.

**parameters**: The parameters of this Function.
· target_functions: One or more functions for which schemas are to be retrieved or created.

**Code Description**: The get_or_create_tool_schema method is a member of the ToolRegistry class, responsible for managing the schemas associated with various tools (functions) within the application. This method accepts one or more callable functions as arguments and checks if a schema for each function is already registered in the internal registry (self._tools). 

If a function's schema is not found, the method invokes the Tool class's create_schema_from_function method to generate a new schema based on the function's metadata, including its name, description, and parameters. This newly created schema is then stored in the registry for future reference. The method logs the creation of the schema for debugging purposes.

The method returns a list of schemas corresponding to the provided functions, ensuring that all requested schemas are either retrieved from the registry or newly created. This functionality is crucial for maintaining a structured representation of functions within the application, allowing for consistent access to their metadata.

The get_or_create_tool_schema method is called within the __init__ method of the BaseAgent class. During the initialization of a BaseAgent instance, it retrieves or creates schemas for the search aggregator and content scraper tools. These schemas are then stored in the conversation manager's available tools, facilitating their use in subsequent interactions.

**Note**: When using this method, ensure that the functions passed as arguments are callable and properly defined, as the method relies on their metadata to generate the schemas.

**Output Example**: A possible appearance of the code's return value when invoking get_or_create_tool_schema might look like this:
```json
[
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": "Performs a search operation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "str",
                        "description": "The search query."
                    },
                    "limit": {
                        "type": "int",
                        "description": "The maximum number of results to return."
                    }
                },
                "required": ["query"],
                "additionalProperties": false
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scrape",
            "description": "Scrapes content from a given URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "str",
                        "description": "The URL to scrape."
                    }
                },
                "required": ["url"],
                "additionalProperties": false
            }
        }
    }
]
```
***
