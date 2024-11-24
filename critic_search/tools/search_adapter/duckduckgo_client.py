from typing import Literal

import httpx
from duckduckgo_search import AsyncDDGS

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

    async def _fallback_search(self, query: str, max_results: int) -> SearchResponse:
        """
        Fallback search method using an alternative HTTP request to a local search API.

        Args:
            query (str): Search query.
            max_results (int): Maximum number of results to fetch.

        Returns:
            SearchResponse: The structured search response from the fallback.
        """
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                "http://localhost:8000/search",
                params={"q": query, "max_results": max_results},
            )
            response.raise_for_status()

            raw_results = response.json().get("results", [])
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
                results=results,
            )

    async def search(
        self,
        query: str,
        days: int = 7,
        max_results: int = 10,
        region: Literal["us-en", "cn-zh"] = "us-en",
    ) -> SearchResponse:
        """
        Perform a search using DuckDuckGo. Fallbacks to an alternative search if DuckDuckGo fails.

        Args:
            query (str): Search query.
            days (int): Number of days to filter results (converted to timelimit).
            max_results (int): Maximum number of results.
            region (Literal): Region for the search.

        Returns:
            SearchResponse: The structured search response.
        """
        timelimit = self._convert_days_to_timelimit(days)

        try:
            async with AsyncDDGS() as ddgs:
                raw_results = await ddgs.atext(
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
                    results=results,
                )
        except Exception as e:
            # Log the error (optional)
            print(f"DuckDuckGo search failed: {e}. Switching to fallback...")
            # Perform fallback search
            return await self._fallback_search(query, max_results)
