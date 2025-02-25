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
## Class: `SearchResponse`

### Overview
The `SearchResponse` class is a data model used to represent the results of a search query. It encapsulates the query itself, the list of search results, and any potential error messages that may have occurred during the search process. This class is commonly used to structure the response from a search API client, such as a Bing or DuckDuckGo search client.

### Attributes
- **query** (`str`): The search query string that was submitted by the user.
- **results** (`List[SearchResult]`): A list of `SearchResult` objects representing the individual search results. If no results are found, this list will be empty.
- **error_message** (`Optional[str]`): An optional string that contains an error message, if applicable. If an error occurred during the search, this attribute will contain a descriptive error message.

### Method

#### `ser_model() -> str`
The `ser_model` method is used to serialize the `SearchResponse` object into a human-readable string. It formats the response based on the availability of results and error messages.

- **Returns**: A formatted string representing the search response, including the query, any error message, and the details of the search results.
  
  **Behavior**:
  - If an `error_message` is provided, the method will include it in the formatted response.
  - If no results are found (i.e., `results` is an empty list), the method will indicate that no results were found.
  - If results are available, the method will format the response with the titles, URLs, and content of the search results.

### Usage Example
```python
search_response = SearchResponse(query="Python programming", results=[...], error_message=None)
print(search_response.ser_model())
```

### Notes
- The `SearchResult` class is used to structure each individual search result, containing attributes like `title`, `url`, and `content`. These details are displayed when the `ser_model` method is called, allowing for easy inspection of the search results.
- The `error_message` is optional, and if there are no errors, the response will display the search results or indicate that no results were found.

This class is useful in the context of search client responses, enabling structured representation and easy presentation of the query and search outcomes.
### FunctionDef ser_model(self)
**ser_model**: The function of ser_model is to generate a formatted string representation of the search response based on the query, error messages, and results.

**parameters**: The parameters of this Function.
· self: An instance of the class that contains the attributes query, error_message, and results.

**Code Description**: The ser_model function constructs a formatted response string that summarizes the outcome of a search operation. It first checks if there is an error message present in the instance. If an error message exists, it formats the response to include the query and the error message, followed by a line of dashes for separation. If there are no results (i.e., the results list is empty), it similarly formats the response to indicate that no results were found. In the case where there are valid search results, the function constructs a response that includes the query and iterates through the results list. For each result, it appends the index, title, URL, and content of the result to the formatted response, again followed by a line of dashes for clarity. Finally, the function returns the complete formatted response string.

**Note**: It is important to ensure that the attributes query, error_message, and results are properly initialized in the class before calling this function. The results should be a list of objects that contain title, url, and content attributes for the function to work correctly.

**Output Example**: 
```
Query: "How to use Python for data analysis?"
Error: No results found.--------------------------------------------------
```
or 
```
Query: "How to use Python for data analysis?"
Search Results:
--------------------------------------------------
[1]:
TITLE: "Data Analysis with Python"
URL: "https://example.com/data-analysis-python"
CONTENT: "This article provides an overview of data analysis techniques using Python."
--------------------------------------------------
[2]:
TITLE: "Python for Data Science"
URL: "https://example.com/python-data-science"
CONTENT: "Learn how Python is used in data science and analytics."
--------------------------------------------------
```
***
## ClassDef SearchResponseList
**SearchResponseList**: The function of SearchResponseList is to represent a list of search response objects and provide functionality to serialize them, ensuring that duplicate content across queries is removed.

**attributes**: The attributes of this Class.
· responses: A list of `SearchResponse` objects that represent the responses from multiple search queries.

**Code Description**: 
The `SearchResponseList` class is used to hold a collection of `SearchResponse` objects, each representing an individual search query's response. It provides a method, `ser_model()`, which serializes these responses into a formatted string while ensuring the removal of duplicate content across the search results.

- The class inherits from `BaseModel`, indicating that it is part of a data model system, likely designed for serialization or structured data handling.
- The primary attribute, `responses`, is a list that holds instances of `SearchResponse`. This attribute holds the individual responses from search queries and is initialized as an empty list by default.
  
