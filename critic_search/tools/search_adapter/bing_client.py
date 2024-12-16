from typing import Dict

from .base import SearchEngineBase
from .models import SearchResponse, SearchResult


class BingSearchEngine(SearchEngineBase):
    API_URL = "https://api.bing.microsoft.com/v7.0/search"
    METHOD = "get"

    def __init__(self, api_key: str):
        self._api_key = api_key

    def build_request_data(self, query: str) -> Dict:
        """
        Constructs the data dictionary for the Bing API request.
        """
        return {
            "q": query,
            "count": 10,  # Number of results to fetch
            "responseFilter": "Webpages",  # What kind of results we are looking for
            "headers": {"Ocp-Apim-Subscription-Key": self._api_key},
        }

    def process_response(self, resp_json: Dict) -> SearchResponse:
        """
        Processes the response from Bing API and converts it to a SearchResponse object.
        """
        web_pages = resp_json.get("webPages", {})
        items = web_pages.get("value", [])
        query_from_response = resp_json.get("queryContext", {}).get(
            "originalQuery", "Unknown Query"
        )
        results = [
            SearchResult(
                title=item.get("name", ""),
                url=item.get("url", ""),
                content=item.get("snippet", ""),
            )
            for item in items
        ]
        return SearchResponse(query=query_from_response, results=results)
