from typing import Dict

from .base import SearchEngineBase
from .models import SearchResponse, SearchResult


class TavilySearchEngine(SearchEngineBase):
    API_URL = "https://api.tavily.com/search"
    METHOD = "post"

    def __init__(self, api_key: str):
        self._api_key = api_key

    def build_request_data(self, query: str) -> Dict:
        return {
            "query": query,
            "api_key": self._api_key,
            "headers": {"Content-Type": "application/json"},
        }

    def process_response(self, resp_json: Dict) -> SearchResponse:
        query_from_response = resp_json.get("query", "Unknown Query")
        search_results = resp_json.get("results", [])
        results = [
            SearchResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                content=r.get("content", ""),
            )
            for r in search_results
        ]
        return SearchResponse(query=query_from_response, results=results)
