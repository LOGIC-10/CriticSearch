# critic_search/search_adapter/aggregator.py
import re
from asyncio import gather
from typing import List

from loguru import logger

from .duckduckgo_client import DuckDuckGoClient
from .exceptions import UsageLimitExceededError
from .models import SearchResponse, SearchResponseList
from .tavily_client import TavilyClient


class SearchAggregator:
    def __init__(self):
        # Initialize supported search engines
        self.clients = {"tavily": TavilyClient(), "duckduckgo": DuckDuckGoClient()}
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
        """
        Perform a search for a single query, trying the specified engines in order.

        Args:
            query (str): The search query.
            engines (List[str]): A list of search engines to try.

        Returns:
            SearchResponse: The search result.

        Raises:
            ValueError: If all specified engines are unavailable.
        """
        for engine in engines:
            if engine in self.available_clients:
                try:
                    # Call the asynchronous search method for the specified engine
                    return await self.clients[engine].search(query)
                except UsageLimitExceededError:
                    # Mark the current engine as unavailable due to usage limits
                    self.mark_engine_unavailable(engine)
                    logger.warning(
                        f"Engine {engine} is unavailable due to usage limits."
                    )
        raise ValueError("All specified engines are unavailable.")

    @logger.catch
    async def search(self, query: List[str], engines: List[str] | None = None) -> str:
        """
        Asynchronous search method supporting multiple concurrent queries and engine fallback.

        Args:
            query (List[str]): A list of search queries.
            engines (List[str], optional): An optional list of search engines to use (from available clients).

        Returns:
            str: A serialized representation of the search results.
        """
        engines = engines or list(self.available_clients)

        # Choose the engine dynamically based on whether the query contains search operators
        query_engines = [
            ["duckduckgo"] if self.contains_search_operators(q) else engines
            for q in query
        ]

        # Perform concurrent searches for multiple queries
        tasks = [
            self._search_single_query(q, eng) for q, eng in zip(query, query_engines)
        ]
        responses = await gather(*tasks)
        return SearchResponseList(responses=responses).model_dump()  # type: ignore
