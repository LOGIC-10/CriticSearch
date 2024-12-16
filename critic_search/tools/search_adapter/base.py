from typing import Dict

from niquests import Session
from niquests.models import Response

from .models import SearchResponse


class SearchEngineBase:
    API_URL: str
    METHOD: str

    def build_request_data(self, query: str) -> dict:
        """Build the request payload before sending."""
        raise NotImplementedError

    def process_response(self, resp_json: Dict) -> SearchResponse:
        """Process JSON from the response and return a Pydantic SearchResponse."""
        raise NotImplementedError

    def make_request(
        self, session: Session, method: str, url: str, data: Dict
    ) -> Response:
        """Make an HTTP request using Niquests session."""

        headers = data.get("headers", None)

        # 如果存在 headers 字段，删除它
        if "headers" in data:
            del data["headers"]

        if method == "get":
            return session.get(url=url, params=data, headers=headers)
        elif method == "post":
            return session.post(url=url, json=data, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")


class SearchAggregatorMeta(type):
    _api_keys: Dict[str, str] = {}

    @classmethod
    def set_api_keys(mcs, api_keys: Dict[str, str]):
        mcs._api_keys.update(api_keys)

    def __call__(cls, *args, **kwargs):
        instance = super().__call__(*args, **kwargs)
        return instance
