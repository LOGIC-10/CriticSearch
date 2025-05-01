## ClassDef SearchResult
**SearchResult**: The function of SearchResult is to represent an individual search result, encapsulating details such as the title, URL, and content.

**attributes**: The attributes of this Class.
· title: A string representing the title of the search result.  
· url: A string representing the URL of the search result.  
· content: A string containing a brief description or snippet of the content of the search result.  

**Code Description**:  
The `SearchResult` class is a data model that stores information about a single search result retrieved from a search engine API. It inherits from `BaseModel`, suggesting that it is likely used with Pydantic or a similar library for data validation and serialization. 

- `title`: This attribute holds the title of the search result. It is represented as a string and typically corresponds to the main heading or name of the webpage or resource returned in the search results.
  
- `url`: This attribute contains the URL string that directs to the search result. It is essential for linking directly to the content described in the `title`.

- `content`: This is a string attribute that contains a brief snippet or preview of the content found at the given URL. This snippet is often a portion of text extracted from the webpage to give users a preview of what the page is about.

The `SearchResult` class is frequently used in the context of search operations, where it is populated with relevant data for each individual search result. This can be seen in the `search` methods of both `BingClient` and `DuckDuckGoClient`. In these classes, after performing a search query, a list of `SearchResult` instances is created, each representing an individual result in the response from the respective search engine API.

In the `BingClient.search` method, for example, the response from the Bing API is parsed, and each item in the list of results is used to instantiate a `SearchResult` object with the corresponding title, URL, and content snippet. The resulting list of `SearchResult` instances is then included in a `SearchResponse` object, which encapsulates the entire search result for further use.

Similarly, in the `DuckDuckGoClient.search` method, the search results are processed, and a list of `SearchResult` objects is created, each holding the title, URL, and content for the results returned by DuckDuckGo.

**Note**:  
- The attributes `title`, `url`, and `content` are expected to be provided when creating an instance of `SearchResult`. Missing or malformed values may lead to errors, especially in systems that rely on proper data validation.
- The `SearchResult` class is often used as part of a larger response object, such as `SearchResponse`, which groups together multiple `SearchResult` instances along with metadata like the search query and potential error messages.
- It is important that each `SearchResult` contains relevant and accurate data, as it directly reflects the results returned by external search APIs, which may vary in structure.
## ClassDef SearchResponse
**SearchResponse**: The function of SearchResponse is to encapsulate the results of a search query, including the query string, a list of search results, and any error messages encountered during the search process.

**attributes**: The attributes of this Class.
· query: A string representing the user's search query.  
· results: A list of `SearchResult` objects that represent the individual search results returned from the query.  
· error_message: An optional string that contains an error message if an error occurred during the search.

**Code Description**: The `SearchResponse` class is a data model that serves to structure the response from search queries. It inherits from `BaseModel`, indicating that it is likely part of a data validation and serialization framework, such as Pydantic. 

The primary attributes of the `SearchResponse` class include:
- `query`: This attribute holds the search query string that was submitted by the user. It is essential for understanding the context of the results returned.
- `results`: This attribute is a list of `SearchResult` instances, each representing an individual result from the search query. The `SearchResult` class encapsulates details such as the title, URL, and content snippet of each search result.
- `error_message`: This optional attribute is used to convey any error messages that may arise during the search process. If no errors occur, this attribute will be `None`.

The `SearchResponse` class includes a method named `ser_model`, which is responsible for serializing the response into a formatted string. This method constructs a human-readable representation of the search results. It checks for the presence of an error message and formats the output accordingly. If there are no results, it indicates that no results were found. If results are present, it enumerates through each `SearchResult`, appending its details to the formatted string.

The `SearchResponse` class is utilized by various search client implementations, such as `BingClient` and `DuckDuckGoClient`. In these implementations, after executing a search query, the results are collected and instantiated as `SearchResult` objects. These objects are then aggregated into a `SearchResponse` object, which is returned to the caller. This structured response allows for consistent handling of search results across different search engines.

For example, in the `BingClient.search` method, after successfully retrieving search results from the Bing API, a list of `SearchResult` instances is created. This list, along with the original query and any potential error messages, is used to construct a `SearchResponse` object that is returned to the user.

**Note**: 
- The `query` attribute must be a valid string representing the user's search input. 
- The `results` attribute will contain a list of `SearchResult` objects, which must be populated with valid data to ensure meaningful output.
- The `error_message` attribute is optional and should be used to provide feedback in case of errors during the search process.
- Proper handling of the `SearchResponse` object is crucial for applications that rely on search functionality, as it encapsulates both successful results and error states.

**Output Example**: A possible return value of the `SearchResponse` object could be structured as follows:
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
### FunctionDef ser_model(self)
**ser_model**: The function of ser_model is to generate a formatted string representation of the search response, including the query, any errors, and the results.

**parameters**: This function does not take any parameters.

