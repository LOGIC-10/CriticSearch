import asyncio
import json
import os
import re
import time
from typing import Dict, List, Optional, overload

import yaml

# from jinja2 import Environment, FileSystemLoader
from jinja2 import Template

from .config import settings
from .llm_service import ChatCompletionMessage, call_llm
from .models import ConversationManager
from .rich_output import printer
from .tools import ContentScraper, SearchAggregator, ToolRegistry, Tool
from .tools.note_manager import taking_notes as note_save, retrieve_notes as note_retrieve
from .utils import *

class BaseAgent:
    # Class-level attributes, shared across all instances
    queryDB = set()  # A set to store queries
    tool_registry = ToolRegistry()  # Registry for tools
    search_aggregator = SearchAggregator()
    user_question = ""
    training_data = []
    conversation_manager = ConversationManager()
    memo = set()  # A set to store the gist extracted from the search results
    available_tools = []  # 工具列表移到BaseAgent作为直接属性

    def __init__(self, auto_discover_tools: bool = True):
        base_dir = os.path.dirname(
            os.path.abspath(__file__)
        )  # Directory of the current script
        self.prompts_dir = os.path.join(base_dir, "prompts")
        self.config = settings  # 添加配置访问支持
        # self.env = Environment(loader=FileSystemLoader(self.prompts_dir))
        # Initialize tool instances for backward compatibility
        self.search_aggregator = SearchAggregator()
        self.content_scraper = ContentScraper()

        if auto_discover_tools:
            # Automatically discover and register all tools
            self._auto_setup_tools()
        else:
            # Legacy manual setup for backward compatibility
            self._manual_setup_tools()

    def _auto_setup_tools(self):
        """
        Automatically discover and register all available tools.
        """
        # Auto-discover tools from the tools package
        discovered_schemas = BaseAgent.tool_registry.auto_discover_and_register_tools()
        
        # Set all discovered tools as available
        BaseAgent.available_tools = discovered_schemas
        
        # Cache commonly used tool schemas for backward compatibility
        # For instance methods, we need to use the actual instance methods
        self.search_aggregator_schema = BaseAgent.tool_registry.get_tool_schema("search")
        self.content_scraper_schema = BaseAgent.tool_registry.get_tool_schema("scrape")
        
        # Replace instance methods with proper bound methods to avoid 'self' parameter
        self._fix_instance_method_schemas()
        
        # 移除旧的英文日志，使用中文统一输出
        # printer.log(f"Auto-discovered and registered {len(discovered_schemas)} tools", style="green")

    def _fix_instance_method_schemas(self):
        """
        Fix instance method schemas by replacing them with bound methods.
        """
        # Replace search schema with bound method (quietly, no logging)
        if "search" in BaseAgent.tool_registry._tools:
            search_schema = Tool.create_schema_from_function(self.search_aggregator.search)
            BaseAgent.tool_registry._tools["search"] = search_schema
            BaseAgent.tool_registry._funcs["search"] = self.search_aggregator.search
        
        # Replace scrape schema with bound method (quietly, no logging)
        if "scrape" in BaseAgent.tool_registry._tools:
            scrape_schema = Tool.create_schema_from_function(self.content_scraper.scrape)
            BaseAgent.tool_registry._tools["scrape"] = scrape_schema
            BaseAgent.tool_registry._funcs["scrape"] = self.content_scraper.scrape
        
        # Update available tools list
        updated_tools = []
        for tool in BaseAgent.available_tools:
            tool_name = tool.get('function', {}).get('name') or tool.get('name')
            if tool_name in ["search", "scrape"]:
                updated_tools.append(BaseAgent.tool_registry.get_tool_schema(tool_name))
            else:
                updated_tools.append(tool)
        
        BaseAgent.available_tools = updated_tools

    def _manual_setup_tools(self):
        """
        Legacy manual tool setup for backward compatibility.
        """
        self.search_aggregator_schema = (
            BaseAgent.tool_registry.get_or_create_tool_schema(
                self.search_aggregator.search
            )
        )

        self.content_scraper_schema = BaseAgent.tool_registry.get_or_create_tool_schema(
            self.content_scraper.scrape
        )

        BaseAgent.available_tools = [
            self.content_scraper_schema,
            self.search_aggregator_schema,
        ]

        # 注册笔记工具schema并加入可用工具
        note_schemas = BaseAgent.tool_registry.get_or_create_tool_schema(
            note_save, note_retrieve
        )
        BaseAgent.available_tools.extend(note_schemas)

    def get_tool_schema(self, tool_name: str) -> Optional[Dict]:
        """
        Get the schema for a specific tool by name.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Optional[Dict]: Tool schema if found, None otherwise
        """
        return BaseAgent.tool_registry.get_tool_schema(tool_name)

    def get_all_tool_schemas(self) -> List[Dict]:
        """
        Get all registered tool schemas.
        
        Returns:
            List[Dict]: List of all tool schemas
        """
        return BaseAgent.tool_registry.get_all_tool_schemas()

    def search_tools(self, query: str) -> List[Dict]:
        """
        Search for tools by name or description.
        
        Args:
            query: Search query
            
        Returns:
            List[Dict]: List of matching tool schemas
        """
        return BaseAgent.tool_registry.search_tools(query)

    def get_tool_names(self) -> List[str]:
        """
        Get all registered tool names.
        
        Returns:
            List[str]: List of tool names
        """
        return BaseAgent.tool_registry.get_tool_names()

    def is_tool_available(self, tool_name: str) -> bool:
        """
        Check if a tool is registered and available.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            bool: True if tool is available
        """
        return BaseAgent.tool_registry.is_tool_registered(tool_name)

    def refresh_tools(self):
        """
        Re-discover and register all tools. Useful for dynamic tool loading.
        """
        if hasattr(self, '_auto_setup_tools'):
            self._auto_setup_tools()
            printer.log("Tools refreshed", style="green")
        else:
            printer.log("Auto-discovery not enabled for this agent", style="yellow")

    def load_template(self, filename, root_folder=None):
        """
        Loads a template file from the prompts directory.

        :param filename: The name of the template file to load.
        :return: The content of the file as a string.
        """
        if root_folder:
            # If a root folder is provided, use it to construct the file path
            filepath = os.path.join(root_folder, filename)
        else:
            filepath = os.path.join(self.prompts_dir, filename)

        # Ensure the file exists
        if not os.path.exists(filepath):
            raise FileNotFoundError(
                f"Template file '{filename}' not found in {self.prompts_dir}"
            )

        # Read and return the content of the file
        with open(filepath, "r", encoding="utf-8") as file:
            return file.read()

    def render_template(self, template_str, data):
        """
        Render a template using string formatting.

        :param template_str: Template content as a string.
        :param data: Dictionary of variables to replace in the template.
        :return: Rendered string.
        """
        template = Template(template_str)
        return template.render(**data)

    def chat_with_template(
        self,
        template_name: str,
        template_data: dict,
        model: str = None,
        check_prompt: bool = False,
        root_folder: str = None,
        save_history: bool = True,
    ) -> str:
        """Unified helper method to handle template rendering and chat calling

        Args:
            template_name: Name of template file
            template_data: Data to render template with
            model: Optional model override

        Returns:
            Chat response content
        """
        template = self.load_template(template_name, root_folder=root_folder)
        rendered_prompt = self.render_template(template, template_data)

        if check_prompt:
            printer.log(f"Full Rendered Prompt:\n{rendered_prompt}")
            
        return self.chat(
            usr_prompt=rendered_prompt,
            model=model or settings.default_model,
            save_history=save_history,
        )

    def chat_with_tools(
        self, template_name: str, template_data: dict, tools: List, model: str = None
    ) -> ChatCompletionMessage:
        """Helper method for chat with tools"""
        template = self.load_template(template_name)
        rendered_prompt = self.render_template(template, template_data)
        return self.chat(
            usr_prompt=rendered_prompt,
            tools=tools,
            model=model or settings.default_model,
        )

    @overload
    def chat(
        self, usr_prompt: List, tools: None = None
    ) -> ChatCompletionMessage: ...

    @overload
    def chat(self, usr_prompt: str, tools: List) -> ChatCompletionMessage: ...

    @overload
    def chat(self, usr_prompt: str, tools: None = None) -> str: ...

    def chat(
        self,
        usr_prompt: str | List,
        tools: Optional[List] = None,
        role: str = "assistant",
        model: str = settings.default_model,  # 默认使用配置文件中的默认模型
        save_history: bool = True,
        messages: Optional[List[dict]] = None,  # 新增参数
    ) -> ChatCompletionMessage | str | None:
        llm_response = call_llm(
            model=model,  # 使用传入的model / 默认model
            usr_prompt=usr_prompt,
            config=settings,
            tools=tools,
            messages=messages  # 新增传递
        )

        if tools is not None:
            return llm_response

        if save_history:
            BaseAgent.conversation_manager.append_to_history(
                role=role, content=llm_response.content
            )

        return llm_response.content

    def update_answer(self, query, previous_answer, search_results, critic_feedback):
        data = {
            "query": query,
            "previous_answer": previous_answer,
            "search_results": search_results,
            "critic_feedback": critic_feedback,
        }

        agent_update_answer_prompt = self.load_template("agent_update_answer.txt")
        rendered_prompt = self.render_template(agent_update_answer_prompt, data)

        agent_update_answer_response = self.chat(usr_prompt=rendered_prompt)

        return agent_update_answer_response

    def model_confident(self, query):
        """
        检查模型是否对当前问题有信心。
        """
        data = {"user_question": query}
        agent_confidence_prompt = self.load_template("agent_confidence.txt")

        rendered_prompt = self.render_template(agent_confidence_prompt, data)
        agent_confidence_response = self.chat(usr_prompt=rendered_prompt)

        return agent_confidence_response

    def web_scrape_results(self, search_results: str) -> str | None:
        """Extract web content from search results using web scraper

        Args:
            search_results: Initial search results to scrape from

        Returns:
            Scraped web content or None if scraping failed
        """
        web_scraper_prompt = self.load_template("web_scraper.txt")
        web_scraper_rendered_prompt = self.render_template(
            web_scraper_prompt,
            {
                "user_question": self.user_question,
                "initial_search_results": search_results,
            },
        )

        # Interact with the model for web scraping
        web_scraper_response = self.chat(
            usr_prompt=web_scraper_rendered_prompt,
            tools=self.content_scraper_schema,
        )

        # If no tool calls, return the response immediately
        if web_scraper_response.tool_calls is None:
            return web_scraper_response.content

        BaseAgent.conversation_manager.append_tool_call_to_history(
            web_scraper_response.tool_calls
        )

        final_web_scraper_results = ""

        for tool_call in web_scraper_response.tool_calls:
            urls = json.loads(tool_call.function.arguments).get("urls", [])
            web_scraper_results = asyncio.run(self.content_scraper.scrape(urls=urls))
            BaseAgent.conversation_manager.append_tool_call_result_to_history(
                tool_call_id=tool_call.id,
                name="scrape",
                content=web_scraper_results,
            )
            final_web_scraper_results += web_scraper_results

        return final_web_scraper_results

    def search_and_browse(self, rendered_prompt) -> str | None:
        search_with_tool_response = self.chat(
            usr_prompt=rendered_prompt, tools=self.search_aggregator_schema
        )

        printer.log(f"search_with_tool_response:\n{search_with_tool_response}")

        # If no tool calls, return the response immediately
        if search_with_tool_response.tool_calls is None:
            return search_with_tool_response.content

        BaseAgent.conversation_manager.append_tool_call_to_history(
            search_with_tool_response.tool_calls
        )

        final_search_results = ""

        for tool_call in search_with_tool_response.tool_calls:
            query = json.loads(tool_call.function.arguments).get("query", "")

            search_results = asyncio.run(self.search_aggregator.search(query=query))

            time.sleep(0.2)

            BaseAgent.conversation_manager.append_tool_call_result_to_history(
                tool_call_id=tool_call.id,
                name="search",
                content=search_results,
            )

            BaseAgent.queryDB.update(query)

            final_search_results += f"{search_results}"

        return self.web_scrape_results(final_search_results)
    
    def extract_and_validate_yaml(self, model_response):
        match = re.search(r"```yaml\n([\s\S]*?)\n```", model_response, re.DOTALL)
        if not match:
            return None  # 如果没有找到匹配的内容，返回None

        model_response = match.group(1).strip()
        try:
            # 尝试解析YAML内容
            parsed_yaml = yaml.safe_load(model_response)
            return yaml.dump(parsed_yaml, default_flow_style=False)

        except yaml.YAMLError as exc:
            print(f"Invalid YAML content: {exc}")
            return None

    def receive_task(self, task):
        """
        接收原始任务。
        """
        self.original_task = task

    def extract_and_validate_json(self, model_response):
        # Try to extract JSON data wrapped in ```json``` blocks
        # and return the parsed JSON content
        match = re.search(r"```json\n([\s\S]*?)\n```", model_response, re.DOTALL)
        if match:
            json_content = match.group(1).strip()
        else:
            json_content = model_response.strip()

        try:
            parsed_json = json.loads(json_content, encoding="utf-8")
            return parsed_json

        except json.JSONDecodeError as exc:
            print(f"Invalid JSON content: {exc}")
            return None

    def taking_notes(self, web_results):
        """从搜索结果中提取信息并记录。"""
        result = self.chat_with_template(
            template_name="taking_notes.txt",
            template_data={"search_result": web_results, "TASK": self.original_task, "previous_notes": self.memo},
        )
        notes = extract_notes(result)
        if isinstance(notes, list) and notes:
            # 先转换成集合进行自动去重，然后更新到memo中
            new_notes = set(notes)  # 使用set自动去重
            printer.rule("New notes"); printer.print(new_notes)
            self.memo.update(new_notes)
            return list(new_notes)
        else:
            printer.print("No new notes.")
            return []


