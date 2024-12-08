# critic_search/search_adapter/bing_client.py
from typing import Literal

import httpx
from loguru import logger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_random,
)

from .base_search_client import BaseSearchClient
from .exceptions import InvalidAPIKeyError, RatelimitException, UsageLimitExceededError
from .models import SearchResponse, SearchResult


class BingClient(BaseSearchClient):
    """
    Bing Search API client.
    """

    def __init__(self, api_key: str):
        self.base_url = "https://api.bing.microsoft.com/v7.0/search"
        self._api_key = api_key

    @retry(
        stop=stop_after_attempt(5),  # 重试最多5次
        wait=wait_exponential(multiplier=1, min=4, max=30)
        + wait_random(min=1, max=5),  # 指数退避 + 随机抖动
        retry=retry_if_exception_type(RatelimitException),
    )
    async def search(
        self,
        query: str,
        max_results: int = 10,
    ) -> SearchResponse:
        """
        Perform an asynchronous search on Bing.

        Args:
            query (str): The search query.
            days (int, optional): Time limit in days. Bing doesn't support direct day filtering similarly,
                                  so you can ignore or implement custom logic.
            max_results (int, optional): Maximum number of results to return.
            region (Literal["us-en", "cn-zh"], optional): Region or language code for the search.

        Returns:
            SearchResponse: Pydantic model containing the search results.
        """
        headers = {"Ocp-Apim-Subscription-Key": self._api_key}

        # You could add a 'mkt' parameter to target a specific market.
        # For example, "mkt": "en-US".
        params = {
            "q": query,
            "count": max_results,
            # You can add additional Bing parameters here if needed.
        }

        logger.debug(f"Using 'bing' for query '{query}'.")

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(self.base_url, headers=headers, params=params)

            # 处理 HTTP 状态码
            if response.status_code == 429:
                raise RatelimitException("Rate limit exceeded.")
            elif response.status_code == 401:
                raise InvalidAPIKeyError()

            # 如果响应为其他错误状态码，抛出异常
            response.raise_for_status()

            # 如果响应成功，解析 JSON 数据
            json_response = response.json()

        # 解析 Bing 的响应
        web_pages = json_response.get("webPages", {})
        items = web_pages.get("value", [])

        results = []
        for item in items:
            results.append(
                SearchResult(
                    title=item.get("name", ""),
                    url=item.get("url", ""),
                    content=item.get("snippet", ""),
                )
            )

        return SearchResponse(query=query, results=results)