**Code Description**:  
The `ser_model` function generates a formatted string that presents the search results or error messages associated with a search query. It checks for the presence of an error message or results in the following order:

1. If there is an error message, the function creates a formatted response containing the query and the error message, followed by a separator line.
2. If the `results` list is empty, it generates a formatted response indicating that no results were found, including the query and an appropriate error message, followed by a separator line.
3. If there are search results, the function formats the response with the query and a header indicating search results. It then iterates over the results, adding details such as the title, URL, and content of each result, followed by a separator line after each entry.

The final formatted string is returned to the caller. This function is useful for presenting a search summary in a readable format, including any potential errors or results from a search operation.

**Note**:  
- This function does not take any input parameters, as it operates on the attributes of the object it is a part of. 
- The function relies on the `query`, `error_message`, and `results` attributes of the object to generate the formatted response. It assumes that `results` is a list of objects that have `title`, `url`, and `content` attributes.

**Output Example**:  
Here’s an example of the returned string based on different scenarios:

1. **Error with a message:**

```
Query: example query
Error: Something went wrong.
--------------------------------------------------
```

2. **No results found:**

```
Query: example query
Error: No results found.
--------------------------------------------------
```

3. **With search results:**

```
Query: example query
Search Results:
--------------------------------------------------
[1]:
TITLE: Example Title 1
URL: http://example.com/1
CONTENT: Example content for result 1.
--------------------------------------------------
[2]:
TITLE: Example Title 2
URL: http://example.com/2
CONTENT: Example content for result 2.
--------------------------------------------------
```
***
## ClassDef SearchResponseList
**SearchResponseList**: The `SearchResponseList` class is designed to encapsulate and manage a list of search responses, specifically handling the serialization and filtering of search results. It provides functionality to ensure unique content across multiple search responses while also allowing for the removal of irrelevant results, such as Wikipedia links.

### Detailed Analysis

The `SearchResponseList` class inherits from `BaseModel`, indicating that it is part of a data model system that provides validation and serialization features, likely provided by frameworks such as Pydantic.

#### Attributes:
- **responses** (`List[SearchResponse]`): This attribute holds a list of `SearchResponse` objects. Each `SearchResponse` corresponds to a search query and contains the results or errors associated with that query.

#### Methods:

1. **_is_wiki_url** (`url: str`) -> `bool`:  
   This private method checks if a given URL belongs to a Wikipedia-related domain. It scans the URL for known Wikipedia-related domain names (e.g., "wikipedia.org", "wiki.", "fandom.com", etc.) and returns `True` if the URL matches any of these domains, and `False` otherwise. This method is used later in the class to filter out Wikipedia-related results from the search responses.

2. **ser_model** () -> `str`:  
   This method is responsible for serializing the search responses into a structured string format. It processes the list of `SearchResponse` objects, ensuring that only unique search results are included, while also filtering out Wikipedia-related URLs.  
   
   The serialization process involves the following key steps:
   - **Global Deduplication**: The method maintains a `global_seen_contents` set to track and eliminate duplicate search results across all responses. If a result has already been encountered (based on its content), it is skipped.
   - **Wiki Filtering**: The method calls `_is_wiki_url` to identify and exclude any search results that link to Wikipedia-related domains, effectively filtering out irrelevant results.
   - **Error Handling**: If any search response contains an error message (i.e., `response.error_message` is not `None`), it is logged and skipped during serialization.
   - **Result Counting**: The method also keeps track of the total number of results, the number of unique results, and the number of filtered Wikipedia results.
   - **Final Serialization**: Once the filtering and deduplication processes are complete, the method constructs a serialized string by calling `model_dump()` on each `SearchResponse` object. This method is assumed to generate a string representation of the `SearchResponse` in a standardized format.
   
   At the end of the process, the method logs important statistics, including the total number of results, the number of unique results, the number of duplicates removed, and the number of Wikipedia links filtered. This information is logged using the `printer.log` method, which is likely a utility for logging output messages.

   The final result of the method is a string representation of the serialized search responses.

#### Usage Context:

The `SearchResponseList` class is primarily used in the `search` method of the `SearchAggregator` class. This method performs concurrent searches using multiple search engines and aggregates the results into a `SearchResponseList` object. Once all search tasks are completed, the method calls `SearchResponseList.ser_model()` to serialize the results into a structured string.

The serialized string is returned as the output of the `search` method. This output provides a clear, formatted representation of the search results, which can be used for further processing or presentation.

### Key Notes:
- The `responses` attribute must be a list of valid `SearchResponse` objects. Each `SearchResponse` should contain a properly formatted search query, a list of `SearchResult` objects, and optionally, an error message.
- The `ser_model` method performs global deduplication and wiki filtering, which is crucial for ensuring that the final output contains only unique and relevant search results.
- The `ser_model` method logs important statistics about the filtering process, which helps in tracking the effectiveness of deduplication and filtering steps.
- The class depends on the `SearchResponse` class for individual search query responses and the `SearchResult` class for individual search results. Proper handling of these classes is essential for the correct functioning of `SearchResponseList`.

