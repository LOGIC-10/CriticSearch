## ClassDef SearchAggregator
**SearchAggregator**: The function of SearchAggregator is to manage and execute search queries across multiple search engines.

**attributes**: The attributes of this Class.
· clients: A dictionary that holds instances of search engine clients, specifically TavilyClient and BingClient, keyed by their respective engine names.  
· available_clients: A set that contains the names of currently available search engines that can be used for querying.

**Code Description**: The SearchAggregator class is designed to facilitate searching through multiple search engines by managing their respective clients. Upon initialization, the class checks for the presence of API keys for Tavily and Bing. If the keys are available, it creates instances of TavilyClient and BingClient and stores them in the clients dictionary. The available_clients set is initialized to keep track of which search engines are currently available for use.

The class provides two main functionalities: marking a search engine as unavailable and performing searches. The `mark_engine_unavailable` method allows the user to remove a search engine from the available_clients set if it encounters issues during a search operation. This is particularly useful for handling errors such as invalid API keys or usage limits being exceeded.

The `_search_single_query` method is an asynchronous function that attempts to execute a search query against the specified engines. It iterates through the provided list of engines, checking if they are available. If an engine is available, it calls its search method and logs the result. If an error occurs, it logs the error and marks the engine as unavailable. If all specified engines fail, it returns a SearchResponse indicating that no available search engines could handle the query.

The `search` method allows users to perform searches using a list of queries. It gathers the available engines and creates tasks for concurrent execution of searches for each query. The results are awaited and returned as a SearchResponseList, which encapsulates the responses from the search engines.

The SearchAggregator class is utilized in the BaseAgent class, where an instance of SearchAggregator is created to manage search queries. This integration allows the BaseAgent to leverage the capabilities of multiple search engines, enhancing its ability to gather information. Additionally, the SearchAggregator is instantiated in the process_single_task function, where it is used to execute search queries based on user tasks.

**Note**: When using the SearchAggregator, ensure that the necessary API keys for the search engines are configured correctly in the settings. Additionally, be aware that if all search engines become unavailable, the search operation will fail, and an appropriate error message will be returned.

**Output Example**: A possible appearance of the code's return value after executing a search query could look like this:
```json
{
  "responses": [
    {
      "query": "Who is Leo Messi?",
      "error_message": "Search failed: No available search engines for this query."
    }
  ]
}
```
### FunctionDef __init__(self)
**__init__**: The function of __init__ is to initialize the SearchAggregator class, setting up the necessary search clients based on available API keys.

**parameters**: The parameters of this Function.
· None

**Code Description**: The __init__ method is the constructor for the SearchAggregator class. It initializes an empty dictionary named `clients`, which is intended to hold instances of search clients that can be used for executing search queries. The method first checks for the presence of an API key for the Tavily search service by accessing `settings.tavily.api_key`. If a valid API key is found, an instance of the TavilyClient is created and added to the `clients` dictionary with the key "tavily". 

Similarly, the method checks for the Bing search service API key using `settings.search_engine.bing.api_key`. If this API key is available, an instance of the BingClient is created and added to the `clients` dictionary with the key "bing". 

After initializing the clients, the method creates a set called `available_clients`, which contains the keys of the clients that have been successfully instantiated. This allows the SearchAggregator to keep track of which search clients are available for use.

The SearchAggregator class is designed to manage multiple search clients, enabling it to perform searches across different services. By initializing the clients in the constructor, the class ensures that it can leverage the functionalities of both TavilyClient and BingClient, provided that the necessary API keys are available. This design promotes flexibility and extensibility, allowing for easy integration of additional search clients in the future.

**Note**: It is important to ensure that the API keys for both Tavily and Bing are correctly configured in the settings. If the keys are missing or invalid, the corresponding clients will not be initialized, which may affect the functionality of the SearchAggregator. Proper error handling should be implemented when using the SearchAggregator to manage search requests.
***
### FunctionDef mark_engine_unavailable(self, engine)
**mark_engine_unavailable**: The function of mark_engine_unavailable is to mark a specific search engine as unavailable.

**parameters**:
· engine: str - The name of the engine to mark as unavailable.

**Code Description**:  
The `mark_engine_unavailable` method is part of a class and is responsible for updating the status of a specified search engine by marking it as unavailable. This is achieved by removing the engine's name from the `available_clients` collection. The parameter `engine` is expected to be a string, which represents the name of the search engine that needs to be marked as unavailable.

In terms of its usage, this function is typically called within error-handling blocks. Specifically, it is invoked whenever an exception is raised during a search operation, indicating that a particular engine is no longer functional for the query being processed. The method ensures that once an engine fails due to errors like retries, invalid API keys, or usage limits, it is effectively removed from the list of available search engines, preventing any further attempts to use that engine in future queries.

