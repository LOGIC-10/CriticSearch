import inspect
from typing import Any, Dict, List, Optional

from griffe import Docstring, DocstringSectionKind
from pydantic import BaseModel, Field, create_model


class ToolCall(BaseModel):
    tool: str = Field(..., description="Name of the tool to be called")
    parameters: Dict = Field(..., description="Parameters for the tool call")
    reasoning: str = Field(..., description="Reasoning for using this tool")


class ToolResponse(BaseModel):
    result: Dict | List | str = Field(..., description="Result from the tool")
    error: Optional[str] = Field(None, description="Error message if tool call failed")


class ParameterProperty(BaseModel):
    type: str = Field(
        ..., description="The data type of the parameter (e.g., 'string')."
    )
    description: Optional[str] = Field(
        None, description="A description of the parameter."
    )


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
        fields = {}
        required = []

        for param_name, param in signature.parameters.items():
            param_type = param.annotation if param.annotation != inspect._empty else Any
            param_default = param.default if param.default != inspect._empty else ...

            # 从解析的参数部分提取描述
            param_description = None
            for param_info in parameters:
                if param_info.name == param_name:  # 使用属性访问
                    param_description = param_info.description
                    break

            # 定义字段
            fields[param_name] = (
                param_type,
                Field(
                    ... if param_default is ... else param_default,
                    description=param_description,
                ),
            )
            if param_default is ...:
                required.append(param_name)

        # 动态创建模型
        DynamicParameters = create_model("DynamicParameters", **fields)

        # 构建最终 JSON Schema
        properties = {}
        for field_name, field_info in DynamicParameters.model_fields.items():
            properties[field_name] = {
                "type": field_info.annotation.__name__,
                "description": field_info.description or f"The {field_name} parameter.",
            }

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
        return cls(type="function", function=function_schema).model_dump()


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