### Example Output:
The `ser_model` method might return a serialized string like this:
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
This serialized output represents a list of search responses, each containing the query, the list of unique results, and any associated error messages.
### FunctionDef _is_wiki_url(self, url)
**_is_wiki_url**: The function of _is_wiki_url is to check if a given URL belongs to Wikipedia or related wiki sites.

**parameters**: The parameters of this Function.
· url: str - The URL string that needs to be checked for its affiliation with wiki-related domains.

**Code Description**: The _is_wiki_url method is designed to determine whether a specified URL is associated with Wikipedia or other wiki-related websites. It achieves this by checking the provided URL against a predefined list of wiki domains. The method converts the URL to lowercase to ensure that the comparison is case-insensitive. 

The method utilizes a list called `wiki_domains`, which contains the following entries:
- "wikipedia.org"
- "wiki."
- "fandom.com"
- "wikimedia.org"
- "wiktionary.org"

The core functionality of the method is implemented using a generator expression within the `any()` function. This expression iterates over each domain in the `wiki_domains` list and checks if any of these domains are present in the lowercase version of the provided URL. If at least one domain is found, the method returns `True`, indicating that the URL is indeed a wiki-related URL. If none of the domains match, it returns `False`.

This method is called within the `ser_model` function of the `SearchResponseList` class. In that context, it is used to filter out search results that link to wiki pages before performing serialization. Specifically, when processing each search response, the `ser_model` function checks each result's URL using the `_is_wiki_url` method. If the URL is identified as a wiki URL, that result is skipped, ensuring that only non-wiki content is included in the final serialized output. This filtering is crucial for maintaining the relevance and uniqueness of the search results being processed.

**Note**: It is important to ensure that the input URL is a valid string format. The method does not handle exceptions or errors related to malformed URLs; it simply checks for the presence of specified domains.

**Output Example**: 
For a URL input such as "https://en.wikipedia.org/wiki/Python_(programming_language)", the method would return `True`, while for "https://www.example.com", it would return `False`.
***
### FunctionDef ser_model(self)
**ser_model**: The function of ser_model is to serialize a list of SearchResponse objects into a formatted string representation, ensuring unique content across queries.

**parameters**: The parameters of this Function.
· None

**Code Description**: 
The `ser_model` function is a method designed to process and serialize a collection of `SearchResponse` objects, ensuring that the serialized output contains only unique content across all queries. The function operates in the following steps:

1. **Initialization**: 
   - A `global_seen_contents` set is created to track the content that has already been processed, ensuring uniqueness. This set will hold the content of search results, preventing duplicates.
   - Counters such as `total_results`, `unique_results_count`, and `filtered_wiki_count` are initialized to track the number of total search results, unique results, and results filtered out due to being wiki-related content.

2. **Processing Each Response**: 
   - The method iterates over the `responses` list, which contains the search results of a query. For each response, it checks if an error message is present. If an error exists, it logs the issue using the `printer.log` method and skips further processing for that particular response.
   - If no error is present, it proceeds to process each result in the `response.results` list.

3. **Filtering and Deduplication**: 
   - For each search result (`res`), the method checks if the URL corresponds to a wiki-related page using the `_is_wiki_url` method. If the result is a wiki URL, it is skipped, and the `filtered_wiki_count` is incremented.
   - For non-wiki results, the function checks if the result's content has been encountered previously (via the `global_seen_contents` set). If the content is unique (not found in the set), it is added to the set and appended to the list of `unique_results`.

4. **Serialization**: 
   - After processing all results for a given response, the filtered and unique results are stored back in the response's `results` list.
   - The method then increments the `unique_results_count` by the number of unique results found and appends the serialized output of the current response (using `response.model_dump()`) to the `result_str`.

5. **Logging and Summary**: 
   - After all responses have been processed, a summary of the serialization process is logged using `printer.log`. This summary includes the total number of results processed, the number of unique results, the number of duplicates removed, and the number of wiki pages filtered.

6. **Return Value**: 
   - The method returns a concatenated string (`result_str`), which contains the serialized representation of all the processed and filtered search results.

**Note**: 
- It is important to note that the method relies on the `_is_wiki_url` method for filtering out wiki-related content. This filtering ensures that only non-wiki content is included in the final serialized output.
- The `printer.log` function is used to provide logs regarding the serialization process, including skipped queries due to errors and a summary of the results after serialization.
- The method does not perform any error handling for potential issues in the `response.model_dump()` function, assuming that the response objects are properly structured and serializable.

**Output Example**:
An example of the serialized string returned by the method could look like this:

```
"Response 1 serialized data... Response 2 serialized data... Response 3 serialized data..."
```

This string will include the serialized data of each `SearchResponse` object, formatted according to the `model_dump()` method of the respective `SearchResponse`.
***
