# agent_factory/search_adapter/models.py
from datetime import datetime
from typing import Dict, List, Optional

from colorama import Fore, Style, init
from loguru import logger
from pydantic import BaseModel, Field, model_serializer
from sqlmodel import Field, SQLModel

from .adapter_usage_db import get_second_day_naive


class SearchResult(BaseModel):
    title: str
    url: str
    content: str
    score: Optional[float] = None
    published_date: Optional[str] = None


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult] = Field(default_factory=list)
    response_time: Optional[float] = None
    error_message: Optional[str] = None


class SearchResponseList(BaseModel):
    responses: List[SearchResponse] = Field(default_factory=list)

    @model_serializer
    def ser_model(self) -> Dict[str, str]:
        """
        Serialize the list of SearchResponse objects into a dictionary.

        Returns:
            Dict[str, str]: A dictionary where the key is the query,
                            and the value is a formatted string representation of the search response.
        """
        result = {}
        for response in self.responses:
            if response.error_message:
                formatted_response = (
                    f"Query: {response.query}\nError: {response.error_message}\n"
                    + "-" * 50
                )
            else:
                formatted_response = (
                    f"Query: {response.query}\nSearch Results:\n" + "-" * 50
                )
                for i, res in enumerate(response.results, 1):
                    formatted_response += (
                        f"\n[{i}]:\nTITLE: {res.title}\nURL: {res.url}\nCONTENT: {res.content}\n"
                        + "-" * 50
                    )
            result[response.query] = formatted_response

            logger.info(
                f"\n{Fore.GREEN}{'=' * 20}== SEARCH_RESULTS =={'=' * 20}{Style.RESET_ALL}\n{formatted_response}\n"
            )

        return result


class TavilyUsage(SQLModel, table=True):
    """
    数据库模型，用于记录 TavilyClient 的使用次数
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    client_name: str = Field(default="TavilyClient", index=True)
    usage_count: int = Field(default=0)
    max_usage: int = Field(default=1000)
    reset_time: datetime = Field(default_factory=lambda: get_second_day_naive())


if __name__ == "__main__":
    response_1 = SearchResponse(
        query="Python programming",
        results=[
            SearchResult(
                title="Python.org",
                url="https://www.python.org",
                content="Official Python website.",
            ),
            SearchResult(
                title="Learn Python",
                url="https://www.learnpython.org",
                content="Interactive Python tutorial.",
            ),
        ],
    )

    response_2 = SearchResponse(
        query="Asynchronous programming",
        results=[
            SearchResult(
                title="AsyncIO",
                url="https://docs.python.org/3/library/asyncio.html",
                content="Official AsyncIO documentation.",
            ),
        ],
    )

    response_list = SearchResponseList(responses=[response_1, response_2])

    dumped_data = response_list.model_dump()
    print(dumped_data)
