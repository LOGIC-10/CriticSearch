# agent_factory/search_adapter/tavily_client.py
import httpx
from typing import Literal
from .exceptions import InvalidTavilyAPIKeyError, UsageLimitExceededError
from .base_client import BaseSearchClient
from .models import SearchResponse


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

    def search(
        self,
        query: str,
        search_depth: Literal["basic", "advanced"] = "basic",
        topic: Literal["general", "news"] = "general",
        days: int = 7,
        max_results: int = 10,
    ) -> SearchResponse:
        """
        Internal search method to send the request to the API.
        """

        data = {
            "query": query,
            "search_depth": search_depth,
            "topic": topic,
            "days": days,
            "max_results": max_results,
            "api_key": self._api_key,
        }

        with httpx.Client(timeout=30) as client:
            response = client.post(
                self.base_url + "/search", json=data, headers=self.headers
            )

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            detail = "Too many requests."
            try:
                detail = response.json().get("detail", {}).get("error", detail)
            except Exception:
                pass
            raise UsageLimitExceededError(detail)
        elif response.status_code == 401:
            raise InvalidTavilyAPIKeyError()
        else:
            response.raise_for_status()  # Raises HTTPStatusError if the request returned an unsuccessful status code

        return SearchResponse.model_validate(response.json())
