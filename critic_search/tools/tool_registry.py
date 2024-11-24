from typing import Callable, Dict

from .models import Tool


class ToolRegistry:
    """
    A simplified registry to manage tools.

    This registry stores tool schemas by their names, allowing registration,
    retrieval, removal, and listing of tools.
    """

    def __init__(self):
        self._tools: Dict[str, dict] = {}

    def register(self, *target_functions: Callable):
        """
        Register one or more functions as tools.

        Args:
            *target_functions (Callable): One or more functions to register.

        Raises:
            ValueError: If any function is already registered.
        """
        for target_function in target_functions:
            tool_schema = Tool.create_schema_from_function(target_function)
            tool_name = tool_schema["function"]["name"]

            if tool_name in self._tools:
                raise ValueError(f"Tool '{tool_name}' is already registered.")

            self._tools[tool_name] = tool_schema
            print(f"Registered tool: {tool_name}")

    def get_tool_schema(self, tool_name: str) -> dict:
        """
        Retrieve a registered tool schema by name.
        """
        if tool_name not in self._tools:
            raise KeyError(f"Tool '{tool_name}' is not registered.")
        return self._tools[tool_name]

    def unregister(self, tool_name: str):
        """
        Unregister a tool by name.

        Args:
            tool_name (str): The name of the tool.

        Raises:
            KeyError: If the tool is not registered.
        """
        if tool_name not in self._tools:
            raise KeyError(f"Tool '{tool_name}' is not registered.")
        del self._tools[tool_name]
        print(f"Unregistered tool: {tool_name}")

    def list_tools(self) -> Dict[str, dict]:
        """
        List all registered tools.

        Returns:
            Dict[str, dict]: A dictionary of all registered tools.
        """
        return self._tools
