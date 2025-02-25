## ClassDef ContentScraper
**ContentScraper**: The function of ContentScraper is to scrape content from the provided URLs by using an external API (Tavily) with a fallback mechanism for custom scraping.

**attributes**: 
- urls: List[str] - A list of URLs from which content is to be scraped.

**Code Description**: 
The `ContentScraper` class provides a static method, `scrape`, that is used to extract content from a list of URLs. The method follows these main steps:

1. **API Key and Initialization**: The method starts by retrieving an API key from the project settings (`settings.tavily.api_key`) and initializes an instance of `TavilyExtract` with the API key.
   
2. **Tavily Extraction**: The method attempts to scrape content from the provided URLs using the `TavilyExtract` instance by calling `extract_content` on the `tavily` object. This method returns results that are either successful or failed.

3. **Error Handling**: If the Tavily extraction results contain an error (indicated by the presence of the "error" key), the method logs the error and proceeds to fall back to a custom web scraping solution by invoking `FallbackWebScraper.scrape`. This is done to ensure that content scraping continues even if the Tavily service fails.

4. **Processing Successful Results**: If the Tavily extraction is successful, the results (contained in the `results` key) are iterated through. For each result, the URL and raw content are extracted and stored as `ScrapedData` objects, which are then added to a list of successful results.

5. **Handling Failed Results**: If any URLs are marked as failed in the Tavily results (`failed_results`), the method logs a warning and retries scraping those URLs using the custom fallback scraper.

6. **Final Results**: After processing both successful and failed results, the method merges these into a final list and returns them encapsulated within a `ScrapedDataList` object, which is serialized using the `model_dump` method before being returned.

This approach ensures a robust content scraping process with error handling and fallback mechanisms for cases when the primary extraction method (Tavily) fails.

The `scrape` method is used within the `BaseAgent` class (located in `src/criticsearch/base_agent.py`), which initializes an instance of `ContentScraper` and adds it to the list of available tools for the conversation manager. This allows the agent to call the `scrape` method when it requires content extraction from a set of URLs.

**Note**: 
- The `scrape` method is asynchronous, meaning it must be awaited when called.
- The method handles both successful and failed scraping attempts by using a combination of the Tavily API and a custom fallback scraper.
- Ensure the API key for Tavily is correctly set in the project settings for successful integration.

**Output Example**: 
The `scrape` method will return a serialized `ScrapedDataList` object that contains a list of `ScrapedData` objects. Each `ScrapedData` object includes the URL and the raw content extracted from the source. Here's a mock example:

```json
{
  "data": [
    {
      "url": "https://example.com/page1",
      "content": "This is the raw content from page 1."
    },
    {
      "url": "https://example.com/page2",
      "content": "This is the raw content from page 2."
    }
  ]
}
```
### FunctionDef scrape(urls)
**scrape**: The function of scrape is to asynchronously scrape content from a list of provided URLs, utilizing the Tavily API for extraction and falling back to a custom web scraping method if necessary.

**parameters**: The parameters of this Function.
· urls: List[str] - A list of URLs to scrape content from.

**Code Description**: The `scrape` function is an asynchronous method designed to extract content from a list of URLs. It first initializes an instance of the `TavilyExtract` class using an API key retrieved from the settings. This instance is responsible for interacting with the Tavily API to perform the content extraction.

The function begins by calling the `extract_content` method of the `TavilyExtract` instance, passing the list of URLs. This method sends an asynchronous POST request to the Tavily API, which returns a JSON response containing the results of the extraction. If the response includes an error, the function logs the error message and proceeds to invoke the `FallbackWebScraper.scrape` method, which serves as a backup scraping mechanism.

In the case of successful extraction, the function processes the results returned by the Tavily API. It iterates through the successful results, extracting the URL and raw content from each result. For each successful extraction, it creates a `ScrapedData` object, which encapsulates the URL and the corresponding content.

Additionally, if there are any failed results in the Tavily API response, the function logs a warning and attempts to scrape the failed URLs using the `FallbackWebScraper.scrape` method. The results from both successful and fallback scraping are merged into a final list of `ScrapedData` objects.

Finally, the function returns a `ScrapedDataList` object, which contains all the scraped data, including both successful and failed attempts. This object is serialized using the `model_dump` method, providing a structured output of the scraping results.

The `scrape` function is called within the `BaseAgent` class, specifically in the `search_and_browse` method. This method orchestrates the overall search and scraping process, first performing a search using the `SearchAggregator` and then invoking the `scrape` function to gather additional content from the URLs identified during the search. This integration ensures that the scraping functionality is seamlessly incorporated into the broader search and retrieval workflow of the application.

**Note**: When using this function, ensure that the URLs provided are valid and accessible. Additionally, be aware of the legal and ethical considerations surrounding web scraping, including compliance with the target website's terms of service.

**Output Example**: A possible appearance of the code's return value could be:
```
[
    ScrapedData(url="http://example.com", title="Example Title", content="This is the main content of the page."),
    ScrapedData(url="http://anotherexample.com", title="Another Example", content="No content available")
]
```
***
