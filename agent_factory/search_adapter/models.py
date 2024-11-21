# agent_factory/search_adapter/models.py
from pydantic import BaseModel, Field
from typing import Optional, List


class SearchResult(BaseModel):
    title: str
    url: str
    content: str
    score: float
    published_date: Optional[str] = None


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult] = Field(default_factory=list)
    response_time: float
