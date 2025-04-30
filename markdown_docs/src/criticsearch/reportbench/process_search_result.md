## FunctionDef filter_results(data)
**filter_results**: The function of filter_results is to filter out results that do not have raw content in the provided data.

**parameters**: 
· data: A dictionary containing the key "results", which is expected to hold a list of result objects.

**Code Description**: The function `filter_results` is designed to process a given dictionary called `data`. Specifically, it filters the list under the key "results" by removing any items (results) that do not contain the key "raw_content". If a result does not have "raw_content" or has it as a falsy value (e.g., None, empty string), it is excluded from the results list. The filtered data is then returned in the same dictionary format. If the "results" key does not exist in the input data, the function ensures that an empty list is used instead, effectively preventing errors during processing.

Here is a step-by-step breakdown:
1. The function first accesses the value associated with the "results" key in the input dictionary `data`.
2. It then applies a list comprehension to iterate over each item (`r`) in this list.
3. For each item, it checks whether the item contains the key "raw_content" and whether it holds a truthy value.
4. If "raw_content" exists and has a truthy value, the item is kept in the list.
5. Finally, the filtered list replaces the existing "results" key in the `data` dictionary.
6. The updated `data` dictionary is returned.

**Note**: 
- The function does not handle situations where the input `data` does not contain the "results" key at all. In this case, it will safely return the original data with an empty list under the "results" key.
- The function assumes that the "results" key, when present, always holds a list, which is a standard format for handling multiple results.

**Output Example**: 
Given the following input data:
```python
{
    "results": [
        {"raw_content": "valid content"},
        {"raw_content": None},
        {"raw_content": "another valid content"}
    ]
}
```

The output after calling `filter_results` would be:
```python
{
    "results": [
        {"raw_content": "valid content"},
        {"raw_content": "another valid content"}
    ]
}
```
## FunctionDef generate_markdown(data)
**generate_markdown**: The function of generate_markdown is to generate a markdown formatted string based on input data containing images and search results.

**parameters**:
· parameter1: data (dict) - A dictionary containing the data with two possible keys: "images" and "results". The "images" key should contain a list of image objects, and the "results" key should contain a list of search result objects.

**Code Description**: 
The `generate_markdown` function is responsible for producing a markdown-formatted string based on the given input data. The function is structured to create two main sections: one for images and another for search results. It uses the input data, which is expected to be a dictionary, and processes the "images" and "results" lists within the dictionary to construct markdown content.

1. **Images Section**: 
   The function first initializes an empty list, `lines`, to store the markdown content. It then checks if the input dictionary has an "images" key, and retrieves the associated list. For each image in this list, the function adds a description (or "N/A" if no description is found) and the URL (or "N/A" if no URL is found) to the `lines` list. The images are enumerated starting from 1, with each entry formatted as follows:
   - `[idx] DESCRIPTION: {description}`
   - `URL: {url}`
   
2. **Search Results Section**: 
   After handling the images, the function proceeds to process the "results" key, if present. It iterates over the list of search results, adding each result's title (or "N/A"), URL (or "N/A"), and raw content (or "N/A") to the markdown string. Each result is also enumerated starting from 1, and the entries are formatted as follows:
   - `[idx]: TITLE: {title}`
   - `URL: {url}`
   - `CONTENT: {raw_content}`
   
3. **Return Value**: 
   Once both the images and search results sections have been processed, the function joins all lines in the `lines` list with newline characters and returns the final string. This string contains a well-structured markdown representation of the input data.

**Note**:
- The function assumes that the "images" and "results" keys in the input data are lists of dictionaries.
- If the "description", "url", "title", "raw_content" are not provided for an item, the function defaults to "N/A".
- The function does not handle any cases where the input data structure deviates from the expected format (i.e., the presence of "images" and "results" keys).
- The markdown string generated can be directly used in markdown viewers or other systems that support markdown formatting.

**Output Example**:

```markdown
# images 

[1] DESCRIPTION: Sunset over mountains
URL: http://example.com/sunset.jpg

[2] DESCRIPTION: N/A
URL: http://example.com/placeholder.jpg

# Search Result

[1]: TITLE: Exploring the beauty of nature
URL: http://example.com/nature-article
CONTENT: This article dives deep into the beauty of nature and its impact on our lives.

[2]: TITLE: N/A
URL: http://example.com/empty-article
CONTENT: N/A
```
