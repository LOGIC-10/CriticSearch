import pytest
from criticsearch.base_agent import BaseAgent
from criticsearch.config import settings

@pytest.mark.integration
@pytest.mark.skipif(
    not settings.models.get(settings.default_model, {}).get("api_key"),
    reason="需要在 settings.yaml 中为 default_model 配置有效的 api_key 才能运行集成测试"
)
def test_real_model_response():
    agent = BaseAgent()
    question = 'What happens in 2008-04-17?? return in json with urls and supporting facts like this: {"answer":"XXX","support":[{"url":"xxx","fact":"XXX}]}'
    response = agent.chat(question)
    print("Integration model response:", response)
    # 确保返回一个非空字符串
    assert isinstance(response, str) and response.strip(), "Expected a non-empty string"
    print("Integration model response:", response)
