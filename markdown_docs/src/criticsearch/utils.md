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
## `extract_queries_from_response` Function Documentation

### Function Signature:
```python
def extract_queries_from_response(response_text: str) -> list:
```

### Description:
The `extract_queries_from_response` function processes a given string (`response_text`), which is expected to contain query data in specific formats, and extracts a list of queries from it. The function uses regular expressions to match and retrieve query data from the response text, handling two potential formats for the query data. After extracting the raw query string, the function further processes it by removing unnecessary characters, such as quotes and extra spaces.

### Parameters:
- **response_text** (`str`): The input string containing the response text from which queries will be extracted. This string must contain query data wrapped in specific XML-like tags (`<queries>`).

### Returns:
- **list**: A list of strings, where each string represents a query extracted from the `response_text`. If no queries are found or the input format is invalid, an empty list is returned.

### Functionality:
1. **Preprocessing**: The function first trims any leading or trailing whitespace from the `response_text`.
2. **Pattern Matching**: It uses two regular expression patterns to match and extract the query data. The patterns are designed to handle two possible formats:
   - `<queries>List[str] = [...]</queries>`
   - `<queries>[...]</queries>`
3. **Query Extraction**: Once a match is found, the function captures the part of the string that contains the queries. It then splits this string into individual queries, considering the possibility of quotes around query strings.
4. **Cleaning**: Each extracted query is cleaned by stripping extra spaces and removing any surrounding quotes (either single or double quotes).
5. **Return**: The function returns a list of cleaned queries. If no queries are found, it returns an empty list.

### Example:
#### Input:
```python
response_text = '<queries>[ "query1", "query2", "query3" ]</queries>'
extract_queries_from_response(response_text)
```

#### Output:
```python
['query1', 'query2', 'query3']
```

### Usage:
This function is typically used to parse response texts from various data sources (e.g., APIs, templates) where queries are embedded in a structured format. It is commonly invoked to extract search or task-related queries for further processing, such as sending them to a search engine or using them in a decision-making process.

### Notes:
- The function assumes that the queries are enclosed within the `<queries>` tag in the input text.
- It can handle both `List[str]` and basic array-like representations of the queries within the `<queries>` tag.
- The function is case-insensitive and allows for flexible formatting within the tags.
## FunctionDef extract_thought_from_response(response_text)
## Function Documentation: `extract_thought_from_response`

### Description:
The `extract_thought_from_response` function is responsible for extracting the content of the `<thought>` tag from a given response text. This function identifies the content enclosed within the `<thought>...</thought>` tags and returns it as a string. If no such content is found, the function returns an empty string.

### Parameters:
- **response_text** (`str`): A string containing the response text in which the `<thought>...</thought>` tag is expected to appear. The content of the `<thought>` tag will be extracted.

### Returns:
- **str**: The content extracted from within the `<thought>` tag. If no `<thought>` tag is found in the `response_text`, an empty string is returned.

### Example Usage:

```python
response_text = "<thought>This is the thought content.</thought> Other content."
thought = extract_thought_from_response(response_text)
print(thought)  # Output: "This is the thought content."
```

### Implementation Details:
The function uses a regular expression (`<thought>(.*?)</thought>`) to search for the content enclosed within the `<thought>` tags. The `re.DOTALL` flag is used to allow the dot (`.`) to match newline characters, while `re.IGNORECASE` ensures the search is case-insensitive. If a match is found, the content inside the `<thought>` tags is returned after stripping any leading or trailing whitespace. If no match is found, an empty string is returned.

### Code Example:

```python
import re

def extract_thought_from_response(response_text: str) -> str:
    """
    Extracts the thought content from a response text.

    Args:
        response_text (str): The response text containing <thought>...</thought> tags.

    Returns:
        str: The extracted thought content, or an empty string if no thought content is found.
    """
    thought_pattern = r'<thought>(.*?)</thought>'
    thought_match = re.search(thought_pattern, response_text, re.DOTALL | re.IGNORECASE)
    if thought_match:
        return thought_match.group(1).strip()
    return ""
``` 

