import re
from typing import List, Optional

from bs4 import BeautifulSoup
from niquests import Session
from pydantic import BaseModel, Field, model_serializer

from criticsearch.config import settings


class ScrapedData(BaseModel):
    url: str
    title: Optional[str] = None
    content: Optional[str] = None
    error: Optional[str] = None


class ScrapedDataList(BaseModel):
    data: List[ScrapedData] = Field(default_factory=list)
    max_content_length: int = 50000  # Max length for individual content
    max_output_length: int = 100000  # Max length for the entire serialized result

    @model_serializer
    def ser_model(self) -> str:
        # List to store concatenated strings
        result = []

        for data in self.data[: settings.scrape_max_responses]:
            if data.error:
                result.append(f"Error for URL {data.url}: {data.error}\n")
                continue  # Skip further processing if there's an error

            assert data.content is not None

            # Truncate content to ensure it does not exceed max_content_length
            if len(data.content) > self.max_content_length:
                data.content = (
                    data.content[: self.max_content_length] + "[TOO LONG, END]"
                )

            result.append(
                f"URL: {data.url}\nTitle: {data.title}\nContent:\n{data.content}\n"
            )

        output = "\n---\n".join(result)

        # Apply final length truncation to the overall result
        if len(output) > self.max_output_length:
            output = output[: self.max_output_length] + "\n[OUTPUT TOO LONG, TRUNCATED]"

        return output


class WebScraper:
    @staticmethod
    def scrape(urls: List[str]):
        """
        Scrapes content from a list of webpages asynchronously.

        Args:
            urls (List[str]): A list of URLs to scrape.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        scraped_data = []

        with Session(multiplexed=True) as session:
            responses = [session.get(url, headers=headers) for url in urls]
            session.gather()

        for response in responses:
            try:
                if response.status_code != 200:
                    return ScrapedData(
                        url=response.url,  # type: ignore
                        error=f"HTTP {response.status_code}: {response.reason_phrase}",
                    )

                html = response.text
                soup = BeautifulSoup(html, "html.parser")  # type: ignore

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
                    # Extract main content text and split into lines
                    content_lines = main_content.get_text(strip=True).splitlines()
                else:
                    # Extract text from all <p> elements
                    content_lines = [p.get_text(strip=True) for p in soup.find_all("p")]

                # Clean up the content and HTML escaping
                content_lines = [
                    re.sub(
                        r"<.*?>",
                        lambda m: "\\" + m.group(0),
                        re.sub(r"\s+", " ", c).strip(),
                    )
                    for c in content_lines
                ]

                # If content_lines is empty, provide a default value
                if not content_lines:
                    content = "No content available"
                else:
                    # Combine the list of lines into a single string
                    content = "\n".join(content_lines)

                data = ScrapedData(
                    url=response.url,  # type: ignore
                    title=soup.title.string if soup.title else "Untitled",
                    content=content,
                )
            except Exception as e:
                data = ScrapedData(url=response.url, error=f"Error: {str(e)}")  # type: ignore

            scraped_data.append(data)

        return ScrapedDataList(data=scraped_data).model_dump()


if __name__ == "__main__":
    urls = [
        "https://www.bankinghub.eu/innovation-digital/central-bank-digital-currency",
        "https://niquests.readthedocs.io/en/stable/user/quickstart.html",
        "https://docs.github.com/en/site-policy/github-terms/github-terms-of-service",
    ]

    scraper = WebScraper()
    import time

    start_time = time.perf_counter()
    result = scraper.scrape(urls)
    end_time = time.perf_counter()

    elapsed_time = end_time - start_time
    print(result)
    print(f"Scraping took {elapsed_time:.2f} seconds")
