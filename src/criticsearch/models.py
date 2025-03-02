import json
from pathlib import Path
from typing import List, Literal, Optional

from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
)
from pydantic import (
    BaseModel,
    SerializationInfo,
    SerializerFunctionWrapHandler,
    field_serializer,
    model_serializer,
)

from .config import settings
from .rich_output import printer


# Model for a single history entry
class HistoryItem(BaseModel):
    role: Literal["user", "assistant", "tool", "critic"]
    content: Optional[str] = None
    tool_calls: Optional[List[ChatCompletionMessageToolCall]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None


# Manager class for conversation history
class ConversationManager(BaseModel):
    history: List[HistoryItem] = []
    max_history_length: int = 10  # Limit for conversation history
    available_tools: List = []
    save_path: Path = Path("conversation_history.jsonl")
    delete_on_init: bool = True  # Flag to delete file on initialization

    def __init__(self, **data):
        super().__init__(**data)
        if self.delete_on_init and self.save_path.exists():
            try:
                self.save_path.unlink(missing_ok=True)  # Delete the file if it exists
                printer.log(f"Deleted existing file: {self.save_path}")
            except Exception:
                printer.print_exception(f"Failed to delete file {self.save_path}")
                raise
        # Set the flag to False to avoid further deletions
        self.delete_on_init = False

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

    def write(self, data: dict, path: Path | str):
        if isinstance(path, str):
            path = Path(path)

        try:
            # Create parent directories if they do not exist
            path.parent.mkdir(parents=True, exist_ok=True)

            # Check if the file exists and read existing data
            if path.exists():
                with path.open("r", encoding="utf-8") as f:
                    try:
                        # Try to parse the existing JSON data (expecting a list at the top level)
                        existing_data = json.load(f)
                        if not isinstance(existing_data, list):
                            existing_data = []  # Ensure it's a list
                    except json.JSONDecodeError:
                        # If the file is empty or corrupt, start with an empty list
                        existing_data = []
            else:
                existing_data = []

            # Append the new data to the existing array
            existing_data.append(data)

            # Write the updated array back to the file
            with path.open("w", encoding="utf-8") as f:
                json.dump(existing_data, f, ensure_ascii=True, indent=2)

        except Exception:
            printer.print_exception(f"Failed to write to {path}")
            raise

    def _auto_save(self):
        """Auto save after each update if save_path is set"""
        if settings.save_sharegpt:
            self.write(
                path=self.save_path, data=self.history[-1].model_dump(exclude_none=True)
            )

    def append_to_history(
        self,
        role: Literal["user", "assistant", "tool", "critic"],
        content: Optional[str] = None,
        **kwargs,
    ):
        """
        Add a new message to the conversation history.
        """
        self.history.append(HistoryItem(role=role, content=content, **kwargs))
        self._auto_save()

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