### Summary:
The `extract_thought_from_response` function is designed to efficiently extract specific thought content from structured response text. It is especially useful when working with formatted responses where certain pieces of information are encapsulated in custom tags.
## FunctionDef extract_answer_from_response(response_text)
**extract_answer_from_response**: The function of extract_answer_from_response is to extract the content between `<answer>` and `</answer>` tags from a given response text.

**parameters**:  
· response_text: A string that contains a response with content enclosed in `<answer>` and `</answer>` tags.

**Code Description**:  
The function `extract_answer_from_response` is designed to extract the content of an `<answer>` tag from a provided `response_text` string. It uses a regular expression to search for the pattern that matches the content within `<answer>` and `</answer>` tags. If a match is found, it returns the extracted content, stripping any leading or trailing whitespace. If no such content is found, the function returns an empty string.

The function operates as follows:
1. It defines a regular expression pattern (`answer_pattern`) to match the content between `<answer>` and `</answer>` tags. The pattern `r'<answer>(.*?)</answer>'` utilizes non-greedy matching to ensure it captures everything between the tags.
2. The function then uses `re.search` with the `re.DOTALL` and `re.IGNORECASE` flags. The `re.DOTALL` flag allows the dot (`.`) to match newline characters, while `re.IGNORECASE` makes the search case-insensitive.
3. If a match is found, the function extracts the content using `group(1)`, which refers to the first captured group (the content inside the `<answer>` tags). The `strip()` method is applied to remove any leading or trailing whitespace.
4. If no match is found, the function returns an empty string.

This function is used in the project primarily to retrieve the answer portion from a larger response that may contain other content. For example, in `src/criticsearch/main.py/_action_router`, after generating a section of content with `agent.chat_with_template`, the `extract_answer_from_response` function is invoked to extract the answer content from the generated response. The extracted answer is then processed and logged as part of the agent's training data.

**Note**:  
- The function relies on proper formatting of the input string, specifically the presence of the `<answer>` and `</answer>` tags. If these tags are missing or incorrectly formatted, the function will return an empty string.
- This function is case-insensitive, meaning it will match tags like `<ANSWER>` and `<answer>` equally.
- If the response text contains multiple `<answer>` sections, only the content of the first match will be returned.

**Output Example**:  
For a response text like:

```html
<response>
    <answer>This is the extracted answer.</answer>
</response>
```

The function will return:

```python
"This is the extracted answer."
```

If no `<answer>` tag is found in the response text, the function will return:

```python
""
```
## FunctionDef extract_boxed_content(answer)
### Function: `extract_boxed_content`

#### Purpose:
The `extract_boxed_content` function extracts the content enclosed within a LaTeX `\boxed{}` expression from a given answer string. If the `\boxed{}` expression is not found, it returns the original answer string.

#### Arguments:
- **answer** (`str`): A string that may contain content enclosed in a `\boxed{}` expression. This argument represents the answer text without any tags.

#### Returns:
- **str**: The content inside the `\boxed{}` expression if it is found. If no such content is found, the function returns the original `answer` string.

#### Description:
This function searches for the LaTeX syntax `\boxed{}` in the provided `answer` string using a regular expression. If a match is found, it extracts and returns the content inside the `\boxed{}`. If no match is found, it returns the original input string unchanged.

#### Example Usage:
```python
answer = "The solution is \\boxed{42}"
result = extract_boxed_content(answer)
print(result)  # Output: 42

answer = "The solution is 42"
result = extract_boxed_content(answer)
print(result)  # Output: The solution is 42
```

#### Notes:
- The function assumes that the `answer` string might contain LaTeX-style boxed content, and it will only extract content if it is enclosed within `\boxed{}`.
- The function uses regular expressions to identify and extract the boxed content efficiently.

---

This function is primarily used to parse and extract boxed content from responses generated by models or other textual inputs in contexts such as automated evaluation or formatted output validation.
## FunctionDef extract_citations(text)
**extract_citations**: The function of extract_citations is to extract all unique URLs contained within `<citation>` tags from a given text.

**parameters**: The parameters of this Function are as follows:
· text: A string representing the input text from which URLs will be extracted.

