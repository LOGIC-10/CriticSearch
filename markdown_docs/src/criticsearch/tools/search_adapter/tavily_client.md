## ClassDef TavilyClient
**TavilyClient**: The function of TavilyClient is to serve as an API client for interacting with the Tavily search service.

**attributes**: The attributes of this Class.
· base_url: str - This attribute stores the base URL for the Tavily API, which is "https://api.tavily.com".
· _api_key: str - This attribute holds the API key required for authenticating requests to the Tavily API.
· headers: dict - This attribute contains the HTTP headers to be sent with API requests, specifically setting the "Content-Type" to "application/json".

**Code Description**: The TavilyClient class inherits from BaseSearchClient and is designed to facilitate asynchronous search operations through the Tavily API. Upon initialization, the class requires an API key, which is stored in the _api_key attribute. The base URL for the API is predefined, and the headers for the requests are set to indicate that the content type is JSON.

The primary functionality of the TavilyClient is encapsulated in the asynchronous search method. This method accepts several parameters: a query string, search depth, topic, the number of days to look back, and the maximum number of results to return. The method constructs a JSON payload with these parameters, including the API key, and sends an asynchronous POST request to the Tavily API's search endpoint.

The search method is equipped with retry logic, allowing it to attempt the request up to five times in the event of a rate limit exception (indicated by a 429 status code). It employs an exponential backoff strategy combined with random jitter to manage retries effectively. If the API responds with a 200 status code, the method processes the response and returns a validated SearchResponse object. If a 429 status code is encountered, it checks for specific error details and raises a UsageLimitExceededError if applicable. For a 401 status code, it raises an InvalidAPIKeyError, indicating that the provided API key is invalid. Any other unexpected status codes result in the method returning a SearchResponse object that includes an error message detailing the issue.

The TavilyClient is utilized within the SearchAggregator class, which initializes instances of various search clients based on available API keys. If a valid Tavily API key is found in the settings, an instance of TavilyClient is created and added to the clients dictionary. This design allows the SearchAggregator to manage multiple search clients, including TavilyClient, enabling it to perform searches across different services seamlessly.

**Note**: It is essential to ensure that the API key for Tavily is correctly configured in the settings. If the key is missing or invalid, the TavilyClient will not be instantiated, which may limit the functionality of the SearchAggregator. Proper error handling should be implemented when using the TavilyClient to manage search requests effectively.

A possible appearance of the code's return value from the search method could be:
```json
{
    "query": "example search",
    "results": [
        {
            "title": "Example Result 1",
            "url": "https://example.com/result1",
            "snippet": "This is a snippet of the first result."
        },
        {
            "title": "Example Result 2",
            "url": "https://example.com/result2",
            "snippet": "This is a snippet of the second result."
        }
    ],
    "error_message": null
}
```
### FunctionDef __init__(self, api_key)
**__init__**: The function of __init__ is to initialize the TavilyClient object with the required API key and configure default settings for the instance.

**parameters**: The parameters of this Function.
- api_key: A string representing the API key used for authentication with the Tavily API.

**Code Description**: The `__init__` method is the constructor of the `TavilyClient` class. It initializes an instance of the class by setting up default values and configurations necessary for interacting with the Tavily API.
  
1. **self.base_url**: This attribute is set to the string "https://api.tavily.com", which represents the base URL of the Tavily API. It is used as the root URL for all API requests made by this client.
  
2. **self._api_key**: This attribute is initialized with the value of the `api_key` parameter. It stores the API key provided when the instance of the client is created. This key will likely be used in API requests for authentication purposes.

3. **self.headers**: A dictionary is created with the key `"Content-Type"` set to `"application/json"`. This header is typically included in HTTP requests to specify that the body of the request is in JSON format. It ensures that the client interacts with the API in a manner that is compatible with its expected input format.

The method does not return any value. It simply prepares the object with the necessary attributes to interact with the Tavily API.

**Note**: 
- The `api_key` is essential for authentication with the Tavily API and must be provided when creating an instance of the `TavilyClient`.
- The `base_url` and headers are set to default values, which can be further customized or extended by other methods in the `TavilyClient` class for specific API requests.
***
### FunctionDef search(self, query, search_depth, topic, days, max_results)
**search**: The function of search is to perform an asynchronous search query based on user-defined parameters and return the results encapsulated in a SearchResponse object.

**parameters**: The parameters of this Function.
· query: str - A string representing the user's search query. This parameter cannot be empty and is essential for executing the search.  
· search_depth: Literal["basic", "advanced"] - This optional parameter specifies the depth of the search, with a default value of "basic".  
· topic: Literal["general", "news"] - This optional parameter defines the topic of the search, defaulting to "general".  
· days: int - This optional parameter indicates the number of days to look back for results, defaulting to 7 days.  
· max_results: int - This optional parameter sets the maximum number of results to return, defaulting to the value specified in the settings or 10 if not defined.

**Code Description**: The search function is an asynchronous method designed to facilitate search queries against a specified API. It constructs a data payload containing the search parameters, including the query string, search depth, topic, days, maximum results, and the API key. Using the httpx library, it initiates an asynchronous POST request to the search endpoint of the API.

Upon receiving a response, the function checks the status code:
- If the status code is 200, it validates and returns the response data as a SearchResponse object.
- If the status code is 429, indicating that the usage limit has been exceeded, it attempts to extract the error detail from the response. If a specific error message is present, it raises a UsageLimitExceededError. If no detail is found, it logs the exception and raises a RatelimitException.
- If the status code is 401, it raises an InvalidAPIKeyError, indicating that the provided API key is invalid.
- For any other status codes, it constructs a SearchResponse object containing the original query and an error message indicating the unexpected status code.

The search function is called by the _search_single_query method within the SearchAggregator class. This method manages the execution of search queries across multiple search engines. It iterates through a list of available engines, invoking the search method for each engine that is operational. The results from these searches are collected and returned as a structured response. The search function is integral to the overall search functionality, providing a consistent interface for querying search engines and handling various error conditions.

**Note**: It is crucial to ensure that the query parameter is a valid and non-empty string. The optional parameters should be set according to the desired search behavior. Proper error handling is implemented for various HTTP status codes, and developers should be aware of the implications of exceeding usage limits or providing invalid API keys.

**Output Example**: A possible return value of the search function could be structured as follows:
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
