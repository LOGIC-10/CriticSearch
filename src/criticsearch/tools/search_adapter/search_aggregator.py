from threading import Lock
from typing import Dict, List, Set

from loguru import logger
from niquests import Session
from niquests.models import Response
from tenacity import RetryError
from urllib3_future.util import Retry

from criticsearch.config import settings

from .base import SearchAggregatorMeta, SearchEngineBase
from .bing_client import BingSearchEngine
from .duckduckgo_client import DuckDuckGoSearchEngine
from .models import SearchResponse, SearchResponseList
from .serpapi_client import SerpAPISearchEngine
from .tavily_client import TavilySearchEngine

retries = Retry(
    total=5,  # Retry up to 5 times
    backoff_factor=1,  # Exponential backoff (1s, 2s, 4s, 8s, ...)
    backoff_max=10,  # Cap the delay at 10 seconds
    status_forcelist=[429, 500, 502, 503, 504],  # Retry on these HTTP codes
    raise_on_status=False,
)


class SearchAggregator(metaclass=SearchAggregatorMeta):
    _unavailable_engines: Set[str] = set()

    def __init__(self):
        """
        在构造方法中，如果引擎实例还没有加载过，则加载一次。
        """
        self.engines = type(self)._engines

    def _load_engines_from_settings(self):
        """
        从 settings 中加载配置并初始化搜索引擎实例。
        """
        # 从 settings 中获取 API keys
        tavily_key = settings.search_engine.tavily.api_key
        serpapi_key = settings.search_engine.serpapi.api_key
        bing_key = settings.search_engine.bing.api_key

        # 初始化引擎实例
        engines = {}

        if "tavily" not in self._unavailable_engines and tavily_key:
            engines["tavily"] = TavilySearchEngine(api_key=tavily_key)

        if "serpapi" not in self._unavailable_engines and serpapi_key:
            engines["serpapi"] = SerpAPISearchEngine(api_key=serpapi_key)

        if "bing" not in self._unavailable_engines and bing_key:
            engines["bing"] = BingSearchEngine(api_key=bing_key)

        # 存储到元类
        type(self).set_engines(engines)

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

        # Limit the number of queries to search when debugging
        queries = queries[: settings.search_max_queries]

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
