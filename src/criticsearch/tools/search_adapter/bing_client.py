# critic_search/search_adapter/bing_client.py
import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_random,
)

from .base_search_client import BaseSearchClient
from .exceptions import InvalidAPIKeyError, RatelimitException
from .models import SearchResponse, SearchResult


class BingClient(BaseSearchClient):
    """
    Bing Search API client.
    """

    def __init__(self, api_key: str):
        self.base_url = "https://api.bing.microsoft.com/v7.0/search"
        self._api_key = api_key

        self._client_name = "BingClient"

    @retry(
        stop=stop_after_attempt(5),  # 重试最多5次
        wait=wait_exponential(multiplier=1, min=4, max=30)
        + wait_random(min=1, max=5),  # 指数退避 + 随机抖动
        retry=retry_if_exception_type(RatelimitException),
    )
    async def search(
        self,
        query: str,
    ) -> SearchResponse:
        headers = {"Ocp-Apim-Subscription-Key": self._api_key}

        params = {
            "q": query,  # 用户的搜索查询词。不能为空。
            # 查询词可以包含 Bing 高级操作符，例如使用 site: 操作符限定结果来源于特定域名。
            # 示例：q="fishing+site:fishing.contoso.com"。
            # 注意：即使使用了 site: 操作符，结果可能仍会包含其他站点的内容，具体取决于相关结果的数量。
            "count": 2,  # 返回的搜索结果数量。默认值为 10，最大值为 50。
            # 可以与 offset 参数结合使用来分页结果。
            # 示例：如果每页显示 10 个搜索结果，第一页设置 count=10 和 offset=0，
            # 第二页设置 offset=10，以此类推。分页时可能存在部分结果重叠。
            "safeSearch": "strict",  # 过滤成人内容的设置。
            # 可选值：
            # - "Off": 返回包含成人文本和图片但不包括成人视频的内容。
            # - "Moderate": 返回包含成人文本但不包括成人图片或视频的内容。
            # - "Strict": 不返回任何成人文本、图片或视频内容。
            "responseFilter": "Webpages",  # 用逗号分隔的答案类型，指定要在响应中包含的内容。
            # 如果未指定此参数，则响应包含所有相关的数据类型。
            # 可选值包括：
            # - Computation, Entities, Images, News, Places, RelatedSearches,
            #   SpellSuggestions, TimeZone, Translations, Videos, Webpages。
            # 示例：使用 &responseFilter=-images 排除图片结果。
            # 注意：若想获得单一答案类型，应优先使用特定的 API 端点。
        }

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(self.base_url, headers=headers, params=params)

        if response.status_code == 200:
            json_response = response.json()

            # 解析 Bing 的响应
            web_pages = json_response.get("webPages", {})
            items = web_pages.get("value", [])

            results = []
            for item in items:
                results.append(
                    SearchResult(
                        title=item.get("name", ""),
                        url=item.get("url", ""),
                        content=item.get("snippet", ""),
                    )
                )

            return SearchResponse(query=query, results=results)
        # 处理 HTTP 状态码
        if response.status_code == 429:
            raise RatelimitException()
        elif response.status_code == 401:
            raise InvalidAPIKeyError()
        else:
            return SearchResponse(
                query=query,
                error_message=f"Unexpected status code: {response.status_code}. Response: {response.text}",
            )
