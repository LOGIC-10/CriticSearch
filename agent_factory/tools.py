# agent_factory/tools.py
import requests
from PIL import Image
from io import BytesIO
import base64
import yaml
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Union, Optional
from pydantic import BaseModel, Field

class ToolCall(BaseModel):
    tool: str = Field(..., description="Name of the tool to be called")
    parameters: Dict = Field(..., description="Parameters for the tool call")
    reasoning: str = Field(..., description="Reasoning for using this tool")

class ToolResponse(BaseModel):
    result: Union[Dict, List, str] = Field(..., description="Result from the tool")
    error: Optional[str] = Field(None, description="Error message if tool call failed")

class WebScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def scrape(self, url: str, elements: Optional[List[str]] = None) -> Dict:
        """
        Scrape content from a webpage.
        
        Args:
            url: The URL to scrape
            elements: List of HTML elements to specifically target (e.g., ['p', 'h1', 'h2'])
                     If None, extracts main content automatically
        
        Returns:
            Dict containing scraped content and metadata
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(['script', 'style', 'meta', 'noscript']):
                script.decompose()
            
            # Extract content based on specified elements or automatic content detection
            if elements:
                content = ' '.join([elem.get_text(strip=True) 
                                  for tag in elements 
                                  for elem in soup.find_all(tag)])
            else:
                # Automatic main content detection
                main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|main|article'))
                if main_content:
                    content = main_content.get_text(strip=True)
                else:
                    # Fallback to extracting paragraphs
                    content = ' '.join([p.get_text(strip=True) for p in soup.find_all('p')])
            
            # Clean up the content
            content = re.sub(r'\s+', ' ', content).strip()
            
            return {
                'url': url,
                'title': soup.title.string if soup.title else None,
                'content': content[:5000],  # Limit content length
                'metadata': {
                    'length': len(content),
                    'elements_found': len(content.split())
                }
            }
            
        except Exception as e:
            return {'error': str(e)}

class SearchTool:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        
    def search(self, query: str, max_results: int = 3) -> Dict:
        """Perform a search using the local DuckDuckGo API."""
        try:
            query = query.replace(":", " ") # it seems that the : will break the local api
            response = requests.get(
                f"{self.base_url}/search",
                params={"q": query, "max_results": max_results}
            )
            response.raise_for_status()
            return {'results': response.json()["results"]}
        except Exception as e:
            return {"error": str(e)}

class ImageAnalyzer:
    def __init__(self, model="gpt-4o-mini"):
        self.model = model
        
    def analyze_image(self, image_data: str) -> Dict:
        """Analyze an image using the specified vision model."""
        try:
            # Convert image data to base64 if it's a URL or file path
            if isinstance(image_data, str):
                if image_data.startswith('http'):
                    response = requests.get(image_data)
                    image = Image.open(BytesIO(response.content))
                else:
                    image = Image.open(image_data)
                
                buffered = BytesIO()
                image.save(buffered, format="PNG")
                image_base64 = base64.b64encode(buffered.getvalue()).decode()
            else:
                image_base64 = image_data
                
            # TODO this is a stand in for later use
            return {
                "description": "Image analysis completed",
                "model_used": self.model,
                "image_format": "base64"
            }
        except Exception as e:
            return {"error": str(e)}

class ToolRegistry:
    def __init__(self):
        self.tools = {}
        
    def register_tool(self, name: str, func: callable, description: str, parameters: Dict):
        self.tools[name] = {
            "function": func,
            "description": description,
            "parameters": parameters
        }
        
    def get_tool(self, name: str) -> Optional[Dict]:
        return self.tools.get(name)
    
    def get_tool_specifications(self) -> Dict:
        return {
            name: {
                "description": tool["description"],
                "parameters": tool["parameters"]
            }
            for name, tool in self.tools.items()
        }
    
import inspect
from typing import Any, Dict, List, Optional

from griffe import Docstring, DocstringSectionKind
from pydantic import BaseModel, Field, create_model


class ParameterProperty(BaseModel):
    type: str = Field(..., description="The data type of the parameter (e.g., 'string').")
    description: Optional[str] = Field(None, description="A description of the parameter.")


class Parameters(BaseModel):
    type: str = Field("object", description="The type of the parameter object.")
    properties: Dict[str, ParameterProperty] = Field(
        ...,
        description="A dictionary where keys are parameter names and values are their properties."
    )
    required: List[str] = Field(
        ...,
        description="A list of required parameter names."
    )
    additionalProperties: bool = Field(
        False,
        description="Whether additional properties are allowed."
    )


class Function(BaseModel):
    name: str = Field(..., description="The name of the function.")
    description: str = Field(..., description="A description of what the function does.")
    parameters: Parameters = Field(..., description="The parameters schema for the function.")


class Tool(BaseModel):
    type: str = Field("function", description="The type of the tool, typically 'function'.")
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
                Field(... if param_default is ... else param_default, description=param_description),
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
                additionalProperties=False
            )
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