**Code Description**: The extract_citations function utilizes a regular expression pattern to identify and extract URLs that are enclosed within `<citation>` tags in the provided text. The function begins by defining a regex pattern that matches the content between `<citation>` and `</citation>` tags. It then employs the re.findall method to search through the input text, capturing all matches while ignoring case and allowing for multiline content.

After obtaining the matches, the function processes the list of URLs by stripping any leading or trailing whitespace from each URL. It filters out any empty strings that may result from the extraction process. To ensure that the returned list of URLs is unique while preserving the original order, the function converts the list to a dictionary and back to a list. This effectively removes duplicates since dictionary keys must be unique.

The extract_citations function is called within other functions in the project, specifically in process_section and parse_markdown_to_structure. In process_section, it is used to extract citations from paragraphs of text, allowing the function to associate relevant URLs with their respective paragraphs. Similarly, in parse_markdown_to_structure, it extracts citations from markdown text, ensuring that any URLs present in the document structure are captured and organized accordingly. This integration is crucial for maintaining the integrity of citations throughout the document processing workflow.

**Note**: It is important to ensure that the input text is properly formatted and contains the expected `<citation>` tags for the function to operate effectively. If the tags are missing or incorrectly formatted, the function may return an empty list.

**Output Example**: A possible return value from the extract_citations function could be:
```python
["http://example.com/citation1", "http://example.com/citation2"]
```
## FunctionDef extract_notes(response_text)
**extract_notes**: The function of extract_notes is to extract a list of notes from a given response text formatted in a specific way.

**parameters**: The parameters of this Function.
· response_text: A string containing the response text that includes notes formatted as <note>...</note> within an <answer>...</answer> structure.

**Code Description**: The extract_notes function is designed to parse a string input, specifically looking for notes encapsulated within <note> tags. It utilizes a regular expression to find all occurrences of the note content in the provided response_text. The function ensures that only well-formed notes are included in the output list. A note is considered valid if it contains both <citation> and </citation> tags, and the counts of these tags must match, indicating that the citation is properly closed. 

The function returns a list of valid notes. If no valid notes are found, it returns an empty list. This function is particularly useful in contexts where responses from a chat or API may contain structured data, and there is a need to extract specific information for further processing or storage.

The extract_notes function is called within the taking_notes method of the BaseAgent class. In this context, it processes the results obtained from a search operation. The results are passed to extract_notes to retrieve any notes that can be recorded. If valid notes are extracted, they are converted into a set to ensure uniqueness before being added to the agent's memo. This integration highlights the utility of extract_notes in managing and organizing information derived from external sources.

**Note**: It is important to ensure that the response_text is formatted correctly according to the expected structure. Any deviations from the expected format may result in an empty list being returned, as the function is strict about the validity of the notes.

**Output Example**: A possible appearance of the code's return value could be:
[
    "First note content with <citation>http://example1.com</citation>",
    "Second note content with <citation>http://example2.com</citation>"
]
## FunctionDef extract_actions(text)
**extract_actions**: The function of extract_actions is to extract all actions from a given text and ensure they are unique.

**parameters**: The parameters of this Function.
· text: A string containing text formatted with <action>...</action> tags.

**Code Description**: The extract_actions function is designed to parse a string input, searching for specific patterns that denote actions within the text. It utilizes a regular expression to identify all occurrences of text enclosed within <action> and </action> tags. The function compiles these matches into a set, which inherently removes any duplicate entries, ensuring that the returned collection of actions is unique.

The function begins by initializing an empty set named 'actions'. It then defines a regular expression pattern that matches any content between the specified action tags. The re.findall method is employed to search through the provided text, with the flags re.DOTALL and re.IGNORECASE allowing for multiline matches and case-insensitive searching, respectively. If any matches are found, they are stripped of leading and trailing whitespace and added to the 'actions' set. Finally, the function returns this set of unique actions. If no actions are found, an empty set is returned.

The extract_actions function is called within the _model_action_decision function located in the src/criticsearch/main.py file. In this context, it processes the decision made by an agent, which is derived from a chat interaction. After obtaining the decision, the extract_actions function is invoked to retrieve any actions specified in the agent's response. The presence of actions is crucial for the subsequent logic in _model_action_decision, as it determines the flow of the program based on the actions identified (e.g., SEARCH, BROWSE, START_WRITING). If no actions are found, an exception is raised, indicating an invalid decision.

