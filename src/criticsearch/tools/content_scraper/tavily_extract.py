import json
from typing import List
import httpx
from tenacity import retry, stop_after_attempt, wait_fixed
from criticsearch.config import settings
from criticsearch.rich_output import printer

class TavilyExtract:
    def __init__(self, api_key: str):
        self.base_url = "https://api.tavily.com/extract"
        self._api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }
        self._client = httpx.AsyncClient(http2=True)

    @retry(stop=stop_after_attempt(settings.max_retries), wait=wait_fixed(1), reraise=True)
    async def extract_content(self, urls: List[str]) -> dict:
        """
        向 Tavily API 发送请求并解析 JSON。若网络请求或解析失败，
        会自动重试最多 settings.max_retries 次，再失败则抛出。
        """
        payload = {"urls": urls}
        try:
            resp = await self._client.post(self.base_url, headers=self.headers, json=payload)
            resp.raise_for_status()
            try:
                return resp.json()
            except json.JSONDecodeError as e:
                printer.print(f"[WARN] 第一次解析 JSON 失败: {e}，重试模型调用…")
                # 触发重试
                raise
        except httpx.RequestError as e:
            printer.print(f"[WARN] 网络请求错误: {e}，重试…")
            raise
        except httpx.HTTPStatusError as e:
            printer.print(f"[WARN] HTTP 状态错误: {e}，重试…")
            raise
