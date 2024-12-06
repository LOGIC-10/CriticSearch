import asyncio
import json
from typing import List, Optional

import yaml
from jinja2 import Environment, FileSystemLoader
from loguru import logger

from critic_search.config import settings
from critic_search.llm_service import ChatCompletionMessage, call_llm
from critic_search.tools import SearchAggregator, ToolRegistry, AsyncWebScraper


class BaseAgent:
    # Class-level attributes, shared across all instances
    queryDB = set()  # A set to store queries
    tool_registry = ToolRegistry()  # Registry for tools

    def __init__(self):
        self.env = Environment(loader=FileSystemLoader("critic_search/prompts"))

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
        self.web_scraper = AsyncWebScraper()

        self.repeat_turns = 10
        self.history = []

        BaseAgent.tool_registry.register(self.search_aggregator.search, self.web_scraper.scrape)

    def common_chat(
        self, usr_prompt, tools: Optional[List] = None, raw: Optional[bool] = False
    ) -> ChatCompletionMessage | str:
        llm_response = call_llm(
            model=settings.default_model,
            usr_prompt=usr_prompt,
            config=settings,
            tools=tools,
        )
        self.history.append({"role": "user", "content": usr_prompt})
        self.history.append({"role": "assistant", "content": llm_response})
        if raw:
            logger.debug(f"llm_response:\n {llm_response}")
            return llm_response
        return llm_response.content  # type: ignore

    def clear_history(self):
        self.history = []

    def update_answer(self, query, previous_answer, search_results, critic_feedback):
        data = {
            "query": query,
            "previous_answer": previous_answer,
            "search_results": search_results,
            "critic_feedback": critic_feedback,
        }

        agent_update_answer_prompt = self.env.get_template("agent_update_answer.txt")
        rendered_prompt = agent_update_answer_prompt.render(**data)

        agent_update_answer_response = self.common_chat(usr_prompt=rendered_prompt)

        return agent_update_answer_response

    def model_confident(self, query):
        """
        检查模型是否对当前问题有信心。
        """
        data = {"user_question": query}
        agent_confidence_prompt = self.env.get_template("agent_confidence.txt")

        rendered_prompt = agent_confidence_prompt.render(**data)
        agent_confidence_response = self.common_chat(usr_prompt=rendered_prompt)

        return agent_confidence_response

    def initialize_search(self, search_rendered_prompt: str, user_question: str):
        """
        Initiate a search based on the rendered prompt and return the results.
        """

        # Define the tool schema for search
        search_tool = [BaseAgent.tool_registry.get_tool_schema(self.search_aggregator.search)]
        web_scrape_tool = [BaseAgent.tool_registry.get_tool_schema(self.web_scraper.scrape)]
        search_tool_schema_list = search_tool + web_scrape_tool

        # Interact with the model for initial search processing
        search_with_tool_response = self.common_chat(
            usr_prompt=search_rendered_prompt, tools=search_tool_schema_list, raw=True
        )

        # If no tool calls, return the response immediately
        if search_with_tool_response.tool_calls is None:  # type: ignore
            return search_with_tool_response

        # Extract tool call IDs and their corresponding queries
        tool_call_id_to_queries = {
            tool_call.id: json.loads(tool_call.function.arguments).get("query", [])  # List[str]
            for tool_call in search_with_tool_response.tool_calls  # type: ignore
        }

        # Collect all queries in a single list for batch search
        all_queries = [query for queries in tool_call_id_to_queries.values() for query in queries]
        logger.info(f"All queries extracted: {all_queries}")

        # Execute the batch search and retrieve results
        search_results = asyncio.run(self.search_aggregator.search(query=all_queries))  # Returns a dictionary

        # Build the response map (tool_call_id -> query -> search_result)
        tool_call_id_to_response = {
            tool_call_id: {
                query: search_results.get(query)  # Match queries with their search results
                for query in queries
            }
            for tool_call_id, queries in tool_call_id_to_queries.items()
        }

        # Initialize a list to store the function call result messages
        function_call_result_messages = []

        # Iterate through the tool_call_id_to_response dictionary and build messages
        for tool_call_id, queries_to_responses in tool_call_id_to_response.items():
             # Concatenate all search results
            search_result = "\n".join(queries_to_responses.values()) # type: ignore 

            # Build the response message for each tool call
            message = {
                "role": "tool",
                "content": json.dumps({
                    "query": list(queries_to_responses.keys()),  # List of queries
                    "search_result": search_result  # Concatenated search results
                }),
                "tool_call_id": tool_call_id,
            }
            function_call_result_messages.append(message)

        # 根据初步的搜索结果进行筛选然后网页爬取
        # Extract search results from tool messages
        search_results = [json.loads(msg['content'])['search_result'] for msg in function_call_result_messages]

        web_scraper_prompt = self.env.get_template("web_scraper.txt")
        web_scraper_rendered_prompt = web_scraper_prompt.render(
            user_question=user_question,
            initial_search_results = search_results
        )

        # Interact with the model for web scraping
        web_scraper_response = self.common_chat(usr_prompt=web_scraper_rendered_prompt, tools=web_scrape_tool, raw=True)

        from IPython import embed; embed()

        # Extract tool call IDs and their corresponding queries
        tool_call_id_to_urls = {
            tool_call.id: json.loads(tool_call.function.arguments).get("urls", [])  # List[str]
            for tool_call in web_scraper_response.tool_calls  # type: ignore
        }

        # Collect all URLs in a single list for batch scraping
        all_urls = [url for urls in tool_call_id_to_urls.values() for url in urls]
        logger.info(f"All URLs extracted: {all_urls}")

        # Execute the batch scraping and retrieve results
        web_scraper_results = asyncio.run(self.web_scraper.scrape(urls=all_urls))  # Returns a dictionary

        # Construct the final prompt by combining the user input and the generated messages
        final_prompt = [
            {"role": "user", "content": search_rendered_prompt},
            search_with_tool_response,
        ] + function_call_result_messages
        
        logger.debug(f"Final prompt constructed: {final_prompt}")

        # Get the final response from the model based on the constructed prompt
        final_response = self.common_chat(usr_prompt=final_prompt)

        # Update the query DB with the new queries
        BaseAgent.queryDB.update(set(all_queries))  # type: ignore

        return final_response, search_results

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


if __name__ == "__main__":
    agent = BaseAgent()
    result = agent.search_aggregator.search(
        [
            "why do we say google was facing challenges in 2019?",
            "what are the challenges google faced in 2019?",
        ]
    )
    print(result)

"""
curl https://toollearning.cn/v1/chat/completions \
    -H "Authorization: Bearer $OPENAI_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{
        "model": "gpt-4o",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful support assistant. Use the supplied tools to assist the user."
            },
            {
                "role": "user",
                "content": "Hi, can you help me search latest sport news?"
            }
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "search",
                    "description": "Asynchronous search method supporting multiple concurrent queries and engine fallback.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                        "type": "array",
                        "description": "A list of search queries.",
                        "items": {
                            "type": "string"
                        }
                        }
                    },
                    "required": [
                        "query"
                    ],
                    "additionalProperties": false
                    }
                }
            }
        ]
    }'
"""
