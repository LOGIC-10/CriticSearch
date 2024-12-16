from threading import Lock
from typing import Dict, List, Set

from loguru import logger
from niquests import Session
from niquests.models import Response
from tenacity import RetryError
from urllib3.util import Retry

from critic_search.config import settings

from .base import SearchAggregatorMeta, SearchEngineBase
from .bing_client import BingSearchEngine
from .db.database import initialize_db
from .duckduckgo_client import DuckDuckGoSearchEngine
from .models import SearchResponse, SearchResponseList
from .serpapi_client import SerpAPISearchEngine
from .tavily_client import TavilySearchEngine

retries = Retry(
    total=5,  # Retry up to 5 times
    backoff_factor=1,  # Exponential backoff (1s, 2s, 4s, 8s, ...)
    backoff_max=10,  # Cap the delay at 10 seconds
    status_forcelist=[429, 500, 502, 503, 504],  # Retry on these HTTP codes
)


class SearchAggregator(metaclass=SearchAggregatorMeta):
    _unavailable_engines: Set[str] = set()
    _lock = Lock()

    # 标识是否已经从 settings 中加载过 API Key
    _keys_loaded = False

    def __init__(self):
        """
        在构造方法里，如果还没有加载过，则自动从 settings 读取 API Keys 并存进元类。
        这样就不需要应用在外部显式调用 set_api_keys。
        """
        with self._lock:
            # 如果还没加载过，就从 settings 读取
            if not self._keys_loaded:
                self._load_api_keys_from_settings()
                initialize_db()

                self._keys_loaded = True

        self.engines: Dict[str, SearchEngineBase] = {}

        # 取出元类中存储的全部key
        all_keys = type(self)._api_keys

        if "tavily" not in self._unavailable_engines:
            tavily_key = all_keys.get("tavily")
            if tavily_key:
                self.engines["tavily"] = TavilySearchEngine(api_key=tavily_key)

        # 如果 serpapi key 不存在，就不初始化 serpapi
        if "serpapi" not in self._unavailable_engines:
            serpapi_key = all_keys.get("serpapi")
            if serpapi_key:
                self.engines["serpapi"] = SerpAPISearchEngine(api_key=serpapi_key)

        # 如果 bing key 不存在，就不初始化 bing
        if "bing" not in self._unavailable_engines:
            bing_key = all_keys.get("bing")
            if bing_key:
                self.engines["bing"] = BingSearchEngine(api_key=bing_key)

    def _load_api_keys_from_settings(self):
        """
        只在第一次需要时，从 settings 中读取并写进元类，
        之后就可以直接从元类 _api_keys 获取。
        """
        # 拿到 tavily / serpapi 的值
        tavily_key = settings.search_engine.tavily.api_key
        serpapi_key = settings.search_engine.serpapi.api_key
        bing_key = settings.search_engine.bing.api_key

        # 调用元类的 set_api_keys 来存储它们
        type(self).set_api_keys(
            {"tavily": tavily_key, "serpapi": serpapi_key, "bing": bing_key}
        )

    @classmethod
    def mark_engine_unavailable(cls, engine_name: str):
        with cls._lock:
            cls._unavailable_engines.add(engine_name)

    @classmethod
    def is_engine_unavailable(cls, engine_name: str) -> bool:
        """检查引擎是否已经被标记为不可用"""
        with cls._lock:
            return engine_name in cls._unavailable_engines

    @logger.catch
    def search(self, queries: List[str]) -> str:
        final_responses = []

        # Start with all queries
        remaining_queries = queries

        # Attempt each engine in order
        for engine_name, engine in self.engines.items():
            raw_responses: List[Response] = []

            logger.info(f"Trying engine {engine_name}.")

            # Make requests for all remaining queries
            with Session(multiplexed=True, retries=retries) as s:
                for q in remaining_queries:
                    data = engine.build_request_data(q)
                    raw_responses.append(
                        engine.make_request(
                            session=s,
                            method=getattr(engine, "METHOD", "").lower(),
                            url=getattr(engine, "API_URL", "").lower(),
                            data=data,
                        ),
                    )
                s.gather()  # Actually send the requests

            # Process the responses

            for index, resp in enumerate(raw_responses):
                if resp.status_code == 200:
                    resp_json = resp.json()
                    parsed = engine.process_response(resp_json)
                    final_responses.append(parsed)
                    remaining_queries.remove(parsed.query)
                else:
                    remaining_queries = queries[index:]

                    logger.error(
                        f"Engine {engine_name} failed with status code {resp.status_code}: {resp.text}. Marking as unavailable."
                    )
                    self.mark_engine_unavailable(engine_name)

                    break

            if len(final_responses) > 1:
                logger.info(
                    f"Successfully processed {len(final_responses)} queries with {engine_name}"
                )

            # If there's nothing left to do, break early
            if not remaining_queries:
                break

        if remaining_queries:
            logger.info(f"Trying engine DuckDuckGo.")

        # If there's still queries left after trying the main engines, fallback to DuckDuckGo
        for query in remaining_queries:
            try:
                ddg_responses = DuckDuckGoSearchEngine.search(query)
                final_responses.append(ddg_responses)
            except RetryError:
                final_responses.append(
                    SearchResponse(
                        query=query, error_message="DuckDuckGo failed to return results"
                    )
                )

        search_response = SearchResponseList(responses=final_responses).model_dump()

        assert isinstance(search_response, str)

        return search_response
