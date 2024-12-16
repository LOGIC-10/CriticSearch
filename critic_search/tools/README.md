## Adding New Tools

To add a new tool to the `Toolbox`, follow these steps:

1. **Define the Tool Function**:
    - Create a static method that performs the desired operation. The function should have an appropriate signature specifying the parameters it requires. Static methods are used so that the functions can be called without needing an instance of the class.

2. **Register the Function**:
    - Use the `@register_tool_function` decorator to register the function as a tool. This marks the function so that the `ToolRegistry` can automatically generate a schema for it.

3. **Return the Result**:
    - Inside the function, perform the operation (e.g., a search, scraping) and return the result.

### Example: Adding a Tool for Data Transformation

Here’s an example of how you could add a new tool to the toolbox that transforms a list of numbers by multiplying them by a given factor:

```python
@staticmethod
@register_tool_function
def transform_numbers(numbers: List[int], factor: int):
    """
    Transforms the list of numbers by multiplying each by the given factor.

    Args:
        numbers (List[int]): A list of numbers to transform.
        factor (int): The factor to multiply each number by.
    """
    return [number * factor for number in numbers]
```

## Automatic Schema Handling

The `ToolRegistry` automatically handles the creation of schemas for the registered tool functions. When you add a new tool using the `@register_tool_function decorator`, the `ToolRegistry` will generate the corresponding schema based on the function’s parameters. This schema is used for validation and when executing the tool programmatically.

Example: Tool Schema
For the perform_search function, the schema might look something like this:

```json
{
  "name": "perform_search",
  "parameters": [
    {
      "name": "query",
      "type": "list",
      "items": {
        "type": "string"
      }
    }
  ]
}
```

This schema defines the function's name and the type of its parameters, helping to ensure that the correct data is passed when the tool is called.

## Tool Execution Flow

When a tool is executed, the `ToolRegistry` takes care of retrieving the correct function based on the tool call and its parameters. The tool is executed, and the result is returned to the caller.

Example Execution:
To execute a tool, you can pass a ToolCall object, which contains the function name and arguments. The ToolRegistry will handle the process of identifying the correct function and executing it.

```python
tool_call = {
    "function": "perform_search",
    "arguments": {"query": ["Python programming", "AsyncIO in Python"]}
}

result = Toolbox.execute_tool_call(tool_call)
print(result)
```

In this example, the ToolRegistry automatically invokes the perform_search function with the specified query and returns the search results.