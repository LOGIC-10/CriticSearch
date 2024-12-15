from typing import Dict, List, Literal, Optional

from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
)
from pydantic import BaseModel, model_serializer


# 定义单条历史记录的模型
class HistoryItem(BaseModel):
    role: Literal["user", "assistant", "tools"]
    content: Optional[str] = None
    tool_calls: Optional[List[ChatCompletionMessageToolCall]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None

    @model_serializer
    def ser_model(self) -> Dict:
        """序列化单条历史记录为 ShareGPT 格式"""
        if self.role == "tools":
            return {
                "from": "function_call",
                "value": self.content,
            }
        else:
            return {
                "from": self.role,
                "value": self.content or "",
            }


# 管理历史记录的类
class ConversationManager(BaseModel):
    history: List[HistoryItem] = []

    def add_history(self, role: Literal["user", "assistant"], content, **kwargs):
        self.history.append(HistoryItem(role=role, content=content, **kwargs))

    def add_tool_call_to_history(self, tool_calls, content):
        self.add_history(role="assistant", content=content, tool_calls=tool_calls)

    def add_tool_call_result_to_history(self, message: Dict):
        self.history.append(HistoryItem.model_validate((message)))

    def clear_history(self):
        self.history.clear()

    # TODO:
    # 1. 使得 system 在最开始
    # 2. 使得 human 和 observation 必须出现在奇数位置，gpt 和 function 必须出现在偶数位置
    @model_serializer
    def ser_model(self) -> Dict:
        """序列化完整历史记录为 ShareGPT 格式"""
        return {"conversations": [item.model_dump() for item in self.history]}


if __name__ == "__main__":
    manager = ConversationManager()
    manager.add_history("user", "What is the weather today?")
    manager.add_history("assistant", "It's sunny and warm.")
    print(manager.model_dump())
