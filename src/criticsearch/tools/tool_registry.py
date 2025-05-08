from typing import Any, Callable, Dict, List
import asyncio
import inspect

from ..rich_output import printer
from .models import Tool


class ToolRegistry:
    """
    A registry for managing tools using their function names as keys.

    This class provides functionality to retrieve or create schemas for tools
    based on provided functions, storing them for reuse and easy access.
    """

    def __init__(self):
        """
        Initialize an empty registry for storing tool schemas.

        Attributes:
            _tools (Dict[str, dict]): A dictionary mapping function names
                                      to their respective schemas.
            _funcs (Dict[str, Callable]): A dictionary mapping function names
                                          to their actual callable functions.
        """
        self._tools: Dict[str, dict] = {}
        self._funcs: Dict[str, Callable] = {}

    def get_or_create_tool_schema(self, *target_functions: Callable) -> List[Dict]:
        """
        Retrieve or create tool schemas for the given functions.

        If a function's schema is not already registered, it will be created
        using `Tool.create_schema_from_function` and added to the registry.

        Args:
            *target_functions (Callable): One or more functions for which
                                          schemas are to be retrieved or created.

        Returns:
            List[Dict]: A list of schemas corresponding to the provided functions.
        """
        schemas = []
        for target_function in target_functions:
            func_name = target_function.__name__

            # Create schema if not already registered
            if func_name not in self._tools:
                self._tools[func_name] = Tool.create_schema_from_function(
                    target_function
                )
                self._funcs[func_name] = target_function
                printer.log(
                    f"Created tool schema for: {func_name}, schema: {self._tools[func_name]}"
                )

            schemas.append(self._tools[func_name])

        return schemas


    def register_tool(
        self,
        name: str,
        func: Callable,
        description: str,
        parameters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        手动注册一个工具（Function Call 或 MCP）。
        Args:
            name: MCP 工具名或函数名
            func: 实际执行该工具的 Python 函数
            description: 工具描述
            parameters: 可选，函数参数 JSON Schema，若不传则自动从 func 签名生成
        Returns:
            schema: 一个符合 OpenAI function call/Tool 格式的 dict
        """
        # 创建 schema
        if parameters is None:
            schema = Tool.create_schema_from_function(func)
        else:
            schema = {
                "name": name,
                "description": description,
                "parameters": parameters,
                "type": "function"
            }
        # 存入注册表
        self._tools[name] = schema
        self._funcs[name] = func
        printer.log(f"Registered tool: {name}, schema: {schema}")
        return schema
    
    def invoke_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """
        Invoke a registered tool by name with provided arguments and return its result.
        """
        func = self._funcs.get(name)
        if func is None:
            raise KeyError(f"No such tool registered: {name}")
        # Call the tool; if it returns an awaitable, run it synchronously
        result = func(**arguments)
        if inspect.isawaitable(result):
            return asyncio.run(result)
        return result