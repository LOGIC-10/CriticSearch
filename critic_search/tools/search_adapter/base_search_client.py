from abc import ABC, abstractmethod
from typing import Any


class BaseSearchClient(ABC):
    @abstractmethod
    async def search(self, query: str, **kwargs: Any) -> Any:
        pass
