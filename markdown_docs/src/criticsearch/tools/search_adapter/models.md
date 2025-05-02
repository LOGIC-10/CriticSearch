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
**SearchResponseList**: The function of SearchResponseList is to manage and serialize a list of search responses, ensuring unique content across queries while filtering out unwanted results.

**attributes**: The attributes of this Class.
· responses: A list of `SearchResponse` objects that encapsulate the results of individual search queries.

**Code Description**: The `SearchResponseList` class inherits from `BaseModel` and is designed to handle multiple `SearchResponse` objects, which represent the results of search queries. The primary attribute of this class is `responses`, which is a list that stores instances of `SearchResponse`. Each `SearchResponse` contains details about a specific search query, including the query string, a list of search results, and any error messages encountered during the search process.

The class includes a private method `_is_wiki_url`, which checks if a given URL belongs to a Wikipedia or related domain. This method is utilized within the `ser_model` method to filter out search results that are deemed irrelevant, specifically those that link to Wikipedia or similar sites. The filtering is based on a predefined list of wiki-related domains.

The `ser_model` method is responsible for serializing the list of `SearchResponse` objects into a formatted string representation. It ensures that the content across different queries is unique by maintaining a global set of seen contents. The method iterates through each `SearchResponse` in the `responses` list, checking for errors and filtering out results that are identified as wiki URLs. It counts the total number of results, the number of unique results, and the number of filtered wiki pages, logging this information for user feedback.

The `SearchResponseList` class is called by the `search` method in the `SearchAggregator` class, which performs multiple search queries concurrently. After executing the search queries, the responses are collected and passed to the `SearchResponseList` for serialization. This integration allows for efficient handling of search results, providing a structured output that can be utilized for further processing or presentation.

**Note**: It is essential to ensure that the `responses` attribute contains valid `SearchResponse` objects. The `ser_model` method relies on the proper structure of these objects to generate meaningful output. Additionally, the filtering mechanism is crucial for excluding unwanted results, which enhances the relevance of the search output.

**Output Example**: A possible return value from the `ser_model` method could be structured as follows:
```json
{
  "results": [
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
This output illustrates a successful serialization of search responses, containing the original query, a list of relevant search results, and no error messages.
### FunctionDef _is_wiki_url(self, url)
**_is_wiki_url**: The function of _is_wiki_url is to check if a given URL belongs to Wikipedia or related wiki sites.

**parameters**: The parameters of this Function.
· url: str - The URL string that needs to be checked for wiki-related domains.

**Code Description**: The `_is_wiki_url` function is a method designed to determine whether a specified URL is associated with Wikipedia or other wiki-related websites. It achieves this by maintaining a predefined list of wiki domains, which includes popular sites such as "wikipedia.org", "fandom.com", and "wikihow.com". 

The function operates as follows:
1. It accepts a single parameter, `url`, which is expected to be a string representing the URL to be evaluated.
2. The method converts the URL to lowercase to ensure that the comparison is case-insensitive.
3. It then checks if any of the domains in the `wiki_domains` list are present in the provided URL using a generator expression combined with the `any()` function. This approach efficiently evaluates each domain against the URL.
4. If any domain from the list is found within the URL, the function returns `True`, indicating that the URL is indeed a wiki-related link. If none of the domains match, it returns `False`.

The `_is_wiki_url` function is called within the `ser_model` method of the `SearchResponseList` class. In this context, it plays a crucial role in filtering search results. Specifically, during the serialization process of search responses, the `ser_model` method utilizes `_is_wiki_url` to identify and exclude any results that are links to wiki pages. This filtering ensures that the final serialized output contains only unique and relevant content, thereby enhancing the quality of the search results presented to the user.

**Note**: The function is designed to be straightforward and efficient, focusing solely on the presence of specific domains within the URL. It is essential for maintaining the integrity of the search results by preventing wiki-related content from being included in the final output.

**Output Example**: The function will return a boolean value, such as `True` for a URL like "https://en.wikipedia.org/wiki/Example" and `False` for a URL like "https://example.com".
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
