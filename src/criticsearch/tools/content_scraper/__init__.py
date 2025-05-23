from typing import List

from ...config import settings
from ...rich_output import printer
from .fallback_web_scraper import FallbackWebScraper
from .models import ScrapedData, ScrapedDataList
from .tavily_extract import TavilyExtract


class ContentScraper:
    @staticmethod
    async def scrape(urls: List[str]) -> ScrapedDataList:
        """
        Scrapes content using the provided URLs.

        Args:
            urls (List[str]): A list of URLs to scrape content from.
        """
        api_key = settings.tavily.api_key
        tavily = TavilyExtract(api_key)

        # Try to extract using Tavily
        tavily_results = await tavily.extract_content(urls)
        final_results = []

        # Check for errors or failed results in the Tavily response
        if "detail" in tavily_results:
            error_message = tavily_results["detail"].get("error", "Unknown error")

            printer.log(
                f"Tavily API extraction failed: {error_message}, falling back to web scraping.",
                style="bold red",
            )

            final_results = await FallbackWebScraper.scrape(urls)
        else:
            # Process successful results from Tavily
            successful_results = []

            results = tavily_results.get("results", [])
            for result in results:
                # Extract the necessary data from the Tavily API response
                url = result.get("url")
                raw_content = result.get("raw_content")

                successful_results.append(
                    ScrapedData(
                        url=url,
                        content=raw_content,
                    )
                )

            failed_results = tavily_results.get("failed_results", [])

            # If Tavily has failed results, log them and proceed with fallback
            if failed_results:
                printer.log(
                    f"Some URLs failed in Tavily extraction. Using fallback web scraping for these URLs.",
                    style="bold yellow",
                )
                failed_urls = [result.get("url") for result in failed_results]
                failed_results = await FallbackWebScraper.scrape(failed_urls)

            # Merge both successful and failed results into ScrapedDataList
            final_results = successful_results + failed_results

        return ScrapedDataList(data=final_results).model_dump()
