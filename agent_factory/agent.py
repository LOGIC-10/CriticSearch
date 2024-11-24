# import os
# from autogen import AssistantAgent, UserProxyAgent
# from autogen import ConversableAgent
# from config import read_config

# config = read_config()
# model = config.get('default_model',"gpt-4o-mini")
# api_key = config.get("models").get(model).get("api_key")
# base_url = config.get("models").get(model).get("base_url")

# llm_config = { "config_list": [{ "model": model, "api_key": api_key }], "base_url": base_url}


# # 定义一个critic agent
# critic_agent = ConversableAgent(
#     "CriticAgent",
#     system_message="Your name is Cathy and you are a part of a duo of comedians.",
#     llm_config=llm_config,
#     human_input_mode="NEVER",  # Never ask for human input.
# )

# # 填充prompt模板内容   

# # 使用 critic agent 生成回复
# critic_agent_reply = critic_agent.generate_reply(messages=[{"content": "Tell me a joke.", "role": "user"}])
# print(critic_agent_reply)

# agent_factory/agent.py
import re
from typing import Dict, List
import yaml
from config import read_config
import os
from jinja2 import Environment, FileSystemLoader
from utils import call_llm
from tools import (
    ToolRegistry, SearchTool, ImageAnalyzer, WebScraper,
    ToolCall, ToolResponse
)

class BaseAgent:
    def __init__(self):
        self.config = read_config()
        self.model = self.config.get('default_model', "gpt-4o-mini")
        self.env = Environment(loader=FileSystemLoader(self.config.get('prompt_folder_path')))
        self.tool_registry = ToolRegistry()
        self._register_default_tools()
        self._setup_prompts()
        
    def _register_default_tools(self):
        """Register the default tools available to the agent."""
        # Register search tool
        search_tool = SearchTool()
        self.tool_registry.register_tool(
            "search",
            search_tool.search,
            "Search for information using DuckDuckGo",
            {
                "query": "str: The search query",
                "max_results": "int: Maximum number of results (default: 3)"
            }
        )
        
        # Register web scraper
        web_scraper = WebScraper()
        self.tool_registry.register_tool(
            "scrape_webpage",
            web_scraper.scrape,
            "Scrape content from a webpage",
            {
                "url": "str: The URL to scrape",
                "elements": "Optional[List[str]]: Specific HTML elements to target"
            }
        )
        
        # Register image analyzer #TODO
        # image_analyzer = ImageAnalyzer(model=self.model)
        # self.tool_registry.register_tool(
        #     "analyze_image",
        #     image_analyzer.analyze_image,
        #     "Analyze an image using vision model",
        #     {
        #         "image_data": "str: URL or base64-encoded image data"
        #     }
        # )
    
    def _setup_prompts(self):
        """Set up system and tool prompts."""
        tool_specs = self.tool_registry.get_tool_specifications()
        
        self.sys_prompt = f"""You are an AI assistant with access to various tools.
Available tools and their specifications:

{yaml.dump(tool_specs, default_flow_style=False)}

When you need to use a tool, respond with YAML in the following format:
```yaml
tool_calls:
  - tool: <tool_name>
    parameters:
      parameter1: value1
      parameter2: value2
    reasoning: <why you're using this tool>
```

Multiple tool calls can be specified in sequence if needed."""

    def parse_tool_calls(self, response: str) -> List[ToolCall]:
        """Parse tool calls from the response."""
        try:
            # Extract YAML between ```yaml and ``` markers
            yaml_match = re.search(r'```yaml\n(.*?)```', response, re.DOTALL)
            if not yaml_match:
                return []
            
            yaml_content = yaml_match.group(1)
            parsed = yaml.safe_load(yaml_content)
            
            if not parsed or 'tool_calls' not in parsed:
                return []
            
            return [ToolCall(**call) for call in parsed['tool_calls']]
            
        except Exception as e:
            print(f"Error parsing tool calls: {e}")
            return []
    
    def execute_tool_calls(self, tool_calls: List[ToolCall]) -> List[ToolResponse]:
        """Execute a sequence of tool calls."""
        responses = []
        
        for call in tool_calls:
            tool = self.tool_registry.get_tool(call.tool)
            if not tool:
                responses.append(ToolResponse(
                    result={},
                    error=f"Tool '{call.tool}' not found"
                ))
                continue
            
            try:
                result = tool["function"](**call.parameters)
                responses.append(ToolResponse(result=result))
            except Exception as e:
                responses.append(ToolResponse(
                    result={},
                    error=f"Error executing {call.tool}: {str(e)}"
                ))
        
        return responses
    
    def common_chat(self, query: str) -> str:
        """Enhanced chat method with tool calling capabilities."""
        # First, get potential tool calls from the model
        tool_response = call_llm(
            model=self.model,
            sys_prompt=self.sys_prompt,
            usr_prompt=f"Query: {query}\n\nDetermine if any tools are needed to answer this query. If so, specify the tool calls in YAML format.",
            config=self.config
        )
        
        # Parse and execute tool calls
        tool_calls = self.parse_tool_calls(tool_response)
        print(tool_calls)
        tool_results = []
        
        if tool_calls:
            tool_responses = self.execute_tool_calls(tool_calls)
            tool_results = [
                f"Tool '{call.tool}' results (called because {call.reasoning}):\n{response.result if not response.error else f'Error: {response.error}'}"
                for call, response in zip(tool_calls, tool_responses)
            ]
            print(tool_results)
        
        # Generate final response with tool results
        final_prompt = f"""Query: {query}

Tool results:
{yaml.dump({'tool_results': tool_results}, default_flow_style=False) if tool_results else 'No tools were used.'}

Please provide a comprehensive response based on the available information."""
        
        return call_llm(
            model=self.model,
            sys_prompt=self.sys_prompt,
            usr_prompt=final_prompt,
            config=self.config
        )
    
    def chat_with_template(self, data: Dict, prompt_template) -> str:
        """Generic chat method that adapts different prompts based on the input data dictionary."""
        rendered_prompt = prompt_template.render(**data)
        return self.common_chat(query=rendered_prompt)
    
    def receive_task(self, task: str):
        """Receive the original task."""
        self.original_task = task

# Example usage
if __name__ == "__main__":
    agent = BaseAgent()
    response = agent.common_chat(
        "What is apple's most recent quarterly revenue figure?"
    )
    print(response)
    response = agent.common_chat("How old is apple according to this wikipedia link? 'https://en.wikipedia.org/wiki/Outline_of_Apple_Inc.'")
    print(response)