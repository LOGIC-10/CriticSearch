from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class SearchClientUsage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    client_name: str = Field(default=None, index=True)
    usage_count: int = Field(default=0)
    max_usage: int = Field(default=1000)
    reset_time: datetime = Field(default=None)


class UniqueContent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str = Field(unique=True)


class HistoryQuery(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    query: str = Field(unique=True)
