import re
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup


class WebScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def scrape(self, url: str, elements: Optional[List[str]] = None) -> Dict:
        """
        Scrape content from a webpage.

        Args:
            url: The URL to scrape
            elements: List of HTML elements to specifically target (e.g., ['p', 'h1', 'h2'])
                     If None, extracts main content automatically

        Returns:
            Dict containing scraped content and metadata
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style", "meta", "noscript"]):
                script.decompose()

            # Extract content based on specified elements or automatic content detection
            if elements:
                content = " ".join(
                    [
                        elem.get_text(strip=True)
                        for tag in elements
                        for elem in soup.find_all(tag)
                    ]
                )
            else:
                # Automatic main content detection
                main_content = (
                    soup.find("main")
                    or soup.find("article")
                    or soup.find("div", class_=re.compile(r"content|main|article"))
                )
                if main_content:
                    content = main_content.get_text(strip=True)
                else:
                    # Fallback to extracting paragraphs
                    content = " ".join(
                        [p.get_text(strip=True) for p in soup.find_all("p")]
                    )

            # Clean up the content
            content = re.sub(r"\s+", " ", content).strip()

            return {
                "url": url,
                "title": soup.title.string if soup.title else None,
                "content": content[:5000],  # Limit content length
                "metadata": {
                    "length": len(content),
                    "elements_found": len(content.split()),
                },
            }

        except Exception as e:
            return {"error": str(e)}
