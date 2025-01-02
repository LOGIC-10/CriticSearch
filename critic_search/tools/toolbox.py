import asyncio
from typing import List

from .search_adapter import SearchAggregator
from .tool_registry import ToolRegistry, register_tool_function
from .web_scraper import WebScraper


class Toolbox(ToolRegistry):
    """
    A collection of tools for searching and scraping data.
    Contains functions for querying search engines and scraping web pages.
    """

    @staticmethod
    @register_tool_function
    def perform_search(queries: List[str]):
        """
        Performs a search using the provided queries.

        Supports various search techniques using special syntax.

        Args:
            queries (List[str]): A list of search queries to execute.
        """
        search_results = SearchAggregator().search(queries=queries)
        return search_results

    @staticmethod
    @register_tool_function
    def scrape_webpages(urls: List[str]):
        """
        Scrapes content using the provided URLs.

        Args:
            urls (List[str]): A list of URLs to scrape content from.
        """
        with asyncio.Runner() as runner:
            scraped_data = runner.run(
                WebScraper().scrape(urls)
            )  # 自动管理事件循环，无需 nest_asyncio.apply()
        return scraped_data
