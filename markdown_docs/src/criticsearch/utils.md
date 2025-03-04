## FunctionDef count_tokens(text, model)
**count_tokens**: The function of count_tokens is to calculate the number of tokens in a given text string based on a specified model.

**parameters**:
· text: The input text that needs to be tokenized.
· model: The model to be used for tokenization. Default is "gpt-4o". This parameter allows the selection of different models that might affect the tokenization method. Common options include "gpt-3.5-turbo", "gpt-4", and "text-embedding-ada-002".

**Code Description**: 
The function `count_tokens` is designed to calculate the number of tokens in a provided text based on a selected model for tokenization. The process begins by determining the correct encoding method for the specified model using the `tiktoken` library, which is responsible for breaking the text into tokens.

1. The function first attempts to fetch the appropriate encoding for the specified model using `tiktoken.encoding_for_model(model)`.
2. If the provided model does not exist or is unsupported (raising a `KeyError`), it defaults to using a fallback encoding, `tiktoken.get_encoding("cl100k_base")`.
3. The text is then encoded into tokens using the encoding method, and the number of tokens is returned by evaluating the length of the tokenized text.

The function is used in scenarios where it's necessary to measure the token count of a text, particularly when dealing with AI models like OpenAI's GPT family, which have token limits for inputs. This is especially useful in contexts such as text preprocessing or chunking operations, where token limits need to be respected.

In the project, `count_tokens` is employed within the `extract_sections` function, which recursively processes sections of a dataset to extract content, titles, and their respective paths. The token count for each section's content is calculated and stored in the resulting data structure. The token count is a crucial piece of information because it helps in ensuring that sections do not exceed certain token limits, particularly when preparing inputs for processing by machine learning models, such as in the case of the `sliding_window_pairing` function.

In the `sliding_window_pairing` function, the `count_tokens` function is critical for ensuring that each "window" of text remains within a specified token limit (`max_token_length`). By calculating the token count for each section, the function can group sections together in a way that ensures the total number of tokens in any given window does not exceed the maximum allowable tokens for the model, making it essential for efficient and valid data processing.

**Note**:
- The `count_tokens` function depends on the `tiktoken` library, which must be available in the environment.
- If an unsupported model is passed, the function will use a fallback tokenization model, but results may differ slightly depending on the encoding used.
- The function is optimized to handle different models, and using an inappropriate model might result in less accurate token counts if the fallback encoding is used.

**Output Example**:
For example, when calling `count_tokens("Hello, world!")`, the function will return the token count of the string. Assuming "Hello" and "world!" are treated as separate tokens, the output might be:

```
4
```
## FunctionDef extract_queries_from_response(response_text)
## `extract_queries_from_response` Function

### Description
The `extract_queries_from_response` function is designed to extract a list of queries from a given response text. The function supports multiple formats for the input text and processes them to return a list of queries. If no valid queries are found, the function returns an empty list.

### Parameters
- **response_text** (`str`): The input response text containing potential query information. The response text can be in one of the following formats:
  - `<queries>[query1, query2]</queries>`
  - `<queries>List[str] = [query1, query2]</queries>`
  - `<queries> [query1, query2] </queries>`

### Returns
- **list**: A list of extracted queries. If no queries are found, an empty list is returned.

### Functionality
1. The function first strips any leading or trailing whitespace from the input `response_text`.
2. It then attempts to match the text against two possible patterns:
   - The first pattern matches a format where queries are wrapped in a `List[str] = [...]` structure.
   - The second pattern matches the standard array-like format `[query1, query2]`.
3. If a match is found, the queries are extracted and further processed:
   - The extracted query string is split based on regular expressions, taking into account commas within quotes to avoid splitting queries incorrectly.
   - Each part is cleaned of any surrounding quotes and extra whitespace.
4. The cleaned queries are returned as a list.
5. If no valid queries are extracted, the function returns an empty list.

### Example
```python
response_text = "<queries>[\"query1\", \"query2\"]</queries>"
queries = extract_queries_from_response(response_text)
print(queries)  # Output: ['query1', 'query2']
```

### Notes
- The function supports both single-quoted and double-quoted strings for the queries.
- It uses regular expressions to identify and extract the query list, ensuring flexibility in handling different formatting variations.
## FunctionDef extract_thought_from_response(response_text)
**extract_thought_from_response**: The function of extract_thought_from_response is to extract the thought content from a given response text formatted with specific tags.

