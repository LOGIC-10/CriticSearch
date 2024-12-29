import asyncio
import re
from typing import List, Optional

import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, model_serializer

from critic_search.log import logger


class ScrapedData(BaseModel):
    url: str
    title: Optional[str] = None
    content: List[str] = Field(default_factory=list)
    metadata: Optional[dict] = None
    error: Optional[str] = None


class ScrapedDataList(BaseModel):
    data: List[ScrapedData] = Field(default_factory=list)
    max_content_length: int = 50000

    @model_serializer
    def ser_model(self) -> str:
        # 用于存储拼接后的字符串
        result = []

        # 遍历所有 ScrapedData 对象
        for data in self.data:
            # 优先处理错误
            if data.error:
                result.append(f"Error for URL {data.url}: {data.error}\n")
                continue  # 如果有错误，跳过后续处理

            # 处理标题，如果没有标题，用 "Untitled"
            title = data.title if data.title else "Untitled"

            # 处理内容，如果没有内容，用 "No content available"
            content_lines = data.content
            if content_lines is None or len(content_lines) == 0:
                content_lines = ["No content available"]
            elif isinstance(content_lines, str):
                content_lines = [content_lines]

            # 合并内容为一个字符串
            content = "\n".join(content_lines)

            # 截断内容以确保长度不超过 max_content_length
            if len(content) > self.max_content_length:
                content = content[: self.max_content_length] + "[TOO LONG, END]"

            # 拼接 URL、标题和内容
            result.append(f"URL: {data.url}\nTitle: {title}\nContent:\n{content}\n")

        # 将所有拼接的内容合并成一个长字符串
        return "\n---\n".join(result)


class AsyncWebScraper:
    @staticmethod
    async def scrape(urls: List[str]):
        """
        Scrapes content from a list of webpages asynchronously.

        Args:
            urls (List[str]): A list of URLs to scrape.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        async def fetch_url(url: str) -> ScrapedData:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, headers=headers, timeout=10)

                    if response.status_code != 200:
                        return ScrapedData(
                            url=url,
                            error=f"HTTP {response.status_code}: Unable to fetch page.",
                        )

                    html = response.text
                    soup = BeautifulSoup(html, "html.parser")

                    # Remove script and style elements
                    for script in soup(["script", "style", "meta", "noscript"]):
                        script.decompose()

                    # Extract content based on specified elements or automatic content detection
                    main_content = (
                        soup.find("main")
                        or soup.find("article")
                        or soup.find("div", class_=re.compile(r"content|main|article"))
                    )
                    if main_content:
                        content = main_content.get_text(strip=True).splitlines()
                    else:
                        content = [p.get_text(strip=True) for p in soup.find_all("p")]

                    # Clean up the content and return
                    content = [re.sub(r"\s+", " ", c).strip() for c in content]

                    return ScrapedData(
                        url=url,
                        title=soup.title.string if soup.title else None,
                        content=content,
                        metadata={
                            "length": len("".join(content)),
                            "elements_found": len(content),
                        },
                    )
            except Exception as e:
                return ScrapedData(url=url, error=f"Error: {str(e)}")

        scraped_data = await asyncio.gather(*(fetch_url(url) for url in urls))

        # Wrap results in ScrapedDataList
        result = ScrapedDataList(data=scraped_data).model_dump()
        logger.info(f"Scraped data:\n{result}")
        return result
