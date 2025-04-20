import pytest
from criticsearch.base_agent import BaseAgent
from criticsearch.llm_service import call_llm as real_call_llm

# Dummy message to simulate ChatCompletionMessage
class DummyMessage:
    def __init__(self, content):
        self.content = content

@pytest.fixture(autouse=True)
def patch_call_llm(monkeypatch):
    # fake call_llm returns DummyMessage with known content
    def fake_call_llm(model, config, usr_prompt, tools=None, messages=None):
        return DummyMessage(content="fake response")
    # patch both llm_service and base_agent references
    monkeypatch.setattr("criticsearch.llm_service.call_llm", fake_call_llm)
    monkeypatch.setattr("criticsearch.base_agent.call_llm", fake_call_llm)

def test_chat_without_tools_returns_str():
    agent = BaseAgent()
    resp = agent.chat("hello")
    assert isinstance(resp, str)
    assert resp == "fake response"

def test_chat_with_tools_returns_message_object():
    agent = BaseAgent()
    dummy_tools = []
    result = agent.chat(["ignored"], tools=dummy_tools)
    # with tools, chat should return the raw message object
    assert hasattr(result, "content")
    assert result.content == "fake response"
