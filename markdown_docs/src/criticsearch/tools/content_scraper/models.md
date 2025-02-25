## ClassDef ScrapedData
**ScrapedData**: The function of ScrapedData is to represent a data object that holds information scraped from a given URL, including content, title, and potential errors.

**attributes**: The attributes of this Class.
· url: str - The URL from which the data is scraped.
· title: Optional[str] - The title of the scraped page, which can be None if unavailable.
· content: Optional[str] - The main content of the scraped page, which can be None if not found or unavailable.
· error: Optional[str] - An error message, if there was an issue during scraping.

**Code Description**: The ScrapedData class is a data container that is designed to store and structure the information extracted from web scraping operations. It inherits from `BaseModel`, which likely provides data validation and serialization functionality. The class includes four attributes:

1. **url** (str): This is the URL from which content is scraped, making it an essential identifier for the scraped data.
2. **title** (Optional[str]): This attribute holds the title of the webpage or content if available, providing a reference to the type or subject of the page. It is optional and can be None if the title is not present.
3. **content** (Optional[str]): The main content that was extracted from the webpage is stored in this field. It is optional, as some pages might not have meaningful content or may not be accessible.
4. **error** (Optional[str]): This attribute is used to store any error message that might have occurred during the scraping process. If an error was encountered, this field will contain the error message; otherwise, it will be None.

The ScrapedData class plays a crucial role in both successful and failed scraping scenarios. When content is scraped successfully, the `url` and `content` attributes are populated. If there are any issues during scraping, such as an HTTP error or a failure to retrieve meaningful content, the `error` attribute will contain details about what went wrong. This class is used by the `scrape` functions found in the `FallbackWebScraper` and `ContentScraper` modules.

From a functional perspective, ScrapedData objects are instantiated during the scraping process to store the results of individual scraping attempts. If the scraping process is successful, the object is populated with data like the content of the page and its title. If scraping fails, the object includes an error message to provide insight into the issue. These instances are then collected in lists, such as `ScrapedDataList`, which is used to return the aggregated results.

The `scrape` function in `ContentScraper` first tries to extract content using the Tavily API and constructs a ScrapedData object for each URL it processes. In case of failure, it uses `FallbackWebScraper.scrape`, which also returns ScrapedData objects. These instances are used throughout the system to ensure that scraping results are handled consistently, even when some URLs result in errors.

**Note**: The `ScrapedData` class should always be handled with care, especially when dealing with failed scrapes. The presence of the `error` attribute should be checked to ensure that the scraping process was successful. Additionally, it is important to understand that content and title are optional attributes and may be missing in certain cases.
## ClassDef ScrapedDataList
**ScrapedDataList**: The function of ScrapedDataList is to represent a collection of ScrapedData objects, holding the results of web scraping, including both successful and failed attempts, with serialization capabilities to output the data in a readable format.

**attributes**: The attributes of this Class.
· data: List[ScrapedData] - A list of ScrapedData objects, representing the individual scraping results for each URL processed. It contains both successful and failed results.
· max_content_length: int - The maximum allowed length for individual scraped content. If the content exceeds this length, it will be truncated.
· max_output_length: int - The maximum length of the serialized result that can be returned. If the output exceeds this length, it will be truncated.

**Code Description**: 
The ScrapedDataList class is designed to manage a collection of ScrapedData objects, which store the results of scraping attempts for multiple URLs. It inherits from BaseModel, providing data validation and serialization capabilities. The class contains three key attributes:

1. **data** (List[ScrapedData]): This attribute holds a list of ScrapedData instances, which represent the individual results of the scraping process. Each ScrapedData object can contain information like the scraped URL, title, content, and any errors encountered during scraping. This list forms the core of the class, containing all the data gathered during scraping.

2. **max_content_length** (int): This attribute defines the maximum allowable length for the content of each scraped data object. If any scraped content exceeds this length, it will be truncated and appended with the string "[TOO LONG, END]" to indicate that the content has been cut off. The default value is set to 10,000 characters.

