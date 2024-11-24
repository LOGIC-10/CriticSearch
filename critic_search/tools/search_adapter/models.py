# agent_factory/search_adapter/models.py
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, model_serializer
from sqlmodel import Field, SQLModel


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


class SearchResponseList(BaseModel):
    responses: List[SearchResponse] = Field(default_factory=list)

    @model_serializer
    def ser_model(self) -> str:
        """
        Serialize the list of SearchResponse objects into a formatted string.

        Returns:
            str: A formatted string representation of the search response list.
        """
        result = []
        for response in self.responses:
            result.append(f"Query: {response.query}\nSearch Results:\n" + "-" * 50)
            for i, res in enumerate(response.results, 1):
                result.append(
                    f"[{i}]:\nTITLE: {res.title}\nURL: {res.url}\nCONTENT: {res.content}\n"
                    + "-" * 50
                )
            result.append("\n")
        return "\n".join(result)


class TavilyUsage(SQLModel, table=True):
    """
    数据库模型，用于记录 TavilyClient 的使用次数
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    client_name: str = Field(default="TavilyClient", index=True)
    usage_count: int = Field(default=0)
    max_usage: int = Field(default=1000)  # 假设一个月最大调用次数
    reset_time: datetime = Field(default=None)  # 下次重置时间


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
