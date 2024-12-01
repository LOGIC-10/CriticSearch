from typing import Callable, Dict

from loguru import logger

from .models import Tool


class ToolRegistry:
    """
    A simplified registry to manage tools, using function names as keys.

    This registry stores tool schemas by their function names, allowing registration,
    retrieval, removal, and listing of tools.
    """

    def __init__(self):
        # 存储函数名称和工具 schema 的映射
        self._tools: Dict[str, dict] = {}

    def register(self, *target_functions: Callable):
        """
        Register one or more functions as tools using their name as the key.

        Args:
            *target_functions (Callable): One or more functions to register.

        Raises:
            ValueError: If any function is already registered.
        """
        for target_function in target_functions:
            # 获取函数名称
            func_name = target_function.__name__

            # 如果工具已经注册，跳过
            if func_name in self._tools:
                continue

            # 创建工具的 schema
            tool_schema = Tool.create_schema_from_function(target_function)

            # 注册工具
            self._tools[func_name] = tool_schema
            logger.debug(f"Registered tool: {func_name}")

    def get_tool_schema(self, target_function: Callable) -> dict:
        """
        Retrieve a registered tool schema by function.

        Args:
            target_function (Callable): The function to retrieve the schema for.

        Raises:
            KeyError: If the tool is not registered.
        """
        func_name = target_function.__name__

        # 检查工具是否已注册
        if func_name not in self._tools:
            raise KeyError(f"Tool '{func_name}' is not registered.")

        # 返回工具的 schema
        return self._tools[func_name]

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
