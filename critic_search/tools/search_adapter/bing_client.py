# critic_search/search_adapter/bing_client.py
import os
from typing import Literal

import httpx
from loguru import logger

from .base_search_client import BaseSearchClient
from .models import SearchResponse, SearchResult


class BingClient(BaseSearchClient):
    """
    Bing Search API client.
    """

    def __init__(self):
        self.base_url = "https://api.bing.microsoft.com/v7.0/search"
        # self.api_key = os.environ.get("BING_API_KEY")
        self.api_key = "be5b506c3ddc4773807826deccb26a79"
        if not self.api_key:
            raise ValueError("BING_API_KEY environment variable is not set.")

    async def search(
        self,
        query: str,
        days: int = 7,        # Not all search engines use this the same way. Bing doesn't have a direct "days" parameter.
        max_results: int = 5,
        region: Literal["us-en", "cn-zh"] = "us-en"
    ) -> SearchResponse:
        """
        Perform an asynchronous search on Bing.

        Args:
            query (str): The search query.
            days (int, optional): Time limit in days. Bing doesn't support direct day filtering similarly, 
                                  so you can ignore or implement custom logic.
            max_results (int, optional): Maximum number of results to return.
            region (Literal["us-en", "cn-zh"], optional): Region or language code for the search.

        Returns:
            SearchResponse: Pydantic model containing the search results.
        """
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key
        }

        # You could add a 'mkt' parameter to target a specific market.
        # For example, "mkt": "en-US".
        params = {
            "q": query,
            "count": max_results,
            # You can add additional Bing parameters here if needed.
        }

        logger.debug(f"Using 'bing' for query '{query}'.")

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(self.base_url, headers=headers, params=params)
            response.raise_for_status()
            json_response = response.json()

        # Parse the Bing response
        web_pages = json_response.get("webPages", {})
        items = web_pages.get("value", [])

        results = []
        for item in items:
            results.append(
                SearchResult(
                    title=item.get("name", ""),
                    url=item.get("url", ""),
                    content=item.get("snippet", "")
                )
            )

        return SearchResponse(query=query, results=results)
