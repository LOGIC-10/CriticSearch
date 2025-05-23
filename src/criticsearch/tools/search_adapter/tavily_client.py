# critic_search/search_adapter/tavily_client.py
from typing import Literal

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_random,
)

from ...config import settings
from ...rich_output import printer
from .base_search_client import BaseSearchClient
from .exceptions import InvalidAPIKeyError, RatelimitException, UsageLimitExceededError, TavilySearchError
from .models import SearchResponse


class TavilyClient(BaseSearchClient):
    """
    Tavily API client class.
    """

    def __init__(self, api_key: str):
        self.base_url = "https://api.tavily.com"
        self._api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
        }

    @retry(
        stop=stop_after_attempt(5),  # 重试最多5次
        wait=wait_exponential(multiplier=1, min=4, max=30)
        + wait_random(min=1, max=5),  # 指数退避 + 随机抖动
        retry=retry_if_exception_type(RatelimitException),
    )
    async def search(
        self,
        query: str,
        search_depth: Literal["basic", "advanced"] = "basic",
        topic: Literal["general", "news"] = "general",
        days: int = 7,
        max_results: int = getattr(settings, "max_results", 10) or 10,
    ) -> SearchResponse:
        """
        异步搜索方法
        """

        # 发起异步请求
        data = {
            "query": query,
            "search_depth": search_depth,
            "topic": topic,
            "days": days,
            "max_results": max_results,
            "api_key": self._api_key,
        }

        async with httpx.AsyncClient(timeout=30, http2=True) as client:
            response = await client.post(
                self.base_url + "/search", json=data, headers=self.headers
            )

        if response.status_code == 200:
            return SearchResponse.model_validate(response.json())
        elif response.status_code == 429:
            try:
                detail = response.json().get("detail", {}).get("error")
                if detail:
                    raise UsageLimitExceededError(detail)  # 抛出后直接传播，不被捕获
            except UsageLimitExceededError:
                raise  # 直接传播 UsageLimitExceededError，避免被后续捕获
            except Exception:
                # 捕获其他异常并记录日志
                printer.print_exception(
                    f"Failed to process 429 response. Response: {response.text}"
                )
                raise RatelimitException()  # 抛出通用限流异常
        elif response.status_code == 401:
            raise InvalidAPIKeyError()
        elif response.status_code == 400:  # 新增对 400 Bad Request 的显式处理
            error_detail = "Bad Request"
            try:
                error_data = response.json()
                error_detail = error_data.get("detail", {}).get("error", response.text)
            except Exception:
                error_detail = response.text  # 如果响应不是JSON或解析失败
            printer.log(f"Tavily API Error 400 for query '{query}': {error_detail}", style="bold red")
            raise TavilySearchError(f"Tavily API Error (400) for query '{query}': {error_detail}")
        else:
            # 对于所有其他未明确处理的错误状态码，也应该抛出异常
            printer.log(f"Tavily API Unexpected status code {response.status_code} for query '{query}'. Response: {response.text}", style="bold red")
            raise TavilySearchError(
                f"Unexpected status code from Tavily API: {response.status_code}. Response: {response.text}"
            )
