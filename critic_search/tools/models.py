import inspect
from typing import Any, Dict, List, Optional, get_args, get_origin

from griffe import Docstring, DocstringSectionKind
from pydantic import BaseModel, Field, field_serializer


def get_list_type_annotation(param_type):
    """
    获取列表中元素的类型，用于构造 JSON Schema 的 items 字段。
    支持 List[str]、List[int] 等类型。
    """
    # 检查是否为泛型 List 类型
    if get_origin(param_type) is list or get_origin(param_type) is list:
        # 获取列表的元素类型
        args = get_args(param_type)
        if args and isinstance(args[0], type):
            return {"type": args[0].__name__}
    # 默认返回字符串类型（未明确指定类型时）
    return {"type": "string"}


def serialize_type(value: str) -> str:
    type_mapping = {
        "str": "string",
        "int": "integer",
        "float": "number",
        "bool": "boolean",
        "list": "array",
        "dict": "object",
        "None": "null",
    }
    return type_mapping.get(value.lower(), "null")


class Item(BaseModel):
    type: str = Field(..., description="The type of the list item")

    @field_serializer("type")
    def serialize_type(self, value: str, _info) -> str:
        return serialize_type(value)


class ParameterProperty(BaseModel):
    type: str = Field(..., description="The data type of the parameter.")
    description: Optional[str] = Field(
        None, description="A description of the parameter."
    )
    items: Optional[Item] = None

    @field_serializer("type")
    def serialize_type(self, value: str, _info) -> str:
        return serialize_type(value)


class Parameters(BaseModel):
    type: str = Field("object", description="The type of the parameter object.")
    properties: Dict[str, ParameterProperty] = Field(
        ...,
        description="A dictionary where keys are parameter names and values are their properties.",
    )
    required: List[str] = Field(..., description="A list of required parameter names.")
    additionalProperties: bool = Field(
        False, description="Whether additional properties are allowed."
    )


class Function(BaseModel):
    name: str = Field(..., description="The name of the function.")
    description: str = Field(
        ..., description="A description of what the function does."
    )
    parameters: Parameters = Field(
        ..., description="The parameters schema for the function."
    )


class Tool(BaseModel):
    type: str = Field(
        "function", description="The type of the tool, typically 'function'."
    )
    function: Function = Field(..., description="The function definition for the tool.")

    @classmethod
    def create_schema_from_function(cls, target_function):
        """Create a Tool schema from a target function."""

        # 提取函数名称和文档字符串
        func_name = target_function.__name__
        func_doc = inspect.getdoc(target_function) or "No description provided."

        # 解析文档字符串，生成 sections
        docstring = Docstring(func_doc)
        # NOTE: Only support  Google-style right now.
        sections = docstring.parse("google")

        # 提取描述信息
        description = ""
        parameters = []

        for section in sections:
            if section.kind == DocstringSectionKind.text:
                description = section.value.strip()
            elif section.kind == DocstringSectionKind.parameters:
                parameters = section.value

        # 提取参数信息
        signature = inspect.signature(target_function)
        required = []
        properties = {}

        for param_name, param in signature.parameters.items():
            param_type = param.annotation if param.annotation != inspect._empty else Any
            param_default = param.default if param.default != inspect._empty else ...

            # 从解析的参数部分提取描述
            param_description = None
            for param_info in parameters:
                if param_info.name == param_name:  # 使用属性访问
                    param_description = param_info.description
                    break

            if param_default is ...:
                required.append(param_name)

            properties[param_name] = {
                "type": param_type.__name__,
                "description": param_description or f"The {param_name} parameter.",
            }

            if get_origin(param_type) is list:
                properties[param_name]["items"] = get_list_type_annotation(param_type)

        # Build the final Function and Tool schema
        function_schema = Function(
            name=func_name,
            description=description,
            parameters=Parameters(
                type="object",
                properties=properties,
                required=required,
                additionalProperties=False,
            ),
        )
        return cls(type="function", function=function_schema).model_dump(
            exclude_none=True
        )


if __name__ == "__main__":

    def get_delivery_date(order_id: str, delivery_type: str = "standard"):
        """
        Get the delivery date for a customer's order.

        Parameters:
            order_id (str): The unique ID of the order.
            delivery_type (str): The type of delivery (e.g., standard or express).
        """
        pass

    tool_schema = Tool.create_schema_from_function(get_delivery_date)
    print(tool_schema)
