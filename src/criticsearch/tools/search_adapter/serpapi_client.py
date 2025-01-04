from typing import Dict

from .base import SearchEngineBase
from .models import SearchResponse, SearchResult


class SerpAPISearchEngine(SearchEngineBase):
    API_URL = "https://serpapi.com/search"
    METHOD = "get"

    def __init__(self, api_key: str):
        self._api_key = api_key

    def build_request_data(self, query: str) -> dict:
        return {
            "q": query,
            "api_key": self._api_key,
        }

    def process_response(self, resp_json: Dict) -> SearchResponse:
        query_from_response = resp_json.get("search_parameters", {}).get(
            "q", "Unknown Query"
        )
        organic_results = resp_json.get("organic_results", [])
        results = []
        for result in organic_results:
            results.append(
                SearchResult(
                    title=result.get("title", ""),
                    url=result.get("link", ""),
                    content=result.get("snippet", ""),
                )
            )

        return SearchResponse(query=query_from_response, results=results)
