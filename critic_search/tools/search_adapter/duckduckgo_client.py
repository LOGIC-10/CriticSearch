from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import RatelimitException
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_random,
)

from .models import SearchResponse, SearchResult


class DuckDuckGoSearchEngine:
    @retry(
        stop=stop_after_attempt(5),  # 重试最多5次
        wait=wait_exponential(multiplier=1, min=4, max=30)
        + wait_random(min=1, max=5),  # 指数退避 + 随机抖动
        retry=retry_if_exception_type(RatelimitException),
    )
    @staticmethod
    def search(query: str):
        ddg_results = DDGS().text(query, max_results=10)
        results = [
            SearchResult(
                title=item.get("title", ""),
                url=item.get("href", ""),
                content=item.get("body", ""),
            )
            for item in ddg_results
        ]
        return SearchResponse(query=query, results=results)
