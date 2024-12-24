# critic_search/tools/search_adapter/models.py
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, model_serializer
from sqlmodel import Field, SQLModel

from critic_search.log import logger


class SearchResult(BaseModel):
    title: str
    url: str
    content: str


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult] = Field(default_factory=list)
    error_message: Optional[str] = None

    @model_serializer
    def ser_model(self) -> str:
        if self.error_message:
            formatted_response = (
                f"\nQuery: {self.query}\nError: {self.error_message}\n" + "-" * 50
            )
        elif self.results == []:
            formatted_response = (
                f"\nQuery: {self.query}\nError: No results found." + "-" * 50
            )
        else:
            formatted_response = f"\nQuery: {self.query}\nSearch Results:\n" + "-" * 50
            for i, res in enumerate(self.results, 1):
                formatted_response += (
                    f"\n[{i}]:\nTITLE: {res.title}\nURL: {res.url}\nCONTENT: {res.content}\n"
                    + "-" * 50
                )
        return formatted_response


class SearchResponseList(BaseModel):
    responses: List[SearchResponse] = Field(default_factory=list)

    @model_serializer
    def ser_model(self) -> str:
        """
        Serialize the list of SearchResponse objects into a dictionary,
        ensuring unique content across queries.

        Returns:
            Dict[str, str]: A dictionary where the key is the query,
                            and the value is a formatted string representation of the search response.
        """
        global_seen_contents = set()  # 全局去重逻辑
        total_results = 0
        unique_results_count = 0
        result_str = ""

        for response in self.responses:
            if response.error_message:
                logger.debug(
                    f"Skipping serialize query '{response.query}' due to error: {response.error_message}"
                )
                continue  # 跳过有 error_message 的响应

            unique_results = []
            for res in response.results:
                total_results += 1
                if res.content not in global_seen_contents:
                    global_seen_contents.add(res.content)
                    unique_results.append(res)

            # 将去重后的结果更新到当前 response
            response.results = unique_results
            unique_results_count += len(unique_results)
            result_str += response.model_dump()  # type: ignore

        # 打印提示信息
        duplicates_removed = total_results - unique_results_count
        logger.success(
            f"Serialization completed. Total results: {total_results}, "
            f"Unique results: {unique_results_count}, "
            f"Duplicates removed: {duplicates_removed}."
        )

        return result_str


class SearchClientUsage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    client_name: str = Field(default=None, index=True)
    usage_count: int = Field(default=0)
    max_usage: int = Field(default=1000)
    reset_time: datetime = Field(default=None)  # 初始值为 None


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