3. **max_output_length** (int): This attribute controls the maximum length of the entire serialized output. If the concatenated result of all scraped data exceeds this length, the output will be truncated with the message "[OUTPUT TOO LONG, TRUNCATED]" to avoid excessive output. The default value is set to 100,000 characters.

The class includes the method `ser_model`, which performs the serialization of the ScrapedDataList object into a human-readable string format. The function iterates over each ScrapedData object in the `data` attribute and processes it as follows:

- If the ScrapedData object contains an error, the method appends an error message to the result, specifying the URL and the associated error.
- If no error is found, the content is checked against the `max_content_length`. If the content exceeds this length, it is truncated to the specified limit, with the string "[TOO LONG, END]" appended to signal the truncation.
- The method then constructs a string for each ScrapedData object, including the URL, title, and content.
- All these strings are concatenated with a separator ("---") between each entry.

Finally, the complete serialized string is checked against the `max_output_length`. If the overall string exceeds the defined length, it will be truncated with the message "[OUTPUT TOO LONG, TRUNCATED]".

From a functional perspective, ScrapedDataList is typically used to aggregate multiple ScrapedData objects that represent the results of a scraping operation. For example, the `scrape` function in the `ContentScraper` module calls this class to collect the results of web scraping and returns a serialized version of the results as a string.

The ScrapedDataList class provides an efficient way to manage and output scraped data, ensuring that even large datasets are handled appropriately by applying length restrictions at both the individual content level and the overall output level. This ensures that the serialized results remain within acceptable limits for processing or logging.

**Note**: When using ScrapedDataList, ensure that the content length and output length are managed effectively, especially when handling large sets of data, to avoid data truncation. Additionally, be aware that the `error` field in ScrapedData objects may be present, and it should be checked to handle failed scraping attempts appropriately.

**Output Example**:
Here is an example of a serialized output that might be returned by the `ser_model` method:

```
URL: https://example.com/page1
Title: Example Page 1
Content:
This is the content of the first page. It contains relevant information about the topic.

---
URL: https://example.com/page2
Title: Example Page 2
Content:
This page has too much content. It is truncated here: Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. [TOO LONG, END]

[OUTPUT TOO LONG, TRUNCATED]
```
### FunctionDef ser_model(self)
**ser_model**: The function of ser_model is to generate a formatted string representation of scraped data, including error handling and content truncation.

**parameters**: The parameters of this Function.
· self: An instance of the class that contains the scraped data and configuration settings.

**Code Description**: The ser_model function processes a collection of scraped data stored in the instance variable `self.data`. It initializes an empty list called `result` to accumulate formatted strings for each data entry. The function iterates over each item in `self.data`, checking for any errors associated with the data. If an error is found, it appends an error message to the `result` list and skips further processing for that entry.

For valid entries, the function asserts that the content is not None. It then checks if the length of the content exceeds a predefined maximum length (`self.max_content_length`). If it does, the content is truncated, and a suffix indicating truncation is added. The function constructs a formatted string that includes the URL, title, and content of the data entry, which is then appended to the `result` list.

After processing all entries, the function joins the strings in the `result` list with a separator ("---") to create a single output string. It then checks if the total length of this output exceeds another predefined maximum length (`self.max_output_length`). If it does, the output is truncated, and a message indicating truncation is appended.

Finally, the function returns the formatted output string, which contains the processed information of all the scraped data entries.

**Note**: It is important to ensure that `self.data` is properly populated with valid data objects before calling this function. Additionally, the maximum lengths for content and output should be set appropriately to avoid unintended truncation.

**Output Example**: 
```
URL: http://example.com/page1
Title: Example Page 1
Content:
This is the content of the first example page.

---
URL: http://example.com/page2
Title: Example Page 2
Content:
Error for URL http://example.com/page2: Page not found

---
URL: http://example.com/page3
Title: Example Page 3
Content:
This is the content of the third example page, which is quite informative and exceeds the maximum length set for content. [TOO LONG, END]
```
***