**parameters**: The parameters of this Function.
· response_text: A string containing the response text that includes thought content formatted with `<\thought>...<\thought>`.

**Code Description**: The extract_thought_from_response function is designed to parse a string input, specifically looking for content enclosed within the tags `<thought>` and `</thought>`. It utilizes a regular expression pattern to identify and extract the desired content. The function first compiles a regex pattern that matches any text between the `<thought>` and `</thought>` tags. It then applies this pattern to the provided response_text using the re.search method, which allows for matching across multiple lines due to the re.DOTALL flag. If a match is found, the function returns the extracted thought content, stripped of any leading or trailing whitespace. If no match is found, it returns an empty string.

This function is called within the process_single_task function located in the src/criticsearch/main.py file. During the execution of process_single_task, after generating a response from an agent, extract_thought_from_response is invoked to retrieve the thought process from the agent's response. This extracted thought content is then logged and can be used for further processing, such as appending to conversation data or for debugging purposes. The function plays a crucial role in ensuring that the thought processes of the agent are captured and utilized effectively within the broader task processing workflow.

**Note**: It is important to ensure that the response_text provided to this function is correctly formatted with the appropriate thought tags; otherwise, the function will not be able to extract any content and will return an empty string.

**Output Example**: Given a response_text of "Here is my thought: <thought>This is the extracted thought content.</thought>", the function would return "This is the extracted thought content."
## FunctionDef extract_answer_from_response(response_text)
**extract_answer_from_response**: The function of extract_answer_from_response is to extract the content of the answer from a given response text formatted with specific tags.

**parameters**: The parameters of this Function.
· response_text: A string containing the response text that includes the answer enclosed within `<answer>` tags.

**Code Description**: The extract_answer_from_response function is designed to parse a string input, specifically looking for content that is encapsulated within `<answer>` tags. It utilizes a regular expression pattern to identify and extract the text that appears between these tags. The function employs the `re.search` method from the `re` module, which searches the input string for the specified pattern. If a match is found, the function retrieves the matched content, trims any leading or trailing whitespace, and returns it as a string. If no match is found, the function returns an empty string.

This function is called within the process_single_task function located in the src/criticsearch/main.py file. In this context, extract_answer_from_response is utilized to extract the answer content from the section content generated by the common agent during the processing of a task. After generating the section content, the function is invoked to retrieve the answer, which is then stored in the conversation data structure along with other relevant information such as thought content and citations. This integration is crucial for maintaining the flow of information and ensuring that the generated reports contain the necessary answers derived from the agent's responses.

**Note**: It is important to ensure that the response_text provided to this function is correctly formatted with the `<answer>` tags; otherwise, the function will return an empty string, indicating that no answer content was found.

**Output Example**: If the input response_text is "Here is the answer: <answer>This is the extracted answer.</answer>", the function will return "This is the extracted answer."
## FunctionDef extract_citations(text)
**extract_citations**: The function of extract_citations is to extract all referenced URLs from a given text and ensure they are unique.

**parameters**: The parameters of this Function.
· text: A string that contains text formatted with <\citation>URL<\citation> tags.

**Code Description**: The extract_citations function is designed to identify and extract URLs that are enclosed within specific citation tags in a provided text. The function takes a single argument, 'text', which is expected to be a string containing one or more citations formatted as <\citation>URL<\citation>. 

The function initializes an empty set called 'citations' to store the unique URLs. It then defines a regular expression pattern, `r'citation>(.*?)<'`, which is used to search for matches in the input text. This pattern looks for any substring that starts with 'citation>' and ends with '<', capturing the content in between. 

Using the `re.findall` method, the function searches the input text for all occurrences that match the defined pattern. If any matches are found, they are added to the 'citations' set, which automatically handles duplicates by only retaining unique entries. Finally, the function returns the 'citations' set, which will contain all the extracted URLs. If no citations are found, an empty set is returned.

**Note**: It is important to ensure that the input text is correctly formatted with the specified citation tags for the function to work effectively. The function relies on the presence of these tags to identify and extract URLs.

**Output Example**: An example of the function's return value could be a set containing URLs such as {'http://example.com', 'http://anotherexample.com'} if those URLs were found in the input text. If no URLs are found, the output would be an empty set: set().
