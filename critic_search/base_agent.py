import re
from typing import List

import yaml
from jinja2 import Environment, FileSystemLoader, Template

from critic_search.config import read_config
from critic_search.tools import SearchAggregator, ToolRegistry, WebScraper
from critic_search.utils import call_llm


class BaseAgent:
    def __init__(self):
        self.config = read_config()
        self.model = self.config.get("default_model", "gpt-4o-mini")
        self.env = Environment(loader=FileSystemLoader("critic_search/prompts"))
        # 定一个通用格式,queryDB应该是一个set,里面每个元素是一个query
        self.queryDB = (
            set()
        )  # 对于citationDB,应该是一个字典，key是query，value是内容和来源
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

        self.sys_prompt = ""
        self.repeat_turns = 10
        self.history = []

    #     self.tool_registry = ToolRegistry()
    #     self._register_default_tools()
    #     self._setup_prompts()

    # def _register_default_tools(self):
    #     self.search_aggregator = SearchAggregator()
    #     self.web_scraper = WebScraper()
    #     self.tool_registry.register(self.search_aggregator.search, self.web_scraper.scrape)

    # def parse_tool_calls(self, response: str) -> List[ToolCall]:
    #     """Parse tool calls from the response."""
    #     try:
    #         # Extract YAML between ```yaml and ``` markers
    #         yaml_match = re.search(r"```yaml\n(.*?)```", response, re.DOTALL)
    #         if not yaml_match:
    #             return []

    #         yaml_content = yaml_match.group(1)
    #         parsed = yaml.safe_load(yaml_content)

    #         if not parsed or "tool_calls" not in parsed:
    #             return []

    #         return [ToolCall(**call) for call in parsed["tool_calls"]]

    #     except Exception as e:
    #         print(f"Error parsing tool calls: {e}")
    #         return []

    # def execute_tool_calls(self, tool_calls: List[ToolCall]) -> List[ToolResponse]:
    #     """Execute a sequence of tool calls."""
    #     responses = []

    #     for call in tool_calls:
    #         tool = self.tool_registry.get_tool(call.tool)
    #         if not tool:
    #             responses.append(
    #                 ToolResponse(result={}, error=f"Tool '{call.tool}' not found")
    #             )
    #             continue

    #         try:
    #             result = tool["function"](**call.parameters)
    #             responses.append(ToolResponse(result=result))
    #         except Exception as e:
    #             responses.append(
    #                 ToolResponse(
    #                     result={}, error=f"Error executing {call.tool}: {str(e)}"
    #                 )
    #             )

    #     return responses

    #     def common_chat_with_tool_call(self, query: str) -> str:
    #         """Enhanced chat method with tool calling capabilities."""
    #         # First, get potential tool calls from the model
    #         tool_response = call_llm(
    #             model=self.model,
    #             sys_prompt=self.sys_prompt,
    #             usr_prompt=f"Query: {query}\n\nDetermine if any tools are needed to answer this query. If so, specify the tool calls in YAML format.",
    #             config=self.config,
    #         )

    #         # Parse and execute tool calls
    #         tool_calls = self.parse_tool_calls(tool_response)
    #         print(tool_calls)
    #         tool_results = []

    #         if tool_calls:
    #             tool_responses = self.execute_tool_calls(tool_calls)
    #             tool_results = [
    #                 f"Tool '{call.tool}' results (called because {call.reasoning}):\n{response.result if not response.error else f'Error: {response.error}'}"
    #                 for call, response in zip(tool_calls, tool_responses)
    #             ]
    #             print(tool_results)

    #         # Generate final response with tool results
    #         final_prompt = f"""Query: {query}

    # Tool results:
    # {yaml.dump({'tool_results': tool_results}, default_flow_style=False) if tool_results else 'No tools were used.'}

    # Please provide a comprehensive response based on the available information."""

    #         return call_llm(
    #             model=self.model,
    #             sys_prompt=self.sys_prompt,
    #             usr_prompt=final_prompt,
    #             config=self.config,
    #         )

    def common_chat(self, query):
        llm_response = call_llm(
            model=self.model,
            sys_prompt=self.sys_prompt,
            usr_prompt=query,
            config=self.config,
        )
        self.history.append({"role": "user", "content": query})
        self.history.append({"role": "assistant", "content": llm_response})
        return llm_response

    def clear_history(self):
        self.history = []

    def update_answer(self, query, previous_answer, search_results, critic_feedback):
        data = {
            "query": query,
            "previous_answer": previous_answer,
            "search_results": search_results,
            "critic_feedback": critic_feedback,
        }
        updated_answer = self.chat_with_template(
            data, self.env.get_template("agent_update_answer.txt")
        )
        return updated_answer

    def model_confident(self, query):
        """
        检查模型是否对当前问题有信心。
        """
        data = {"user_question": query}
        model_response = self.chat_with_template(
            data, self.env.get_template("agent_confidence.txt")
        )
        return model_response

    def initialize_search(self, query):
        """
        初始化搜索。
        """
        data = {"user_question": query}
        model_response = self.chat_with_template(
            data, self.env.get_template("planner_agent_initial_search_plan.txt")
        )
        return model_response

    def chat_with_template(self, data, prompt_template: Template):
        """
        通用的聊天方法，根据传入的data字典适配不同的prompt。
        """
        rendered_prompt = prompt_template.render(**data)
        # print(rendered_prompt)
        response_message = self.common_chat(query=rendered_prompt)
        return response_message

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
