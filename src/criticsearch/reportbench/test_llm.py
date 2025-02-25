from critic_search.base_agent import BaseAgent
from critic_search.config import settings

def test_llm():
    prompt = "你好，测试common_chat调用是否顺利？"
    agent = BaseAgent()
    answer = agent.common_chat(usr_prompt=prompt)
    print("common_chat Response:", answer)

if __name__ == "__main__":
    test_llm()