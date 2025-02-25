## ClassDef SearchAggregator
**SearchAggregator**: The function of SearchAggregator is to aggregate and execute search queries across multiple search engines while handling various error conditions and API limitations.

**attributes**:
- clients: A dictionary holding instances of different search engine clients, such as TavilyClient and BingClient, which are used to execute search queries.
- available_clients: A set that tracks the search engines that are currently available for use, excluding any that are marked as unavailable due to errors or limitations.

**Code Description**:  
The `SearchAggregator` class is responsible for managing multiple search engines and executing queries across them. Upon initialization, it checks for API keys for both Tavily and Bing search engines from the settings. If valid keys are found, it initializes corresponding clients for these engines and stores them in the `clients` attribute. The `available_clients` set is then populated with the keys (names) of the initialized clients. 

The class includes the following key methods:

- `mark_engine_unavailable(engine: str)`: This method marks a specified search engine as unavailable by removing it from the `available_clients` set. This is used when an error or limitation (such as an invalid API key, retry limit reached, or usage limit exceeded) occurs with a particular search engine.
  
- `_search_single_query(query: str, engines: List[str])`: This asynchronous method attempts to search a given query across the provided list of search engines. For each engine, it checks if the engine is available and then tries to perform the search. If the search is successful, the result is returned. If an exception occurs, the engine is marked as unavailable, and the method moves on to the next engine in the list. Various exceptions are handled, including `RetryError`, `InvalidAPIKeyError`, and `UsageLimitExceededError`.

- `search(query: List[str])`: This is the primary method that allows the user to perform searches using a list of queries. It first checks if there are any available search engines. If none are available, it raises an exception. It then creates asynchronous tasks for each query and executes them concurrently. The method returns the aggregated search results as a list of responses.

The `SearchAggregator` class is used in other components of the project to facilitate search functionality. For instance, in `BaseAgent`, it is instantiated and its search method is called to perform searches with specific queries. This enables the broader application to conduct searches in a robust and fault-tolerant manner by leveraging multiple search engines. Additionally, in the main entry point (`src/criticsearch/tools/search_adapter/__main__.py/main`), an asynchronous search is triggered, and the results are printed.

**Note**:  
- Ensure that valid API keys for the search engines (Tavily and Bing) are provided in the settings, as the functionality depends on these keys to initialize the respective clients.
- The `search` method handles multiple queries simultaneously, making it efficient in handling concurrent searches.
- If all search engines are marked unavailable, the method returns a `SearchResponse` indicating the failure to execute the search, along with an appropriate error message.
  
**Output Example**:
A possible return value of the `search` method might look like this:

```json
{
  "responses": [
    {
      "query": "Who is Leo Messi?",
      "results": [
        {
          "title": "Lionel Messi - Wikipedia",
          "url": "https://en.wikipedia.org/wiki/Lionel_Messi",
          "snippet": "Lionel Andrés Messi is an Argentine professional footballer widely regarded as one of the greatest players of all time."
        }
      ]
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
**_search_single_query**: The function of _search_single_query is to perform an asynchronous search query using specified search engines and return the results encapsulated in a SearchResponse object.

**parameters**: The parameters of this Function.
· query: str - A string representing the user's search query. This parameter cannot be empty.
· engines: List[str] - A list of search engine names that are available for performing the search.

**Code Description**: The `_search_single_query` function is an asynchronous method designed to execute a search query against a list of specified search engines. It iterates through each engine in the provided `engines` list and checks if the engine is available in the `available_clients` collection. If the engine is available, it attempts to call the asynchronous `search` method of the corresponding client.

The function handles various exceptions that may arise during the search process:
- If a `RetryError` occurs, it logs a warning indicating that the engine has failed after multiple retries and marks the engine as unavailable using the `mark_engine_unavailable` method.
- If an `InvalidAPIKeyError` is raised, it logs an error message indicating that the search engine's API key is invalid and marks the engine as unavailable.
- If a `UsageLimitExceededError` is encountered, it logs a warning about the usage limit being exceeded and marks the engine as unavailable.
- For any other exceptions, it logs the exception details and marks the engine as unavailable.

If all specified search engines are unavailable, the function logs an error message and returns a `SearchResponse` object containing the original query and an error message indicating that no available search engines could fulfill the request.

This function is called by the `search` method of the `SearchAggregator` class. The `search` method gathers a list of currently available search engines and creates tasks for concurrent execution of `_search_single_query` for each query in the provided list. The results from these tasks are then collected and returned as a structured response.

**Note**: It is essential to ensure that the engines passed to this function are valid and that the `available_clients` collection is properly maintained to reflect the current state of search engines. The function does not handle the re-inclusion of engines marked as unavailable; this must be managed separately if required.

**Output Example**: A possible return value of the `_search_single_query` function could be a `SearchResponse` object structured as follows:
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
***
### FunctionDef search(self, query)
**search**: The function of search is to perform a search using the provided query and return the results as a serialized response.

**parameters**: The parameters of this Function.
· query: List[str] - A list of search queries that the user wants to search for.

**Code Description**: The `search` method is an asynchronous function designed to execute multiple search queries concurrently using available search engines. It takes a list of search queries as input and returns a serialized string representation of the search results.

The method begins by retrieving the list of currently available search engines from the `available_clients` attribute. If there are no available engines, it raises a `ValueError`, indicating that the search cannot be performed. This ensures that the function does not attempt to execute a search when there are no resources to handle it.

Next, the method creates a list of tasks, where each task corresponds to a single search query. This is done by calling the `_search_single_query` method for each query in the provided list, passing the list of available engines to it. The `_search_single_query` method is responsible for executing the search against each engine and returning the results encapsulated in a `SearchResponse` object.

Once the tasks are created, the method uses the `gather` function from the `asyncio` library to execute all the search tasks concurrently. This allows for efficient handling of multiple queries, as it does not block the execution while waiting for each individual search to complete.

After all tasks are executed, the method collects the responses and constructs an instance of `SearchResponseList`, which is designed to hold and serialize the search results. The `model_dump()` method of `SearchResponseList` is called to generate a formatted string representation of the results, ensuring that any duplicate content across the responses is removed.

The `search` method is called by various components in the project, including the `search_and_browse` method in the `BaseAgent` class and the `main` function in the `__main__.py` module. In `search_and_browse`, it is invoked to handle user prompts for search queries, while in `main`, it demonstrates a simple use case of performing a search for a specific query.

**Note**: It is important to ensure that the search engines are properly configured and available before calling this method. The method handles the serialization of results, ensuring that duplicates are filtered out, which enhances the relevance of the returned data.

**Output Example**: A possible return value of the `search` function could be a serialized string representing the search results, structured as follows:
```
{
  "results": [
    {
      "title": "Introduction to Python",
      "url": "https://example.com/python",
      "content": "Python is a high-level programming language."
    },
    {
      "title": "Python Tutorials",
      "url": "https://example.com/tutorials",
      "content": "Learn Python programming with these tutorials."
    }
  ],
  "summary": {
    "total_results": 5,
    "unique_results": 3,
    "duplicates_removed": 2
  }
}
``` 
This output illustrates the results of the search queries, including a summary of the total results and the number of unique results returned.
***
