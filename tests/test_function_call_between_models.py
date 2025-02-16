import pytest

from criticsearch.config import settings
from criticsearch.llm_service import call_llm

# 定义工具（tools）
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather of an location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    }
                },
                "required": ["location"],
            },
        },
    },
]

# 定义要测试的模型
models_to_test = ["gpt-4o-mini", "aihubmix-DeepSeek-R1"]

# 定义用户消息
messages = [
    {"role": "user", "content": "What's the weather like in San Francisco today?"}
]


# 测试用例
@pytest.mark.parametrize("model", models_to_test)
def test_function_call(model):
    # 调用 call_llm 函数
    response = call_llm(
        model=model,
        usr_prompt=messages,
        config=settings,
        tools=tools,
    )

    # Case 1: DeepSeek model should not return a function call
    deepseek_family = ["r1", "reasoner"]

    if any(sub in model.lower() for sub in deepseek_family):
        with pytest.raises(AssertionError):
            assert response.tool_calls, f"Model {model} should not return tool_calls."

    # Case 2: Other models (like GPT-4o-mini) should return valid tool calls
    else:
        assert response.tool_calls, f"Model {model} returned empty tool_calls."

        # 检查 function 的名称是否正确
        for tool_call in response.tool_calls:
            assert tool_call.function.name == "get_weather", (
                f"Model {model} returned incorrect function name."
            )

            # 检查 function 的参数是否正确
            assert "location" in tool_call.function.arguments, (
                f"Model {model} returned incorrect function arguments."
            )
