import asyncio
import json
import os
import re
import time
from typing import List, Optional, overload

import yaml

# from jinja2 import Environment, FileSystemLoader
from jinja2 import Template

from .config import settings
from .llm_service import ChatCompletionMessage, call_llm
from .models import ConversationManager
from .rich_output import printer
from .tools import ContentScraper, SearchAggregator, ToolRegistry
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

    def __init__(self):
        base_dir = os.path.dirname(
            os.path.abspath(__file__)
        )  # Directory of the current script
        self.prompts_dir = os.path.join(base_dir, "prompts")
        # self.env = Environment(loader=FileSystemLoader(self.prompts_dir))

        # 对于citationDB,应该是一个字典，key是query，value是内容和来源
        # 这个列表中的每个元素都是一个字典，代表一个搜索的问题以及对应的搜索结果
        self.citationDB = [
            {  # citationDB中只会把受到critic表扬的搜索结果加入
                "why do we say google was facing challenges in 2019?": {
                    "document_id": {  # 这个document_id是一个唯一的标识符，用于标识这个文档
                        "url": "",
                        "title": "",
                        "content": "",
                    }
                }
            }
        ]
        self.search_aggregator = SearchAggregator()

        self.search_aggregator_schema = (
            BaseAgent.tool_registry.get_or_create_tool_schema(
                self.search_aggregator.search
            )
        )

        self.content_scraper = ContentScraper()

        self.content_scraper_schema = BaseAgent.tool_registry.get_or_create_tool_schema(
            self.content_scraper.scrape
        )

        BaseAgent.conversation_manager.available_tools = [
            self.content_scraper_schema,
            self.search_aggregator_schema,
        ]

        self.repeat_turns = 10

    def load_template(self, filename):
        """
        Loads a template file from the prompts directory.

        :param filename: The name of the template file to load.
        :return: The content of the file as a string.
        """
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
        self, template_name: str, template_data: dict, model: str = None
    ) -> str:
        """Unified helper method to handle template rendering and chat calling

        Args:
            template_name: Name of template file
            template_data: Data to render template with
            model: Optional model override

        Returns:
            Chat response content
        """
        template = self.load_template(template_name)
        rendered_prompt = self.render_template(template, template_data)
        return self.chat(
            usr_prompt=rendered_prompt, model=model or settings.default_model
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
    ) -> ChatCompletionMessage | str | None:
        llm_response = call_llm(
            model=model,  # 使用传入的model / 默认model
            usr_prompt=usr_prompt,
            config=settings,
            tools=tools,
        )

        if tools is not None:
            return llm_response

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
            parsed_json = json.loads(json_content)
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


