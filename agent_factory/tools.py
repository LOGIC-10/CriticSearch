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