## ClassDef TavilyExtract
**TavilyExtract**: The function of TavilyExtract is to interact with the Tavily API to extract content from a list of provided URLs.

**attributes**: The attributes of this Class.
· base_url: The base URL for the Tavily API endpoint used for content extraction.
· _api_key: The API key used for authentication with the Tavily API.
· headers: The headers required for making requests to the Tavily API, including content type and authorization.

**Code Description**: The TavilyExtract class is designed to facilitate the extraction of content from specified URLs using the Tavily API. Upon initialization, it requires an API key, which is stored as a private attribute (_api_key). The class constructs the necessary headers for API requests, ensuring that the content type is set to JSON and that the API key is included in the authorization header.

The primary method of the class, `extract_content`, takes a list of URLs as input. It constructs a JSON payload containing these URLs and makes an asynchronous POST request to the Tavily API using the httpx library. The method handles potential HTTP errors by raising exceptions for any 4xx or 5xx responses, and it captures request errors as well. If the request is successful, the method parses the JSON response and returns the data. In case of errors, it returns a dictionary containing the error message.

This class is utilized within the `scrape` function of the ContentScraper module. The `scrape` function first initializes an instance of TavilyExtract with the API key retrieved from the settings. It then calls the `extract_content` method, passing the list of URLs to be scraped. The results from the Tavily API are checked for errors; if any errors are present, the function logs the error and falls back to a custom web scraping method. If the extraction is successful, it processes the results, extracting the necessary data and merging successful and failed results into a final output.

**Note**: Ensure that the API key is valid and has the necessary permissions to access the Tavily API. The URLs provided should be accessible and valid to avoid unnecessary errors during the extraction process.

**Output Example**: A possible appearance of the code's return value could be:
{
  "results": [
    {
      "url": "https://example.com",
      "raw_content": "<html>...</html>"
    }
  ],
  "failed_results": [
    {
      "url": "https://failed-url.com"
    }
  ]
}
### FunctionDef __init__(self, api_key)
**__init__**: The function of __init__ is to initialize the TavilyExtract object by setting up the base URL for API requests and configuring the necessary headers for authentication.

**parameters**: The parameters of this function.
· api_key: str - This is the API key required for authenticating requests to the Tavily API.

**Code Description**: 
The `__init__` function is the constructor method of the `TavilyExtract` class. It is responsible for setting up the essential attributes needed to interact with the Tavily API. Upon initialization:

1. The `base_url` attribute is assigned a fixed value, `"https://api.tavily.com/extract"`. This URL is the endpoint used for making API requests.
  
2. The `_api_key` attribute is initialized with the provided `api_key` parameter, which is a string containing the user's personal API key. This key is used to authenticate requests made to the Tavily API.

3. The `headers` attribute is a dictionary containing two key-value pairs:
   - `"Content-Type": "application/json"`: This specifies that the data being sent in requests will be formatted as JSON.
   - `"Authorization": f"Bearer {self._api_key}"`: This header is used for bearer token authentication, where the API key is included in the Authorization header to verify the identity of the requester.

This constructor ensures that an instance of the `TavilyExtract` class is correctly set up with the necessary API URL and authentication details for subsequent API interactions.

**Note**: 
- The `api_key` parameter is mandatory for initializing the `TavilyExtract` class and must be kept secure to prevent unauthorized access.
- The `base_url` and `headers` are automatically configured and cannot be modified directly through the constructor. Any changes to these values would require altering the code itself.
***
### FunctionDef extract_content(self, urls)
**extract_content**: The function of extract_content is to asynchronously request and retrieve content data from an external service based on a list of provided URLs.

**parameters**:
· urls: List[str]  
  - A list of URLs for which content needs to be extracted.

**Code Description**:  
The `extract_content` function is an asynchronous method that facilitates the extraction of content from a specified external service. The method is designed to take a list of URLs as input and then make an HTTP POST request to a remote API to retrieve the content associated with these URLs.

1. **Payload Creation**:  
   The function first constructs a payload dictionary containing the `urls` parameter passed to the function. This payload is intended to be sent as the body of the POST request.

2. **Making the API Call**:  
   Using the `httpx.AsyncClient` with HTTP/2 support enabled, the function sends an asynchronous POST request to the service’s base URL (stored in `self.base_url`). The headers (stored in `self.headers`) and the payload (containing the URLs) are included in the request. This is performed within an asynchronous context to ensure non-blocking behavior during the request.

3. **Handling Responses**:  
   Upon receiving the response, the function checks whether the request was successful by calling `response.raise_for_status()`. If the status code indicates an error (4xx/5xx), an exception is raised and caught.

4. **Error Handling**:  
   If an HTTP error occurs (e.g., 404 or 500), the function will return a dictionary with the key `error` and a message indicating that an HTTP error occurred. Similarly, if there’s an issue with the request itself (e.g., network issues), a `RequestError` is caught, and an error message is returned.

5. **Returning Data**:  
   If the request is successful, the function parses the response as JSON and returns the resulting data. This JSON data is typically structured to contain content related to the requested URLs.

In terms of its usage, the `extract_content` method is invoked within the `scrape` function found in the `src/criticsearch/tools/content_scraper/__init__.py` file. The `scrape` function calls `extract_content` to attempt content extraction using the Tavily API. If successful, it processes the returned results into a list of `ScrapedData` objects. If the extraction fails or encounters errors, it falls back to a custom web scraping mechanism via `FallbackWebScraper`. This integration ensures the robustness of the scraping process, allowing for alternative methods when the primary API fails.

**Note**:  
- The function is asynchronous and requires an `await` keyword when calling it.  
- The `httpx` library should be installed and configured correctly to ensure successful HTTP requests.  
- Proper error handling is implemented to catch both HTTP-specific and general request errors, returning meaningful error messages for each type of failure.

**Output Example**:  
A possible response when the request is successful could look like the following:

```json
{
  "results": [
    {
      "url": "http://example.com/page1",
      "raw_content": "This is the content of the first page."
    },
    {
      "url": "http://example.com/page2",
      "raw_content": "This is the content of the second page."
    }
  ],
  "failed_results": []
}
```

If there is an error, the returned dictionary may look like this:

```json
{
  "error": "HTTP error occurred: 404 Client Error: Not Found for url: http://example.com/page1"
}
```
***
