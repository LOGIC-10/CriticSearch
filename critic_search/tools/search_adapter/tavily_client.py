# critic_search/search_adapter/tavily_client.py
from typing import Literal

import httpx
from loguru import logger
from sqlmodel import Session, select

from .adapter_usage_db import (
    engine,
    get_current_time_of_new_york_naive,
    get_second_day_naive,
    initialize_db,
)
from .base_search_client import BaseSearchClient
from .exceptions import InvalidAPIKeyError, UsageLimitExceededError
from .models import SearchResponse, TavilyUsage


class TavilyClient(BaseSearchClient):
    """
    Tavily API client class.
    """

    def __init__(self):
        self.base_url = "https://api.tavily.com"
        self._api_key = "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"
        self.headers = {
            "Content-Type": "application/json",
        }
        initialize_db()

    def _increment_usage_count(self):
        """
        增加使用次数，如果达到上限则抛出异常
        """
        with Session(engine) as session:
            usage_record = session.exec(
                select(TavilyUsage).where(TavilyUsage.client_name == "TavilyClient")
            ).first()

            if not usage_record:
                # 如果记录不存在，则创建新记录
                usage_record = TavilyUsage(
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

    async def search(
        self,
        query: str,
        search_depth: Literal["basic", "advanced"] = "basic",
        topic: Literal["general", "news"] = "general",
        days: int = 7,
        max_results: int = 5,
    ) -> SearchResponse:
        """
        异步搜索方法
        """
        # 检查和更新使用次数
        self._increment_usage_count()

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
            response = await client.post(
                self.base_url + "/search", json=data, headers=self.headers
            )

        if response.status_code == 200:
            return SearchResponse.model_validate(response.json())
        elif response.status_code == 429:
            raise UsageLimitExceededError()
        elif response.status_code == 401:
            raise InvalidAPIKeyError()
        else:
            # 返回一个带错误信息的 SearchResponse，避免返回 None
            return SearchResponse(
                query=query,
                error_message=f"Unexpected status code: {response.status_code}. Response: {response.text}",
            )
