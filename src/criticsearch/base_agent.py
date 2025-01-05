import json
import re
from importlib.resources import as_file, files
from pathlib import Path
from typing import Dict

import yaml
from jinja2 import Environment, FileSystemLoader
from loguru import logger
from sqlmodel import Session, select

from .config import settings
from .llm_service import call_llm
from .models import ConversationManager
from .tools.search_adapter.db.database import engine
from .tools.search_adapter.db.models import HistoryQuery
from .tools.toolbox import Toolbox


class BaseAgent:
    # Class-level attributes, shared across all instances
    user_question = ""

    # # 对于citationDB,应该是一个字典，key是query，value是内容和来源
    # # 这个列表中的每个元素都是一个字典，代表一个搜索的问题以及对应的搜索结果
    # citationDB = [
    #     {  # citationDB中只会把受到critic表扬的搜索结果加入
    #         "why do we say google was facing challenges in 2019?": {
    #             "document_id": {  # 这个document_id是一个唯一的标识符，用于标识这个文档
    #                 "url": "",
    #                 "title": "",
    #                 "content": "",
    #             }
    #         }
    #     }
    # ]

    conversation_manager = ConversationManager()
    conversation_manager.available_tools = Toolbox.get_function_schemas()

    @staticmethod
    def common_chat(
        usr_prompt: str, use_tool: bool = True, role: str | None = None
    ) -> str:
        llm_response = call_llm(
            model=settings.default_model,
            usr_prompt=usr_prompt,
            config=settings,
            tools=BaseAgent.conversation_manager.available_tools if use_tool else None,
        )

        # BaseAgent.conversation_manager.append_to_history(
        #     role="user", content=usr_prompt
        # )

        # logger.info(f"llm_response:\n{llm_response}")

        if role is not None:
            role = role
        else:
            role = "assistant"

        # If no tool calls, return the response immediately
        if llm_response.tool_calls is None:
            BaseAgent.conversation_manager.append_to_history(
                role=role, content=llm_response.content
            )

            assert llm_response.content is not None, "llm_response.content is None"

            return llm_response.content

        else:
            BaseAgent.conversation_manager.append_tool_call_to_history(
                llm_response.tool_calls,
                content=llm_response.content,
            )

            tool_call_result_list = []

            for tool_call in llm_response.tool_calls:
                tool_call_result = json.dumps(
                    Toolbox.execute_tool_call(tool_call), ensure_ascii=True
                )

                tool_call_result_list.append(tool_call_result)

                BaseAgent.conversation_manager.append_tool_call_result_to_history(
                    tool_call_id=tool_call.id,
                    name=tool_call.function.name,
                    content=tool_call_result,
                )

            return "\n\n".join(tool_call_result_list)

    @staticmethod
    def render_template(name: str, **kwargs) -> str:
        template_dir = files("criticsearch.prompts")

        # Ensure the template directory is valid
        if not template_dir.is_dir():
            raise FileNotFoundError(
                f"The specified template directory '{template_dir}' does not exist."
            )

        # Convert Traversable to Path for FileSystemLoader compatibility
        with as_file(template_dir) as template_path:
            # Initialize Jinja2 environment
            env = Environment(loader=FileSystemLoader(template_path))

            # Determine the template filename with '.j2' as the default extension
            template_filename = f"{name}.txt"

            # Load the template
            try:
                template = env.get_template(template_filename)
            except FileNotFoundError:
                raise FileNotFoundError(
                    f"The specified template '{template_filename}' does not exist in '{template_dir}'."
                )

            # Render the template with the user_query as a variable
            return template.render(**kwargs)

    @staticmethod
    def extract_and_validate_yaml(model_response) -> str | Dict | None:
        """
        Extracts YAML content wrapped in ```yaml``` from the response,
        validates it, and retries if parsing fails.
        """
        match = re.search(r"```yaml\n([\s\S]*?)\n```", model_response, re.DOTALL)

        if not match:
            return model_response

        yaml_content = match.group(1).strip()

        try:
            return yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            logger.warning(f"Failed to parse YAML: {e}. Retrying...")
            return None  # Indicate failure to parse YAML

    @staticmethod
    def chat_with_template(
        template_name: str,
        use_tool: bool = True,
        role: str | None = None,
        **template_params,
    ) -> str | Dict:
        logger.success(
            f"Chat using template: {template_name} with using tool or not: {use_tool}"
        )

        prompt = BaseAgent.render_template(name=template_name, **template_params)

        def perform_request():
            """Helper to perform chat request and validate YAML."""
            response = BaseAgent.common_chat(
                usr_prompt=prompt, use_tool=use_tool, role=role
            )
            return BaseAgent.extract_and_validate_yaml(response)

        result = perform_request()

        if result is None:  # Retry if YAML extraction failed
            result = perform_request()

        assert result is not None

        return result

    @staticmethod
    def get_all_history_queries() -> str:
        """
        Fetch all unique queries from the HistoryQuery table.

        Returns:
            List[str]: A list of all unique queries.
        """
        try:
            with Session(engine) as session:
                # Fetch all query values from the HistoryQuery table
                statement = select(HistoryQuery.query)
                results = session.exec(statement).all()

                # Convert results to a list and join with commas
                result_list = list(results)
                joined_results = ", ".join(result_list)

                return joined_results

        except Exception:
            logger.exception(f"Failed to fetch queries from HistoryQuery.")
            return ""
