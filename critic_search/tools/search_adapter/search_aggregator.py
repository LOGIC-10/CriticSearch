# critic_search/search_adapter/aggregator.py
import re
from asyncio import gather
from typing import Dict, List

from loguru import logger

from .duckduckgo_client import DuckDuckGoClient
from .exceptions import RetryError, UsageLimitExceededError
from .models import SearchResponse, SearchResponseList
from .tavily_client import TavilyClient
from .bing_client import BingClient

class SearchAggregator:
    def __init__(self):
        # Initialize supported search engines
        self.clients = {"tavily": TavilyClient(), "duckduckgo": DuckDuckGoClient(), "bing": BingClient(),}
        self.available_clients = set(self.clients.keys())

        # Define a regex pattern for identifying search operators
        self.search_operators_pattern = re.compile(
            r'(".*?"|\bsite:|filetype:|intitle:|inurl:|\b[-+~]\b)'
        )

    def mark_engine_unavailable(self, engine: str):
        """
        Mark a specific search engine as unavailable.

        Args:
            engine (str): The name of the engine to mark as unavailable.
        """
        if engine in self.available_clients:
            self.available_clients.remove(engine)

    def contains_search_operators(self, query: str) -> bool:
        """
        Check if a query contains special search operators.

        Args:
            query (str): The search query.

        Returns:
            bool: True if the query contains special operators, False otherwise.
        """
        return bool(self.search_operators_pattern.search(query))

    async def _search_single_query(
        self, query: str, engines: List[str]
    ) -> SearchResponse:
        for engine in engines:
            if engine in self.available_clients:
                try:
                    # Call the asynchronous search method for the specified engine
                    return await self.clients[engine].search(query)
                except UsageLimitExceededError:
                    # Mark the current engine as unavailable due to usage limits
                    logger.warning(
                        f"Engine {engine} is unavailable due to usage limits."
                    )
                    self.mark_engine_unavailable(engine)
                except RetryError:
                    logger.warning(
                        f"Engine '{engine}' for query: {query} failed after multiple retries. Marking as unavailable."
                    )
                    self.mark_engine_unavailable(engine)
                except Exception:
                    logger.exception(
                        f"Engine '{engine}' encountered error. Marking as unavailable."
                    )
                    self.mark_engine_unavailable(engine)

        logger.error("All specified search engines are unavailable.")
        return SearchResponse(
            query=query,
            error_message="Search failed: No available search engines for this query.",
        )

    async def search(self, query: List[str]) -> Dict[str, str]:
        """
        Asynchronous search method supporting multiple concurrent queries and engine fallback.

        Args:
            query (List[str]): A list of search queries.
        """
        # If query is a single string, convert it into a list with one element
        if isinstance(query, str):
            query = [query]

        query = query[:10]  # Limit the number of queries to k

        # Choose the engine dynamically based on whether the query contains search operators
        async def dynamic_engine_task(q: str):
            """
            动态选择引擎并执行任务。
            Args:
                q (str): 当前查询。
                delay (float): 延迟时间。
            """
            # 动态选择有效的引擎
            engines = (
                ["duckduckgo"]
                if self.contains_search_operators(q)
                else list(self.available_clients)
            )

            if not engines:
                raise ValueError(f"No available engines for query: {q}")
            return await self._search_single_query(q, engines)

        # Perform concurrent searches for multiple queries
        # 为每个任务动态添加延迟，但保持并发
        tasks = [dynamic_engine_task(q) for i, q in enumerate(query)]
        responses = await gather(*tasks)
        return SearchResponseList(responses=responses).model_dump()
