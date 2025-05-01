import pytest
import json
from httpx import AsyncClient
from criticsearch.tools.content_scraper.tavily_extract import TavilyExtract
from criticsearch.config import settings

class DummyResponse:
    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code

    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            raise Exception(f"HTTP {self.status_code}")

    def json(self):
        # 模拟 JSON 解析
        return self._data

class DummyClient:
    def __init__(self, resp):
        self._resp = resp

    async def post(self, url, headers=None, json=None):
        return self._resp

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

@pytest.mark.asyncio
async def test_extract_content_success(monkeypatch):
    # 准备一个正确的 JSON 返回值
    dummy = DummyResponse({"foo": "bar"})
    monkeypatch.setattr(AsyncClient, "__init__", lambda self, http2=True: None)
    monkeypatch.setattr(AsyncClient, "post", lambda self, url, headers, json: dummy)
    monkeypatch.setattr(AsyncClient, "raise_for_status", dummy.raise_for_status)

    extractor = TavilyExtract(api_key="test-key")
    data = await extractor.extract_content(["http://example.com"])
    assert isinstance(data, dict)
    assert data["foo"] == "bar"

@pytest.mark.asyncio
async def test_extract_content_retry_on_invalid_json(monkeypatch):
    # 第一次返回无效 JSON，第二次返回合法 JSON
    class BadResp(DummyResponse):
        def __init__(self):
            super().__init__(None)
        def json(self):
            raise json.JSONDecodeError("Expecting value", "", 0)
    bad = BadResp()
    good = DummyResponse({"ok": True})

    call_count = {"n": 0}
    async def fake_post(self, url, headers=None, json=None):
        call_count["n"] += 1
        return bad if call_count["n"] < 2 else good

    monkeypatch.setattr(AsyncClient, "__init__", lambda self, http2=True: None)
    monkeypatch.setattr(AsyncClient, "post", fake_post)

    extractor = TavilyExtract(api_key="test-key")
    data = await extractor.extract_content(["http://example.com"])
    assert data == {"ok": True}
    assert call_count["n"] == 2

@pytest.mark.asyncio
@pytest.mark.skipif(
    not getattr(settings, "tavily", None) or not settings.tavily.get("api_key"),
    reason="未找到 Tavily API Key，跳过真实调用测试"
)
async def test_real_extract_content():
    extractor = TavilyExtract(settings.tavily["api_key"])
    urls = ["https://www.electionguide.org/elections/id/4314/"]  # 可替换为任何公开可访问的网页
    result = await extractor.extract_content(urls)
    # 结果应为 dict，且包含每个 URL 的解析结果（非空 dict 或包含 text 字段）
    assert isinstance(result, dict)
    assert urls[0] in result
    assert isinstance(result[urls[0]], dict), "返回值应为 dict"
    # 可选：如果 API 返回有 text 字段，可做如下断言
    # assert "text" in result[urls[0]] and result[urls[0]]["text"], "内容应包含 text"