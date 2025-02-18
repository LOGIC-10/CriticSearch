import asyncio
import re
from typing import List

import httpx
from bs4 import BeautifulSoup

from .models import ScrapedData


class FallbackWebScraper:
    @staticmethod
    async def scrape(urls: List[str]) -> List[ScrapedData]:
        """
        Scrapes content from a list of webpages asynchronously.
        If Tavily API fails, fall back to scraping.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        async def fetch_url(url: str) -> ScrapedData:
            try:
                async with httpx.AsyncClient(
                    http2=True, follow_redirects=True
                ) as client:
                    response = await client.get(url, headers=headers, timeout=10)

                    if response.status_code != 200:
                        return ScrapedData(
                            url=url,
                            error=f"HTTP {response.status_code}: {response.reason_phrase}",
                        )

                    html = response.text
                    soup = BeautifulSoup(html, "html.parser")

                    # Remove unwanted elements
                    for script in soup(["script", "style", "meta", "noscript"]):
                        script.decompose()

                    # Extract content
                    main_content = (
                        soup.find("main")
                        or soup.find("article")
                        or soup.find("div", class_=re.compile(r"content|main|article"))
                    )
                    content = (
                        "No content available"
                        if not main_content
                        else "\n".join(
                            [
                                re.sub(r"\s+", " ", p.get_text(strip=True))
                                for p in main_content.find_all("p")
                            ]
                        )
                    )

                    return ScrapedData(
                        url=url,
                        title=soup.title.string if soup.title else "Untitled",
                        content=content,
                    )
            except Exception as e:
                return ScrapedData(url=url, error=f"Error: {str(e)}")

        return await asyncio.gather(*(fetch_url(url) for url in urls))
