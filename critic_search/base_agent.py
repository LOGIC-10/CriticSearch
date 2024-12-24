import asyncio
import json
import os
from typing import List, Optional, overload

import yaml

# from jinja2 import Environment, FileSystemLoader
from jinja2 import Template
from loguru import logger

from .config import settings
from .llm_service import ChatCompletionMessage, call_llm
from .models import ConversationManager
from .tools import AsyncWebScraper, SearchAggregator, ToolRegistry


class BaseAgent:
    # Class-level attributes, shared across all instances
    queryDB = set()  # A set to store queries
    tool_registry = ToolRegistry()  # Registry for tools
    user_question = ""
    conversation_manager = ConversationManager()

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

        self.web_scraper = AsyncWebScraper()

        self.web_scraper_schema = BaseAgent.tool_registry.get_or_create_tool_schema(
            self.web_scraper.scrape
        )

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

    @overload
    def common_chat(
        self, usr_prompt: List, tools: None = None
    ) -> ChatCompletionMessage: ...

    @overload
    def common_chat(self, usr_prompt: str, tools: List) -> ChatCompletionMessage: ...

    @overload
    def common_chat(self, usr_prompt: str, tools: None = None) -> str: ...

    def common_chat(
        self,
        usr_prompt: str | List,
        tools: Optional[List] = None,
        role: str = "assistant",
    ) -> ChatCompletionMessage | str | None:
        llm_response = call_llm(
            model=settings.default_model,
            usr_prompt=usr_prompt,
            config=settings,
            tools=tools,
        )

        # logger.info(f"usr_prompt:\n {usr_prompt}")
        # logger.info(f"llm_response:\n {llm_response}")

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

        agent_update_answer_response = self.common_chat(usr_prompt=rendered_prompt)

        return agent_update_answer_response

    def model_confident(self, query):
        """
        检查模型是否对当前问题有信心。
        """
        data = {"user_question": query}
        agent_confidence_prompt = self.load_template("agent_confidence.txt")

        rendered_prompt = self.render_template(agent_confidence_prompt, data)
        agent_confidence_response = self.common_chat(usr_prompt=rendered_prompt)

        return agent_confidence_response

    def search_and_browse(self, rendered_prompt) -> str | None:
        search_with_tool_response = self.common_chat(
            usr_prompt=rendered_prompt, tools=self.search_aggregator_schema
        )

        # If no tool calls, return the response immediately
        if search_with_tool_response.tool_calls is None:
            return search_with_tool_response.content

        BaseAgent.conversation_manager.append_tool_call_to_history(
            search_with_tool_response.tool_calls
        )

        # Extract tool call IDs and their corresponding queries
        tool_call_id_to_queries = {
            tool_call.id: json.loads(tool_call.function.arguments).get("query", [])
            for tool_call in search_with_tool_response.tool_calls
        }

        # Collect all queries in a single list for batch search
        all_queries = [
            query for queries in tool_call_id_to_queries.values() for query in queries
        ]

        logger.info(f"All queries extracted: {all_queries}")

        # Update the query DB with the new queries
        BaseAgent.queryDB.update(set(all_queries))  # type: ignore

        # Execute the batch search and retrieve results
        search_results = asyncio.run(
            self.search_aggregator.search(query=all_queries)
        )  # Returns a dictionary

        # Build the response map (tool_call_id -> query -> search_result)
        tool_call_id_to_response = {
            tool_call_id: {
                query: search_results.get(
                    query
                )  # Match queries with their search results
                for query in queries
            }
            for tool_call_id, queries in tool_call_id_to_queries.items()
        }

        # Initialize a list to store the function call result messages
        function_call_result_messages = []

        # Iterate through the tool_call_id_to_response dictionary and build messages
        for tool_call_id, queries_to_responses in tool_call_id_to_response.items():
            # Concatenate all search results
            search_result = "\n".join(
                value for value in queries_to_responses.values() if value is not None
            )

            search_result_json = json.dumps(
                {
                    "query": list(queries_to_responses.keys()),  # List of queries
                    "search_result": search_result,  # Concatenated search results
                }
            )
            # Build the response message for each tool call
            message = {
                "role": "tools",
                "content": search_result_json,
                "tool_call_id": tool_call_id,
            }

            BaseAgent.conversation_manager.append_tool_call_result_to_history(
                tool_call_id=tool_call_id,
                name="search",
                content=search_result_json,
            )

            function_call_result_messages.append(message)

        # 根据初步的搜索结果进行筛选然后网页爬取
        # Extract search results from tool messages
        search_results = [
            json.loads(msg["content"])["search_result"]
            for msg in function_call_result_messages
        ]

        web_scraper_prompt = self.load_template("web_scraper.txt")
        web_scraper_rendered_prompt = self.render_template(
            web_scraper_prompt,
            {
                "user_question": self.user_question,
                "initial_search_results": search_results,
            },
        )

        # Interact with the model for web scraping
        web_scraper_response = self.common_chat(
            usr_prompt=web_scraper_rendered_prompt,
            tools=self.web_scraper_schema,
        )

        # If no tool calls, return the response immediately
        if web_scraper_response.tool_calls is None:
            return web_scraper_response.content

        BaseAgent.conversation_manager.append_tool_call_to_history(
            web_scraper_response.tool_calls
        )

        final_web_scraper_results = []
        for tool_call in web_scraper_response.tool_calls:
            urls = json.loads(tool_call.function.arguments).get("urls", [])

            web_scraper_results = asyncio.run(self.web_scraper.scrape(urls=urls))

            web_scraper_results_str = self._format_web_scraper_results(
                web_scraper_results
            )

            BaseAgent.conversation_manager.append_tool_call_result_to_history(
                tool_call_id=tool_call.id,
                name="scrape",
                content=web_scraper_results_str,
            )

            final_web_scraper_results.append(web_scraper_results_str)

        return "\n".join(final_web_scraper_results)

    def _format_web_scraper_results(self, web_scraper_results) -> str:
        """
        Format web scraper results into markdown text.

        Args:
            web_scraper_results: List of scraping results with title, url and content

        Returns:
            str: Formatted markdown text with results
        """
        result_blocks = []
        for item in web_scraper_results:
            title = item.title or "No Title"
            content_lines = item.content
            if content_lines is None:
                content_lines = []
            elif isinstance(content_lines, str):
                content_lines = [content_lines]

            block = f"## [{title}]({item.url})\n\n" + "\n".join(content_lines)
            result_blocks.append(block)

        return "\n\n---\n\n".join(result_blocks)

    def receive_task(self, task):
        """
        接收原始任务。
        """
        self.original_task = task

    def extract_and_validate_yaml(self, model_response):
        # 正则表达式匹配包裹在```yaml```之间的内容
        import re

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