**Note**: It is important to ensure that the input text is correctly formatted with the <action> tags for the function to work effectively. The function is case-insensitive, which allows for flexibility in the input format.

**Output Example**: An example of the output when the input text is "<action>SEARCH</action><action>BROWSE</action>" would be a set containing: {'SEARCH', 'BROWSE'}. If the input text does not contain any action tags, the output would be an empty set: set().
## FunctionDef extract_tag_content(text, tag)
## Function Documentation: `extract_tag_content`

### Overview
The function `extract_tag_content` is designed to extract the content enclosed within a specified HTML-like tag from a given text. It supports case-insensitive searches and handles multiline text efficiently.

### Function Signature
```python
def extract_tag_content(text: str, tag: str) -> str:
```

### Parameters
- **`text`** (`str`): The input text that contains the tag. This text can include any HTML-like elements or other content.
- **`tag`** (`str`): The name of the tag whose content is to be extracted. For example, if the tag is `<question>`, the value of `tag` would be `"question"`.

### Returns
- **`str`**: The content inside the specified tag. If the tag is not found, an empty string is returned. The extracted content will be stripped of leading and trailing whitespace.

### Functionality
The function constructs a regular expression pattern based on the provided `tag` and attempts to find the content within the tag in the `text`. The regular expression is case-insensitive and supports multiline content within the tag.

### Example Usage
```python
text = "<question>What is the capital of France?</question>"
tag = "question"
result = extract_tag_content(text, tag)
print(result)  # Output: "What is the capital of France?"
```

### Error Handling
If the specified tag is not present in the `text`, the function returns an empty string.

### Notes
- The function handles both uppercase and lowercase tag names due to the use of `re.IGNORECASE`.
- It is optimized to handle multiline content by using the `re.DOTALL` flag.
## FunctionDef extract_and_validate_json(model_response)
**extract_and_validate_json**: The function of extract_and_validate_json is to extract JSON content from a model response, whether it's wrapped in ```json``` fences or is just raw JSON text, and return the parsed object or None on failure.

**parameters**: The parameters of this Function.
· model_response: str - A string representing the model's response, which may contain JSON data that needs to be extracted and validated.

**Code Description**: The extract_and_validate_json function is designed to handle the extraction and validation of JSON data from a given model response. The function begins by attempting to identify and remove any Markdown-style fences that may wrap the JSON content. This is achieved using a regular expression pattern that matches the fences and captures the content within them. If the response does not contain such fences, the entire response is treated as the payload.

Once the potential JSON content is isolated, the function attempts to parse it using the json.loads method. If this parsing is successful, the parsed JSON object is returned. However, if a json.JSONDecodeError occurs, indicating that the content is not valid JSON, the function proceeds to clean the payload by removing any stray backticks and attempts to parse it again.

If the second parsing attempt fails, the function logs an error message using the print_exception method from the RichPrinter class, which provides detailed feedback about the error encountered, including the original model response. In this case, the function returns None, indicating that the extraction and validation process was unsuccessful.

The extract_and_validate_json function is called within various parts of the project, notably in the query_update and generate_seed functions of the ReverseUpgradeWorkflow class. In these contexts, it plays a crucial role in ensuring that the responses from the conversational agent are properly formatted as JSON before further processing. For instance, in the query_update function, it is used to extract updated question and evidence data from the model's response, which is essential for refining the QAItem being updated. Similarly, in the generate_seed function, it validates the JSON response that contains the seed question and answer, ensuring that the workflow can proceed with valid data.

**Note**: It is important to ensure that the model_response parameter is well-formed and contains valid JSON data. The function's reliance on the successful execution of the json.loads method means that any issues with the input format can lead to failures in the extraction process.

**Output Example**: A possible return value from the extract_and_validate_json function could be a parsed JSON object structured as follows:
```json
{
    "updated_question": "What is the capital of France?",
    "updated_evidence": ["Paris is the capital of France.", "It is located in northern central France."]
}
```