The key functionality of this class is in the `ser_model()` method. This method iterates over the `SearchResponse` objects in the `responses` list and performs several actions:
1. It maintains a set of `global_seen_contents` to ensure that duplicate search results are removed across queries.
2. For each `SearchResponse`, if there is an error message (i.e., `error_message` is not `None`), the method will log the error and skip processing that response.
3. For each result in a valid `SearchResponse`, it checks if the content of the result has been seen before across all responses. If the content is unique, it is added to a list of unique results, and this result is serialized.
4. After processing, the method updates the `SearchResponse` object to reflect only unique results and keeps track of the total number of results and the unique results count. It then generates a string representation of the serialized results.
5. The method logs the number of duplicates removed and returns the final serialized string.

The `SearchResponseList` class is primarily used in the context of aggregating and serializing multiple search responses in a way that filters out redundant results. It plays a crucial role in handling multiple search queries, especially when working with multiple search engines or sources. 

From a functional perspective, this class is invoked in the `search` method of the `SearchAggregator` class. The `search` method performs concurrent searches for a list of queries, collects the responses, and returns them as an instance of `SearchResponseList`. This allows for streamlined processing and serialization of the search results, ensuring that the final output only includes unique search results from the queries.

**Note**: 
- The `ser_model()` method only includes `SearchResponse` objects that do not contain error messages in its serialization.
- It ensures that any duplicate content across multiple responses is filtered out based on the content of the search results, which helps in returning cleaner and more relevant data.
- This class uses logging to provide feedback on the serialization process, including information on skipped responses due to errors and the number of duplicates removed.

**Output Example**:
An example output of the `ser_model()` method might look like this:

```
Query: "Python programming"
Search Results:
--------------------------------------------------
[1]:
TITLE: Introduction to Python
URL: https://example.com/python
CONTENT: Python is a high-level programming language.
--------------------------------------------------
[2]:
TITLE: Python Tutorials
URL: https://example.com/tutorials
CONTENT: Learn Python programming with these tutorials.
--------------------------------------------------
Serialization completed. Total results: 5, Unique results: 3, Duplicates removed: 2.
``` 

This output shows the results of the search query, including the serialized format of unique results, and a summary of the serialization process.
### FunctionDef ser_model(self)
**ser_model**: The function of ser_model is to serialize a list of SearchResponse objects into a string, ensuring uniqueness in the content across different queries.

**parameters**: This function does not take any parameters.

**Code Description**:  
The `ser_model` method is responsible for serializing the list of `SearchResponse` objects contained within the instance. It processes each `SearchResponse` object to ensure that the search results are unique by comparing their content against a global set of previously seen content.

1. **Global Uniqueness Tracking**:  
   A set named `global_seen_contents` is used to store the content of the results encountered so far, ensuring that each result is unique across all queries processed by this method.

2. **Response Processing**:  
   The method loops over each `SearchResponse` object in `self.responses`. For each `response`, if it contains an error message, it is skipped, and the serialization continues with the next response.

3. **Result Deduplication**:  
   For each `response`, the method iterates through its `results` and checks whether the `content` of each result has already been encountered (using the `global_seen_contents` set). If a result’s content is unique (i.e., not found in the set), it is added to the list `unique_results` and the content is added to the set to prevent future duplicates. The total number of results and unique results are tracked during this process.

4. **Updating the Response**:  
   After deduplication, the `results` attribute of the `response` is updated with the `unique_results`. The count of unique results is accumulated in `unique_results_count`.

5. **Serialization**:  
   The `model_dump()` method is called on each `response` to generate its serialized string representation, which is appended to `result_str`. This `result_str` will contain the serialized data of all responses, with duplicates removed.

6. **Logging**:  
   After processing all responses, the method logs a summary message, indicating the total number of results processed, the number of unique results, and the number of duplicates removed.

7. **Return Value**:  
   Finally, the method returns the `result_str`, which contains the serialized data of the unique results.

**Note**: 
- The method ensures that only unique search results are included in the serialized output, removing any duplicates based on content.
- The method relies on the `model_dump()` method of the `SearchResponse` object to generate its string representation, which may vary depending on the implementation of that method.
- If any `SearchResponse` contains an error message, it will be skipped entirely, and no results from that response will be included in the final serialized output.

**Output Example**:  
Assuming `self.responses` contains two `SearchResponse` objects with some duplicate results, the returned `result_str` might look like this:

```
"SearchResponse(query='query1', results=[{'content': 'unique content 1'}, {'content': 'unique content 2'}])SearchResponse(query='query2', results=[{'content': 'unique content 3'}, {'content': 'unique content 1'}])"
```

In this example, 'unique content 1' is only included once, even though it appeared in multiple responses.
***
