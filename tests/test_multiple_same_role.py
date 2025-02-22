from criticsearch.config import settings
from criticsearch.llm_service import call_llm

# 定义测试消息，前面是 assistant，最后一条是 user
messages = [
    {"role": "assistant", "content": "Hello! How can I assist you today?"},
    {
        "role": "assistant",
        "content": "I can provide weather updates, news summaries, and more.",
    },
    {
        "role": "assistant",
        "content": "For example, I can tell you the weather in any city.",
    },
    {"role": "user", "content": "What's the weather like in San Francisco today?"},
]

# 调用 LLM
response = call_llm(
    model="gpt-4o-mini",
    usr_prompt=messages,
    config=settings,
)

# 打印响应
print(response)