**Note**:  
- The `mark_engine_unavailable` function operates by directly modifying the `available_clients` list. Therefore, it is essential that `available_clients` is a mutable collection that supports the `remove` operation, like a list or set.
- The engine's unavailability is handled automatically through exception handling in related functions (like `_search_single_query`), ensuring that engines that fail during the search process are excluded from subsequent attempts. 
- It is important to note that this function does not handle the re-inclusion of the engine once it has been marked as unavailable; this would need to be managed separately if required.
***
### FunctionDef _search_single_query(self, query, engines)
**_search_single_query**: The function of _search_single_query is to execute a search query against multiple search engines and return the results encapsulated in a SearchResponse object.

**parameters**: The parameters of this Function.
· query: str - A string representing the search query to be executed.  
· engines: List[str] - A list of search engine names that are available for executing the query.

**Code Description**: The _search_single_query function is an asynchronous method designed to perform a search operation using a specified query across multiple search engines. It iterates through the provided list of engines, checking if each engine is available for use. If an engine is found to be available, the function attempts to execute the search by calling the search method of the corresponding client for that engine.

Upon calling the search method, the function awaits the result. If the search is successful, it logs the result using the printer.log method and returns the result encapsulated in a SearchResponse object. The logging provides visibility into the search results, which can be useful for debugging and monitoring purposes.

In the event of an error during the search operation, the function handles several specific exceptions:
- RetryError: Indicates that the search engine failed after multiple retry attempts. The engine is marked as unavailable using the mark_engine_unavailable method.
- InvalidAPIKeyError: Raised when the API key used for the search is invalid. The engine is also marked as unavailable in this case.
- UsageLimitExceededError: This exception is raised when the search engine has exceeded its usage limits. The engine is marked as unavailable as well.
- General Exception: Any other unexpected errors are caught, and the function logs the exception details using the printer.print_exception method, marking the engine as unavailable.

If all specified search engines are found to be unavailable after iterating through the list, the function logs a message indicating that no available search engines could be used for the query. It then returns a SearchResponse object containing the original query and an error message stating that the search failed due to the unavailability of search engines.

The _search_single_query function is called by the search method within the SearchAggregator class. The search method is responsible for executing multiple search queries concurrently by creating tasks for each query and utilizing the asyncio.gather function to run them. This design allows for efficient handling of multiple queries, leveraging the asynchronous capabilities of the underlying framework.

**Note**: It is important to ensure that the engines parameter contains valid search engine names that are currently available. The function relies on proper exception handling to manage errors effectively, ensuring that any issues encountered during the search process are logged and handled gracefully.

**Output Example**: A possible return value of the _search_single_query function could be structured as follows:
```python
SearchResponse(
    query="latest technology news",
    results=[
        SearchResult(title="Tech Innovations", url="https://example.com/tech-innovations", content="Explore the latest in technology."),
        SearchResult(title="Gadget Reviews", url="https://example.com/gadget-reviews", content="Read reviews on the newest gadgets.")
    ],
    error_message=None
)
``` 
This output illustrates a successful search response containing the original query, a list of search results, and no error messages.
***
### FunctionDef search(self, query)
**search**: The function of search is to perform a search using the provided query, supporting various search techniques through special syntax.

**parameters**: The parameters of this Function.
· query: List[str] - A list of search queries to be executed.

**Code Description**: The search function is an asynchronous method within the SearchAggregator class that facilitates searching across multiple search engines based on the provided list of queries. The function begins by retrieving the currently available search engines from the instance's available_clients attribute. If no engines are available, it raises a ValueError, indicating that the search cannot proceed.

To execute the search, the function creates a list of tasks, where each task corresponds to a single search query. These tasks are generated by calling the _search_single_query method, which is responsible for executing a search against the available engines. The search_single_query method is called for each query in the provided list, allowing for concurrent execution of searches.

Once the tasks are created, the function uses the asyncio.gather method to run all tasks concurrently and await their results. This approach enhances efficiency by allowing multiple searches to be processed simultaneously rather than sequentially.

After gathering the responses from all search tasks, the function constructs a SearchResponseList object, which encapsulates the results of the searches. This object is then serialized and returned as a string representation, providing a structured output of the search results.

The search method is called by various components within the project, including the search_and_browse method in the BaseAgent class. This method utilizes the search function to perform searches based on user prompts and integrates the results into a broader workflow that may involve web scraping and content generation.

**Note**: It is essential to ensure that the query parameter contains valid search terms and that the available_clients attribute is populated with active search engines. Proper error handling is implemented to manage cases where no engines are available, ensuring that the function fails gracefully.

**Output Example**: A possible return value of the search function could be structured as follows:
```json
{
  "responses": [
    {
      "query": "latest technology news",
      "results": [
        {
          "title": "Tech Innovations",
          "url": "https://example.com/tech-innovations",
          "content": "Explore the latest in technology."
        },
        {
          "title": "Gadget Reviews",
          "url": "https://example.com/gadget-reviews",
          "content": "Read reviews on the newest gadgets."
        }
      ],
      "error_message": null
    }
  ]
}
``` 
This output illustrates a successful search response containing the original query, a list of search results, and no error messages.
***
