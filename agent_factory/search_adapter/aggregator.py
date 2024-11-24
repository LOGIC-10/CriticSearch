from typing import List

from .models import SearchResponse
from .tavily_client import TavilyClient


class SearchAggregator:
    def __init__(self):
        # 默认使用 Tavily 客户端
        self.default_client = TavilyClient()

    def search(self, query: str, engines: List[str] = None) -> SearchResponse:
        """
        搜索方法，默认使用 Tavily 进行搜索，返回直接的搜索结果。

        Args:
            query (str): 搜索关键词。
            engines (List[str], optional): 可选的搜索引擎列表（当前忽略）。
        """
        # 当前只支持 Tavily，因此直接调用默认客户端的搜索方法
        return self.default_client.search(query)