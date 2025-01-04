import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Literal, Optional

from charset_normalizer import from_bytes
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
)
from pydantic import (
    BaseModel,
    Field,
    SerializationInfo,
    SerializerFunctionWrapHandler,
    field_serializer,
    model_serializer,
)


# Model for a single history entry
class HistoryItem(BaseModel):
    role: Literal["user", "assistant", "tool", "critic"]
    content: Optional[str] = None
    tool_calls: Optional[List[ChatCompletionMessageToolCall]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None


def generate_save_path():
    base_dir = Path(".data")
    current_date = datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.now().strftime("%H-%M-%S")
    save_dir = base_dir / current_date
    save_dir.mkdir(parents=True, exist_ok=True)

    save_file = save_dir / f"conversation_history_{current_time}.json"  # 文件名为时间戳

    if not save_file.exists():
        save_file.write_text("[]", encoding="utf-8")  # 初始内容为空数组

    return save_file


# Manager class for conversation history
class ConversationManager(BaseModel):
    history: List[HistoryItem] = []
    max_history_length: int = 10  # Limit for conversation history
    available_tools: List = []
    save_path: Path = Field(default_factory=generate_save_path)

    @field_serializer("history")
    def serialize_history(self, history: List[HistoryItem]):
        serialized_history = []
        for item in history[-self.max_history_length :]:
            serialized_history.append(item.model_dump(exclude_none=True))
        return serialized_history

    @model_serializer(mode="wrap")
    def custom_serialize(
        self, handler: SerializerFunctionWrapHandler, info: SerializationInfo
    ):
        """
        Custom serialization logic that handles different contexts, such as 'sharegpt'.
        """
        # Perform default serialization
        result = handler(self)

        result = result["history"]

        if info.context and info.context.get("sharegpt"):
            # Transform history into ShareGPT format
            # TODO: human 和 observation 必须出现在奇数位置，gpt 和 function 必须出现在偶数位置
            conversations = []
            for item in self.history:
                role_mapping = {
                    "user": "human",
                    "assistant": "function_call",
                    "tool": "observation",
                    "critic": "critic",
                }

                role = role_mapping.get(item.role, item.role)
                value = item.content if item.content else None

                # For tool calls, include the tool_call_id or arguments
                if role == "function_call":
                    if item.tool_calls:
                        for tool_call in item.tool_calls:
                            value = json.dumps(
                                {
                                    "name": tool_call.function.name,
                                    "arguments": tool_call.function.arguments,
                                },
                                ensure_ascii=True,
                            )

                            conversations.append({"from": role, "value": value})
                    else:
                        conversations.append({"from": "gpt", "value": value})

                elif role == "observation":
                    conversations.append(
                        {"from": role, "value": json.dumps(value, ensure_ascii=True)}
                    )

                else:
                    conversations.append({"from": role, "value": value})

            # Build final output structure
            result = {
                "conversations": conversations,
                "tools": json.dumps(self.available_tools, ensure_ascii=True),
            }

        return result

    def write(self, data: Dict):
        with self.save_path.open("r", encoding="utf-8") as f:
            try:
                # Try to parse the existing JSON data (expecting a list at the top level)
                existing_data = json.load(f)
                if not isinstance(existing_data, list):
                    existing_data = []  # Ensure it's a list
            except json.JSONDecodeError:
                # If the file is empty or corrupt, start with an empty list
                existing_data = []

            # Append the new data to the existing array
            existing_data.append(data)

            # Write the updated array back to the file
            with self.save_path.open("w", encoding="utf-8") as f:
                json.dump(existing_data, f, ensure_ascii=True, indent=2)

    def _auto_save(self):
        """Auto save after each update if save_path is set"""
        self.write(data=self.history[-1].model_dump(exclude_none=True))

    def append_to_history(
        self,
        role: Literal["user", "assistant", "tool", "critic"],
        content: Optional[str] = None,
        **kwargs,
    ):
        """
        Add a new message to the conversation history.
        """
        # Normalize and process the content
        if content is not None:
            normalized_bytes = content.encode("utf-8", errors="replace")
            processed_content = str(from_bytes(normalized_bytes).best())
        else:
            processed_content = None

        self.history.append(HistoryItem(role=role, content=processed_content, **kwargs))
        self._auto_save()

        # logger.info(f"Current history:\n{self.model_dump()}")

    def append_tool_call_to_history(
        self,
        tool_calls: List[ChatCompletionMessageToolCall],
        content: Optional[str] = None,
    ):
        """
        Add a tool call entry to the conversation history.
        """
        self.append_to_history(role="assistant", tool_calls=tool_calls, content=content)

    def append_tool_call_result_to_history(
        self, tool_call_id: str, name: str, content: str
    ):
        """
        Add a tool call result to the conversation history.
        """
        self.append_to_history(
            role="tool", tool_call_id=tool_call_id, name=name, content=content
        )

    def clear_history(self):
        """
        Clear the entire conversation history.
        """
        self.history.clear()


if __name__ == "__main__":
    manager = ConversationManager()
    manager.append_to_history("user", "What is the weather today?")
    manager.append_to_history("assistant", "It's sunny and warm.")
    print(manager.model_dump())
