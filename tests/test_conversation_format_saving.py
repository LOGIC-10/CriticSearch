import json
from types import SimpleNamespace
import pytest
from criticsearch.base_agent import BaseAgent
from openai.types.chat.chat_completion_message_tool_call import ChatCompletionMessageToolCall, Function

class DummyToolCall(ChatCompletionMessageToolCall):
    def __init__(self, id, name, args):
        super().__init__(
            id=id,
            type="function",
            function=Function(name=name, arguments=json.dumps(args))
        )

@pytest.fixture(autouse=True)
def clear_history_and_stub(monkeypatch):
    # 清空历史
    BaseAgent.conversation_manager.clear_history()
    # Stub 模板加载与渲染，避免文件不存在
    monkeypatch.setattr(
        BaseAgent, "load_template", lambda self, filename, root_folder=None: ""
    )
    monkeypatch.setattr(
        BaseAgent, "render_template", lambda self, template_str, data: ""
    )
    yield
    BaseAgent.conversation_manager.clear_history()

def test_conversation_roundtrip(monkeypatch, tmp_path):
    agent = BaseAgent()

    # 1. 用户提问
    BaseAgent.conversation_manager.append_to_history(
        role="user", content="Hello, world!"
    )

    # 2. 模拟工具调用
    def fake_call_llm(model, usr_prompt, config, tools=None):
        if tools is not None:
            # 模拟一次 search 工具调用
            return SimpleNamespace(
                tool_calls=[DummyToolCall("tc1", "search", {"query": ["foo"]})],
                content=None
            )
        # 模拟普通聊天回复
        return SimpleNamespace(tool_calls=None, content="OK, got it.")
    monkeypatch.setattr("criticsearch.base_agent.call_llm", fake_call_llm)

    # 3. agent 调用工具
    res = agent.search_and_browse("unused prompt")
    # 4. 模拟工具执行结果保存
    BaseAgent.conversation_manager.append_tool_call_result_to_history(
        tool_call_id="tc1", name="search", content="<<fake search result>>"
    )

    # 5. 再来一次普通回复
    reply = agent.chat_with_template(
        template_name="direct_response.txt",
        template_data={"task": "dummy"},
    )

    # 6. 序列化并检查
    result = BaseAgent.conversation_manager.model_dump(context={"sharegpt": True})
    assert "conversations" in result and "tools" in result
    convs = result["conversations"]

    senders = [c["from"] for c in convs]
    # 首条应为用户 (human)
    assert senders[0] == "human"
    # 工具调用以 function_call 出现，并带有 search
    assert any(c["from"] == "function_call" and "search" in c["value"] for c in convs)
    # 工具结果以 observation 出现，包含 fake search result
    assert any(c["from"] == "observation" and "fake search result" in c["value"] for c in convs)
    # 最后一条正常回复以 gpt 出现
    assert convs[-1]["from"] == "gpt"
    assert "OK, got it." in convs[-1]["value"]
