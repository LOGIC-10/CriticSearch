# critic_search/search_adapter/aggregator.py
from asyncio import gather
from typing import List

from loguru import logger

from .duckduckgo_client import DuckDuckGoClient
from .exceptions import UsageLimitExceededError
from .models import SearchResponse, SearchResponseList
from .tavily_client import TavilyClient


class SearchAggregator:
    def __init__(self):
        # 初始化支持的搜索引擎
        self.clients = {"tavily": TavilyClient(), "dcuckduckgo": DuckDuckGoClient()}
        self.available_clients = set(self.clients.keys())

    def mark_engine_unavailable(self, engine: str):
        """
        将指定的引擎标记为不可用。
        """
        if engine in self.available_clients:
            self.available_clients.remove(engine)

    async def _search_single_query(
        self, query: str, engines: List[str]
    ) -> SearchResponse:
        """
        搜索单个关键词，按指定的引擎顺序尝试。

        Args:
            query (str): 搜索关键词。
            engines (List[str]): 搜索引擎列表。

        Returns:
            SearchResponse: 搜索结果。
        """
        for engine in engines:
            if engine in self.available_clients:
                try:
                    # 调用指定引擎的异步搜索方法
                    return await self.clients[engine].search(query)
                except UsageLimitExceededError:
                    # 标记当前引擎为不可用
                    self.mark_engine_unavailable(engine)
                    logger.warning(
                        f"Engine {engine} is unavailable due to usage limits."
                    )
                except Exception as e:
                    logger.error(f"Error occurred in {engine} search: {e}")
        raise ValueError("All specified engines are unavailable.")

    @logger.catch
    async def search(self, query: List[str], engines: List[str] | None = None) -> str:
        """
        异步搜索方法，支持多个关键词并发搜索和自动切换引擎。

        Args:
            query (List[str]): 搜索关键词列表。
            engines (List[str], optional): 可选的搜索引擎列表（从 available_clients 中筛选）。
        """
        engines = engines or list(self.available_clients)

        # 多个关键词并发搜索
        tasks = [self._search_single_query(q, engines) for q in query]
        responses = await gather(*tasks)
        return SearchResponseList(responses=responses).model_dump()  # type: ignore
