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
### Class: `SearchResponseList`

#### Overview:
The `SearchResponseList` class is designed to represent a collection of `SearchResponse` objects. It provides functionality to serialize the list of search responses, ensuring unique content across all search queries by removing duplicates.

#### Attributes:
- **responses** (`List[SearchResponse]`): A list containing `SearchResponse` objects. Each `SearchResponse` encapsulates the results of a single search query, including the query string, a list of search results, and any error messages encountered during the search process. The list is initialized with an empty list by default.

#### Methods:
- **ser_model()** -> `str`:
  The `ser_model` method serializes the list of `SearchResponse` objects into a string format. This method ensures that any duplicate content across the search results is removed. The serialization process proceeds as follows:
  1. The method iterates over each `SearchResponse` in the `responses` list.
  2. If the `SearchResponse` contains an error message, it logs the error and skips serialization for that particular response.
  3. For each valid `SearchResponse`, the method checks for unique search results by comparing the `content` of each result to a global set of seen contents.
  4. The results are filtered to retain only unique entries, and the count of unique results is updated.
  5. After filtering, the method appends the serialized content of the `SearchResponse` to the result string.
  6. A summary log is generated, indicating the total number of results, the number of unique results, and the number of duplicates removed.
  
  The method returns a formatted string containing the serialized results of the search responses.

#### Example Usage:
```python
search_response_list = SearchResponseList(responses=[response1, response2])
serialized_results = search_response_list.ser_model()
```

#### Notes:
- The `responses` attribute must be populated with instances of the `SearchResponse` class.
- The method `ser_model` performs de-duplication across all responses and presents the results in a human-readable format.
- If any `SearchResponse` contains an error message, it will be skipped during serialization, ensuring that the final output only contains valid data.
### FunctionDef ser_model(self)
**ser_model**: The function of ser_model is to serialize a list of SearchResponse objects into a formatted string, ensuring unique content across different queries.

**parameters**: The parameters of this Function.
- None

**Code Description**:  
The `ser_model` method is designed to process a list of `SearchResponse` objects and serialize the relevant data into a string representation. The method ensures that content within the search responses is unique across all queries by removing duplicate results based on their content.

1. **Global Deduplication Logic**:  
   The function initializes a set called `global_seen_contents` to store content that has already been encountered. This set helps track which results have been seen across all queries, ensuring that duplicates are eliminated.

2. **Processing Search Responses**:  
   The method then iterates over each `response` in the `self.responses` list. If a response contains an `error_message`, it is skipped, and a log message is generated using the `printer.log` method to notify that the response was ignored due to an error. This ensures that only valid responses are processed.

3. **Result Deduplication**:  
   For each valid response, the method further iterates over the `results` in the response. It checks whether the `content` of each result has already been encountered by comparing it against the `global_seen_contents` set. If a result's content is unique, it is added to the list `unique_results`, and its content is stored in the set to prevent future duplicates. The method keeps track of both the total number of results and the number of unique results.

4. **Updating the Response**:  
   Once duplicates are removed, the `results` of the current `response` are updated to include only the unique results. The count of unique results is then updated.

5. **Result Serialization**:  
   After processing all responses, the `model_dump` method is called on each `response` to obtain a serialized string representation of the response, which is concatenated into the `result_str` variable.

6. **Logging the Summary**:  
   After completing the serialization process, a log message is printed using the `printer.log` method to summarize the operation. The message includes the total number of results, the number of unique results, and the number of duplicates removed.

7. **Return Value**:  
   The method returns the concatenated string (`result_str`) representing all serialized and deduplicated search responses.

**Note**:  
- The `model_dump` method is assumed to serialize each response object into a string format, and the exact format depends on its implementation.
- The `printer.log` function is used for logging, which formats the messages in a styled manner to enhance readability in the console output.
- It is important to ensure that all responses in `self.responses` are well-formed and contain the expected attributes, especially `error_message` and `results`. This method does not handle any unexpected data formats or missing attributes.

**Output Example**:  
Assuming a scenario where there are two search responses with some duplicate content, the output might look like:

```
Serialization completed. Total results: 10, Unique results: 7, Duplicates removed: 3.
<Serialized String of the Responses>
```

The string returned would contain the serialized representations of the unique search responses, with any duplicates removed based on the content comparison.
***
