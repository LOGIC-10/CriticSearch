# critic_search/search_adapter/tavily_client.py
from typing import Literal

import httpx
from loguru import logger
from sqlmodel import Session, select
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_random,
)

from .base_search_client import BaseSearchClient
from .exceptions import InvalidAPIKeyError, RatelimitException, UsageLimitExceededError
from .models import SearchClientUsage, SearchResponse
from .search_client_usage_db import (
    engine,
    get_current_time_of_new_york_naive,
    get_second_day_naive,
)


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

    def _increment_usage_count(self):
        """
        增加使用次数，如果达到上限则抛出异常
        """
        with Session(engine) as session:
            usage_record = session.exec(
                select(SearchClientUsage).where(
                    SearchClientUsage.client_name == "TavilyClient"
                )
            ).first()

            if not usage_record:
                # 如果记录不存在，则创建新记录
                usage_record = SearchClientUsage(
                    client_name="TavilyClient",
                    usage_count=0,
                )
                session.add(usage_record)

            # 检查是否达到使用上限
            if usage_record.usage_count >= usage_record.max_usage:
                if get_current_time_of_new_york_naive() >= usage_record.reset_time:
                    logger.debug("Reset time reached. Resetting usage count.")
                    # 重置计数器
                    usage_record.usage_count = 0
                    usage_record.reset_time = get_second_day_naive()
                else:
                    raise UsageLimitExceededError("Monthly usage limit reached.")

            # 增加使用次数
            usage_record.usage_count += 1
            session.commit()

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
        max_results: int = 10,
    ) -> SearchResponse:
        """
        异步搜索方法
        """

        logger.debug(f"Attempting to use engine 'Tavily' for query '{query}'. ")

        # 发起异步请求
        data = {
            "query": query,
            "search_depth": search_depth,
            "topic": topic,
            "days": days,
            "max_results": max_results,
            "api_key": self._api_key,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            # 检查和更新使用次数
            self._increment_usage_count()

            response = await client.post(
                self.base_url + "/search", json=data, headers=self.headers
            )

        if response.status_code == 200:
            return SearchResponse.model_validate(response.json())
        elif response.status_code == 429:
            try:
                detail = response.json().get("detail", {}).get("error")
                if detail:
                    raise UsageLimitExceededError(detail)
            except Exception:
                pass

            raise RatelimitException()
        elif response.status_code == 401:
            raise InvalidAPIKeyError()
        else:
            return SearchResponse(
                query=query,
                error_message=f"Unexpected status code: {response.status_code}. Response: {response.text}",
            )
