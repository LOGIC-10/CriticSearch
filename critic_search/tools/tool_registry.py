import inspect
import json
from typing import Callable, List

from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
)
from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam

from critic_search.log import colorize_message, logger

from .models import Tool


def register_tool_function(func: Callable):
    """
    Registers a function as a tool that can be invoked via tool calls.
    Adds a marker to indicate that this function is a tool.

    Args:
        func (Callable): The function to register as a tool.

    Returns:
        Callable: The original function, now marked as a tool.
    """
    original_func = inspect.unwrap(func)
    setattr(original_func, "_is_tool", True)  # Mark the function as a tool
    return func


class ToolRegistry:
    """
    A registry for managing tool functions. Allows retrieval of function
    schemas and executing tool calls dynamically.
    """

    @classmethod
    def get_function_schemas(cls) -> List[ChatCompletionToolParam]:
        """
        Retrieves the schemas for all registered tool functions.

        Returns:
            List[ChatCompletionToolParam]: A list of schemas representing
            the parameters for each registered tool function.
        """
        # Get all functions marked as tools
        functions = [
            member
            for _, member in inspect.getmembers(cls)
            if callable(member) and getattr(member, "_is_tool", False)
        ]

        # Create schemas for each tool function
        schemas = []
        for tool_function in functions:
            schema = Tool.create_schema_from_function(tool_function)
            schemas.append(schema)

        # Log the generated schemas
        colorize_message(
            message_title="Generated Tool Schemas", message_content=f"{schemas}"
        )

        return schemas

    @classmethod
    def execute_tool_call(cls, tool_call: ChatCompletionMessageToolCall):
        """
        Executes a tool function based on the provided tool call.

        Args:
            tool_call (ChatCompletionMessageToolCall): The tool call containing
            the function name and parameters to execute.

        Returns:
            The result of executing the function.
        """
        # Extract function name and arguments from the tool call
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        logger.success(f"Executing tool: {function_name} with arguments: {arguments}")

        # Retrieve the target function based on its name
        target_function = getattr(cls, function_name)

        # Execute the function and return the result
        result = target_function(**arguments)

        try:
            logger.info(
                f"Tool '{function_name}' executed successfully with result:\n{result}"
            )
        except ValueError:
            print(
                f"Tool '{function_name}' executed successfully with result:\n{result}"
            )

        return result
