from typing import Iterable

from openai import APIConnectionError, OpenAI
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.chat.chat_completion_user_message_param import (
    ChatCompletionUserMessageParam,
)


class ModelManager:
    def __init__(self, config):
        self.config = config
        self.clients = {}

    def get_model_config(self, model_name=None):
        models = self.config.get("models", {})
        if not models:
            raise ValueError("No models found in configuration.")

        if model_name is None:
            model_name = next(iter(models.keys()))

        if model_name not in models:
            raise ValueError(
                f"Model '{model_name}' not found in configuration. Available models: {list(models.keys())}"
            )

        model_config = models.get(model_name, {})
        return model_config

    def create_client(self, model_name=None):
        if model_name is None:
            model_name = next(iter(self.config.models.keys()))

        if model_name in self.clients:
            return self.clients[model_name]

        model_config = self.get_model_config(model_name)
        client = OpenAI(
            api_key=model_config.get("api_key"),
            base_url=model_config.get("base_url", "https://api.openai.com/v1"),
            timeout=self.config.get("timeout", 60),
            max_retries=self.config.get("max_retries"),
        )

        self.clients[model_name] = client
        return client


def call_llm(
    model, usr_prompt: str | Iterable[ChatCompletionMessageParam], config, tools
) -> ChatCompletionMessage:
    try:
        model_manager = ModelManager(config)
        client = model_manager.create_client(model)

        # 从 ModelManager 获取配置
        model_config = model_manager.get_model_config(model)
        if isinstance(usr_prompt, str):
            messages = [ChatCompletionUserMessageParam(content=usr_prompt, role="user")]
        else:
            messages = usr_prompt

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=model_config.get("temperature", 0.7),
            max_tokens=model_config.get("max_tokens", 8192),
            tools=tools,
        )

        response_message = response.choices[0].message
        return response_message

    except APIConnectionError as e:
        raise RuntimeError(f"Failed to connect to OpenAI API: {e}")
    except ValueError as e:
        raise ValueError(f"Error in configuration or model: {e}")
