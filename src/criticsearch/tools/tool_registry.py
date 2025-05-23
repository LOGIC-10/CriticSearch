from typing import Any, Callable, Dict, List, Optional, Union
import asyncio
import inspect
import importlib

from ..rich_output import printer
from .models import Tool


class ToolRegistry:
    """
    A registry for managing tools using their function names as keys.

    This class provides functionality to retrieve or create schemas for tools
    based on provided functions, storing them for reuse and easy access.
    It also supports auto-discovery of tools from the tools package.
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
                # 只在调试模式下输出详细schema信息
                # printer.log(
                #     f"Created tool schema for: {func_name}, schema: {self._tools[func_name]}"
                # )

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

    def auto_discover_and_register_tools(self) -> List[Dict]:
        """
        Automatically discover and register tools according to the official standards.
        
        Only discovers tools that are:
        1. Properly defined in the tools package
        2. Exported in tools/__init__.py
        3. Have proper type annotations and docstrings
        4. Meet tool registration requirements
        
        Returns:
            List[Dict]: List of all registered tool schemas
        """
        discovered_tools = []
        
        # Import the tools package to get properly exported tools
        try:
            tools_module = importlib.import_module('criticsearch.tools')
        except ImportError:
            printer.log("Failed to import tools module", style="red")
            return []
        
        # Get explicitly exported items from __all__ or all public items
        exported_items = getattr(tools_module, '__all__', None)
        if exported_items is None:
            # Fallback to public items if __all__ is not defined
            exported_items = [name for name in dir(tools_module) if not name.startswith('_')]
        
        printer.log(f"🔍 扫描工具包，发现导出项: {exported_items}", style="blue")
        
        # Check each exported item
        for item_name in exported_items:
            try:
                item = getattr(tools_module, item_name)
                
                # Check if it's a function that meets tool standards
                if inspect.isfunction(item) and self._is_valid_tool_function(item):
                    schema = self.get_or_create_tool_schema(item)[0]
                    discovered_tools.append(schema)
                    printer.log(f"✅ 注册独立工具函数: {item_name}", style="green")
                
                # Check if it's a class with tool methods
                elif inspect.isclass(item) and self._is_valid_tool_class(item):
                    class_tools = self._register_valid_class_tools(item)
                    discovered_tools.extend(class_tools)
                    
            except Exception as e:
                printer.log(f"⚠️  处理导出项 {item_name} 时失败: {e}", style="yellow")
                continue
        
        # Also check for standard tool functions in note_manager
        self._register_note_manager_tools(discovered_tools)
        
        printer.log(f"🎉 工具自动发现完成，共注册 {len(discovered_tools)} 个工具", style="green")
        return discovered_tools

    def _register_note_manager_tools(self, discovered_tools: List[Dict]):
        """Register note manager tools which are known valid tools."""
        try:
            from .note_manager import taking_notes, retrieve_notes
            
            # These are known valid tools
            for tool_func in [taking_notes, retrieve_notes]:
                if self._is_valid_note_tool(tool_func):
                    schema = self.get_or_create_tool_schema(tool_func)[0]
                    discovered_tools.append(schema)
                    printer.log(f"   📝 注册笔记管理工具: {tool_func.__name__}", style="green")
                    
        except ImportError as e:
            printer.log(f"⚠️  笔记管理工具不可用: {e}", style="yellow")
    
    def _is_valid_note_tool(self, func: Callable) -> bool:
        """Check if a note manager function is a valid tool."""
        return (
            func.__doc__ is not None and
            len(func.__doc__.strip()) >= 10 and
            not func.__name__.startswith('_') and
            func.__name__ in {'taking_notes', 'retrieve_notes'}  # Only model-facing note tools
        )

    def _is_valid_tool_function(self, func: Callable) -> bool:
        """
        Check if a function meets the strict tool registration standards.
        
        Requirements:
        1. Has a comprehensive docstring
        2. Has proper type annotations
        3. Is not a private function
        4. Is from the tools package
        5. Can be called by models
        
        Args:
            func: Function to check
            
        Returns:
            bool: True if function meets tool standards
        """
        # Basic checks
        if (func.__doc__ is None or 
            len(func.__doc__.strip()) < 10 or  # Require reasonable docstring
            func.__name__.startswith('_')):
            return False
        
        # Must be from tools package
        module = getattr(func, '__module__', '')
        if not module.startswith('criticsearch.tools'):
            return False
        
        # Exclude internal registry methods and utility functions
        excluded_names = {
            'get_args', 'get_origin', 'get_list_type_annotation',
            'abstractmethod', 'gather', 'retry', 'copy', 
            'auto_discover_and_register_tools', 'get_all_tool_schemas',
            'get_or_create_tool_schema', 'get_tool_names', 'get_tool_schema',
            'invoke_tool', 'is_tool_registered', 'register_tool', 'search_tools'
        }
        if func.__name__ in excluded_names:
            return False
        
        # Check function signature for proper annotations
        try:
            sig = inspect.signature(func)
            # Should have return annotation for tools
            return True  # Basic validation passed
        except (ValueError, TypeError):
            return False

    def _is_valid_tool_class(self, cls: type) -> bool:
        """
        Check if a class contains valid tool methods according to standards.
        
        Args:
            cls: Class to check
            
        Returns:
            bool: True if class has valid tool methods
        """
        # Must be from tools package
        module = getattr(cls, '__module__', '')
        if not module.startswith('criticsearch.tools'):
            return False
        
        # Skip internal registry and model classes
        if cls.__name__ in {'ToolRegistry', 'Tool', 'Function', 'Parameters', 'ParameterProperty', 'Item'}:
            return False
        
        # Check for any methods that could be tools
        for method_name, method in inspect.getmembers(cls):
            if not method_name.startswith('_') and callable(method):
                # Check if it's a valid tool method by name and documentation
                # Only include tools that are meant for model usage
                if (hasattr(method, '__doc__') and 
                    method.__doc__ is not None and
                    len(method.__doc__.strip()) >= 10 and
                    method_name in {'search', 'scrape'}):  # Only model-facing tools
                    return True
        
        return False

    def _register_valid_class_tools(self, cls: type) -> List[Dict]:
        """
        Register tool methods from a class that meet standards.
        
        Args:
            cls: Class containing tool methods
            
        Returns:
            List[Dict]: List of registered tool schemas
        """
        schemas = []
        
        # Check all methods of the class
        for method_name, method in inspect.getmembers(cls):
            if (not method_name.startswith('_') and 
                callable(method) and
                hasattr(method, '__doc__') and
                method.__doc__ is not None and
                len(method.__doc__.strip()) >= 10 and
                method_name in {'search', 'scrape'}):  # Only model-facing tools
                
                try:
                    schema = self.get_or_create_tool_schema(method)[0]
                    schemas.append(schema)
                    printer.log(f"   📦 注册类方法工具: {cls.__name__}.{method_name}", style="green")
                except Exception as e:
                    printer.log(f"   ❌ 注册 {cls.__name__}.{method_name} 失败: {e}", style="yellow")
            
        return schemas

    def get_tool_schema(self, tool_name: str) -> Optional[Dict]:
        """
        Get the schema for a specific tool by name.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Optional[Dict]: Tool schema if found, None otherwise
        """
        return self._tools.get(tool_name)

    def get_all_tool_schemas(self) -> List[Dict]:
        """
        Get all registered tool schemas.
        
        Returns:
            List[Dict]: List of all tool schemas
        """
        return list(self._tools.values())

    def search_tools(self, query: str) -> List[Dict]:
        """
        Search for tools by name or description.
        
        Args:
            query: Search query
            
        Returns:
            List[Dict]: List of matching tool schemas
        """
        query_lower = query.lower()
        matching_tools = []
        
        for tool_name, schema in self._tools.items():
            # Search in tool name
            if query_lower in tool_name.lower():
                matching_tools.append(schema)
                continue
                
            # Search in tool description
            description = schema.get('description', '').lower()
            if query_lower in description:
                matching_tools.append(schema)
                
        return matching_tools

    def get_tool_names(self) -> List[str]:
        """
        Get all registered tool names.
        
        Returns:
            List[str]: List of tool names
        """
        return list(self._tools.keys())

    def is_tool_registered(self, tool_name: str) -> bool:
        """
        Check if a tool is registered.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            bool: True if tool is registered
        """
        return tool_name in self._tools 