from typing import Literal

from duckduckgo_search import AsyncDDGS
from duckduckgo_search.exceptions import RatelimitException
from loguru import logger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_random,
)

from .base_search_client import BaseSearchClient
from .models import SearchResponse, SearchResult


class DuckDuckGoClient(BaseSearchClient):
    def _convert_days_to_timelimit(self, days: int) -> str:
        """
        Convert days to DuckDuckGo's timelimit format.

        Args:
            days (int): Number of days to filter results.

        Returns:
            str: A string representing DuckDuckGo's timelimit format ('d', 'w', 'm', 'y').
        """
        if days <= 1:
            return "d"  # Last 24 hours
        elif days <= 7:
            return "w"  # Last week
        elif days <= 30:
            return "m"  # Last month
        else:
            return "y"  # Last year

    @retry(
        stop=stop_after_attempt(5),  # 重试最多5次
        wait=wait_exponential(multiplier=1, min=4, max=30)
        + wait_random(min=1, max=5),  # 指数退避 + 随机抖动
        retry=retry_if_exception_type(RatelimitException),
    )
    async def search(
        self,
        query: str,
        days: int = 7,
        max_results: int = 10,
        region: Literal["us-en", "cn-zh"] = "us-en",
    ) -> SearchResponse:
        timelimit = self._convert_days_to_timelimit(days)

        logger.debug(
            f"Attempting to use 'duckduckgo-search-client' for query '{query}'."
        )

        raw_results = await AsyncDDGS(timeout=10).atext(
            query,
            region=region,
            safesearch="on",
            timelimit=timelimit,
            max_results=max_results,
        )

        results = [
            SearchResult(
                title=result["title"],
                url=result["href"],
                content=result["body"],
            )
            for result in raw_results
        ]
        return SearchResponse(
            query=query,
            results=results[:max_results],
        )
