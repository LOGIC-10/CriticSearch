from threading import Lock
from typing import Dict, Set

from loguru import logger
from niquests import Session
from niquests.models import Response

from .db.database import recreate_db
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
    _engines: Dict[str, SearchEngineBase] = {}
    _lock = Lock()
    _engines_loaded = False

    @classmethod
    def set_engines(mcs, engines: Dict[str, SearchEngineBase]):
        """
        存储搜索引擎实例到元类，便于共享
        """
        mcs._engines.update(engines)

    def __call__(cls, *args, **kwargs):
        """
        实例化时直接复用元类中存储的 _engines，并确保只加载一次引擎。
        """
        with cls._lock:
            if not cls._engines_loaded:
                instance = super().__call__(*args, **kwargs)
                instance._load_engines_from_settings()
                recreate_db()
                logger.info("Engines loaded.")
                cls._engines_loaded = True
        return super().__call__(*args, **kwargs)
