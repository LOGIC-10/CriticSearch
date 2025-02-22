from typing import Callable, Dict, List

from loguru import logger

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
        """
        self._tools: Dict[str, dict] = {}

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
                logger.debug(
                    f"Created tool schema for: {func_name}, schema: {self._tools[func_name]}"
                )

            schemas.append(self._tools[func_name])

        return schemas
