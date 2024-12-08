import asyncio
import re
from typing import List, Optional

import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel


class ScrapedData(BaseModel):
    url: str
    title: Optional[str] = None
    content: Optional[List[str]] = None
    metadata: Optional[dict] = None
    error: Optional[str] = None


class AsyncWebScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    async def scrape(
        self, urls: List[str], elements: Optional[List[str]] = None
    ) -> List[ScrapedData]:
        """
        Scrapes content from a list of webpages asynchronously.

        Args:
            urls (List[str]): A list of URLs to scrape.
            elements (Optional[List[str]]): A list of HTML elements to target (e.g., ['p', 'h1', 'h2']).
                If None, the main content is extracted automatically.
        """

        async def fetch_url(url: str) -> ScrapedData:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, headers=self.headers, timeout=10)

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
                    if elements:
                        content = [
                            elem.get_text(strip=True)
                            for tag in elements
                            for elem in soup.find_all(tag)
                        ]
                    else:
                        # Automatic main content detection
                        main_content = (
                            soup.find("main")
                            or soup.find("article")
                            or soup.find(
                                "div", class_=re.compile(r"content|main|article")
                            )
                        )
                        if main_content:
                            content = main_content.get_text(strip=True).splitlines()
                        else:
                            content = [
                                p.get_text(strip=True) for p in soup.find_all("p")
                            ]

                    # Clean up the content and return
                    content = [re.sub(r"\s+", " ", c).strip() for c in content]

                    return ScrapedData(
                        url=url,
                        title=soup.title.string if soup.title else None,
                        content=content[:5000],  # Limit content length
                        metadata={
                            "length": sum(len(c.split()) for c in content),
                            "elements_found": len(content),
                        },
                    )
            except Exception as e:
                return ScrapedData(url=url, error=f"Error: {str(e)}")

        # Asynchronously scrape all URLs
        return await asyncio.gather(*(fetch_url(url) for url in urls))
