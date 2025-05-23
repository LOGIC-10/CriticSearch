# critic_search/search_adapter/aggregator.py
from asyncio import gather
from typing import Dict, List

from criticsearch.config import settings
from criticsearch.rich_output import printer

from .bing_client import BingClient
from .exceptions import InvalidAPIKeyError, RetryError, UsageLimitExceededError
from .models import SearchResponse, SearchResponseList
from .tavily_client import TavilyClient


class SearchAggregator:
    def __init__(self):
        self.clients: Dict[str, TavilyClient | BingClient] = {}

        # 如果 Tavily 的 API key 存在，初始化客户端
        tavily_api_key = settings.tavily.api_key
        if tavily_api_key:
            self.clients["tavily"] = TavilyClient(tavily_api_key)

        # 如果 Bing 的 API key 存在，初始化客户端
        bing_api_key = settings.search_engine.bing.api_key
        if bing_api_key:
            self.clients["bing"] = BingClient(bing_api_key)

        self.available_clients = set(self.clients.keys())

    def mark_engine_unavailable(self, engine: str):
        """
        Mark a specific search engine as unavailable.

        Args:
            engine (str): The name of the engine to mark as unavailable.
        """
        if engine in self.available_clients:
            self.available_clients.remove(engine)

    async def _search_single_query(
        self, query: str, engines: List[str]
    ) -> SearchResponse:
        for engine in engines:
            if engine in self.available_clients:
                try:
                    # Call the asynchronous search method for the specified engine
                    result = await self.clients[engine].search(query)
                    printer.log(f"{result.model_dump()}")
                    return result
                except RetryError:
                    printer.log(
                        f"Engine '{engine}' for query: {query} failed after multiple retries. Marking as unavailable."
                    )
                    self.mark_engine_unavailable(engine)
                except InvalidAPIKeyError:
                    printer.log(
                        f"Engine '{engine}' for query: {query} failed because of wrong api key. Marking as unavailable."
                    )
                    self.mark_engine_unavailable(engine)
                except UsageLimitExceededError:
                    printer.log(
                        f"Engine '{engine}' for query: {query} failed because of usage limit exceeded. Marking as unavailable."
                    )
                    self.mark_engine_unavailable(engine)
                except Exception:
                    printer.print_exception(
                        f"Engine '{engine}' encountered error. Marking as unavailable."
                    )
                    self.mark_engine_unavailable(engine)

        printer.log("All specified search engines are unavailable.", style="bold red")
        return SearchResponse(
            query=query,
            error_message="Search failed: No available search engines for this query.",
        )

    async def search(self, query: List[str]) -> str:
        """
        Performs a search using the provided query.
        Supports various search techniques using special syntax.

        Args:
            query (List[str]): A list of search queries.
        """
        # Get the list of currently available search engines
        engines = list(self.available_clients)
        if not engines:
            raise ValueError("No available engines to perform the search.")

        # Create tasks for concurrent search
        tasks = [self._search_single_query(q, engines) for q in query]

        # Execute all tasks and gather the responses
        responses = await gather(*tasks)

        # Return the search responses as a dictionary
        return SearchResponseList(responses=responses).model_dump()  # type: ignore
