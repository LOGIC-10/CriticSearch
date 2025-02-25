## ClassDef TavilyClient
**TavilyClient**: The function of TavilyClient is to serve as an API client for interacting with the Tavily search service.

**attributes**: The attributes of this Class.
· base_url: str - This attribute stores the base URL for the Tavily API.
· _api_key: str - This attribute holds the API key required for authenticating requests to the Tavily API.
· headers: dict - This attribute contains the headers that will be sent with each API request, specifically setting the content type to JSON.

**Code Description**: The TavilyClient class inherits from the BaseSearchClient class, establishing itself as a specific implementation for interacting with the Tavily API. Upon initialization, it sets the base URL for the Tavily API and stores the provided API key for use in subsequent requests. The class is designed to facilitate asynchronous search operations through the `search` method, which allows users to query the Tavily API with various parameters.

The `search` method is decorated with a retry mechanism, which attempts to resend the request up to five times in case of a rate limit exception (RatelimitException). This method accepts several parameters: `query`, `search_depth`, `topic`, `days`, and `max_results`, allowing for flexible search configurations. The method constructs a JSON payload containing these parameters along with the API key and sends an asynchronous POST request to the Tavily API's search endpoint.

Upon receiving a response, the method checks the status code to determine the outcome of the request. A successful response (HTTP status code 200) results in the parsing of the JSON response into a SearchResponse object. If the response indicates a rate limit has been exceeded (HTTP status code 429), it raises a UsageLimitExceededError or RatelimitException based on the details provided in the response. An unauthorized access attempt (HTTP status code 401) raises an InvalidAPIKeyError. For any other unexpected status codes, the method returns a SearchResponse object containing an error message.

The TavilyClient is utilized within the SearchAggregator class, where it is instantiated if a valid Tavily API key is available. This integration allows the SearchAggregator to manage multiple search clients, including TavilyClient and BingClient, enabling it to perform searches across different services seamlessly.

**Note**: It is essential to ensure that the API key provided to the TavilyClient is valid and that the application handles exceptions appropriately, particularly those related to rate limits and unauthorized access. Proper error handling will enhance the robustness of the application when interacting with the Tavily API.

A possible appearance of the code's return value from the `search` method could be:
```json
{
    "query": "example search",
    "results": [
        {
            "title": "Example Result 1",
            "link": "https://example.com/result1",
            "snippet": "This is a snippet of the first result."
        },
        {
            "title": "Example Result 2",
            "link": "https://example.com/result2",
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
## Function: `search`

### Overview
The `search` function is an asynchronous method designed to perform a search query using the Tavily engine. It allows users to specify search parameters, such as the query string, search depth, topic, date range, and maximum number of results. The function interacts with an API endpoint and returns a structured response encapsulated in the `SearchResponse` class. In case of errors such as rate limiting or invalid API keys, appropriate exceptions are raised.

### Parameters
- **query** (`str`): The search query string to be used in the search request. This parameter is required.
- **search_depth** (`Literal["basic", "advanced"]`): The depth of the search. The default value is `"basic"`, and the available options are:
  - `"basic"`: A standard search depth.
  - `"advanced"`: A more detailed search.
  
- **topic** (`Literal["general", "news"]`): The topic of the search query. The default value is `"general"`, and the options available are:
  - `"general"`: General search results.
  - `"news"`: Results specifically related to news topics.
  
- **days** (`int`): The time frame in days for filtering results. The default value is `7`, meaning results from the past 7 days will be included.
  
- **max_results** (`int`): The maximum number of search results to return. The default value is `10`, and it can be adjusted as needed.

### Returns
- **SearchResponse**: The function returns an instance of the `SearchResponse` class, which contains the results of the search query. The `SearchResponse` includes the query string, a list of search results, and any error messages encountered during the process.

### Exceptions
The function raises the following exceptions in case of errors:
- **UsageLimitExceededError**: Raised when the API usage limit is exceeded. This is specifically handled when a `429` status code is returned.
- **RatelimitException**: Raised when a rate-limiting issue occurs, typically in the event of frequent API requests or when an exception other than `UsageLimitExceededError` is encountered due to rate-limiting issues.
- **InvalidAPIKeyError**: Raised when the provided API key is invalid, typically corresponding to a `401` status code.

### Behavior
1. The function sends an asynchronous POST request to the Tavily search API with the specified parameters.
2. If the request is successful (status code `200`), the function returns a `SearchResponse` object containing the search results.
3. If the API response returns a `429` status code (rate limiting), the function checks if the response contains a usage limit error. If found, it raises a `UsageLimitExceededError`. If any other error occurs while handling the response, a `RatelimitException` is raised.
4. If the API response returns a `401` status code (authentication error), the function raises an `InvalidAPIKeyError`.
5. If the status code is not `200`, `429`, or `401`, the function returns a `SearchResponse` with an error message indicating an unexpected status code.

### Usage Example
```python
tavily_client = TavilyClient(api_key="your_api_key")
response = await tavily_client.search(query="Python programming", search_depth="advanced", topic="general", days=7, max_results=5)
print(response.ser_model())
```

### Notes
- The `SearchResponse` class is used to structure the response from the search API, which includes the query, results, and any error messages.
- The `UsageLimitExceededError` is raised when the search client has exceeded the API usage limits.
***
