## ClassDef ReportVerifier
# ReportVerifier Class Documentation

## Overview

The `ReportVerifier` class is designed for performing factual quality assurance (QA) verification on extracted facts. It utilizes a specified agent to interact with a context and verifies the factual accuracy of the extracted data through a series of questions and answers. The class integrates the use of a scoring mechanism, specifically the Rouge metric, to evaluate the factual correctness of responses.

## Methods

### `__init__(self, agent)`

The constructor initializes the `ReportVerifier` class. It requires an agent to interact with during the verification process and sets up a Rouge scorer for evaluating the factual correctness of responses.

**Parameters:**
- `agent`: An object that facilitates communication with the QA system, which is used to verify the correctness of the extracted facts.

### `verify_section(self, context: str, extracted_facts: List[Dict]) -> float`

This method performs the factual QA verification process for a given section of the report. It processes each fact, verifies it by generating responses, and calculates a score to indicate the overall correctness of the section.

**Parameters:**
- `context`: A string containing the context or background information required to verify the facts.
- `extracted_facts`: A list of dictionaries, each containing a fact to verify, including the question, format, and expected answer.

**Returns:**
- A floating-point value representing the overall score of the verification process, indicating the correctness of the section.

**Process:**
1. **Initialization**: It starts by printing the total number of questions to verify.
2. **Verification**: For each extracted fact, a helper function (`verify_single_question`) is used to:
   - Prepare the QA data, including the context, user question, and the fact format.
   - Communicate with the agent using the `chat_with_template` method, passing the QA data and the template file `factQA_verifier.txt`.
   - Check the agent’s response against the expected answer.
3. **Parallel Execution**: The verification of each question is handled concurrently using a thread pool with a maximum of 20 workers. This improves performance when verifying large numbers of facts.
4. **Result**: The method returns a floating-point score, reflecting the overall verification results, after comparing each response against the correct answers.

### `verify_single_question(self, fact) -> float`

This method is a helper function used within `verify_section` to verify a single extracted fact. It prepares the QA data, queries the agent, and compares the response to the expected answer.

**Parameters:**
- `fact`: A dictionary containing a single extracted fact, which includes the question, format, and expected answer.

**Returns:**
- A floating-point score reflecting the accuracy of the response for the given fact.

### `_check_answer(self, response: str, correct_answer: str) -> float`

This private method compares the response from the agent with the correct answer and calculates a score based on the accuracy of the match.

**Parameters:**
- `response`: The response from the agent after processing the fact.
- `correct_answer`: The expected correct answer for the fact.

**Returns:**
- A floating-point score representing the accuracy of the response, calculated using the Rouge metric.

## Dependencies

- `rouge_scorer.RougeScorer`: A Rouge scorer is used to evaluate the factual correctness of the responses based on the Rouge-L score.
- `ThreadPoolExecutor`: Used to run multiple fact verification tasks concurrently for improved performance.

## Usage Example

```python
# Instantiate the agent (not shown in this example)
agent = SomeAgent()

# Instantiate the ReportVerifier with the agent
report_verifier = ReportVerifier(agent)

# Example context and extracted facts
context = "The capital of France is Paris."
extracted_facts = [
    {"question": "What is the capital of France?", "format": "text", "answer": "Paris"},
    {"question": "Is Paris the capital of France?", "format": "text", "answer": "Yes"}
]

# Verify the section of extracted facts
score = report_verifier.verify_section(context, extracted_facts)

# Print the score
print(f"Verification Score: {score}")
```

In this example, the `verify_section` method processes each question in the `extracted_facts` list and compares the agent's responses to the expected answers. It then calculates a final score for the section's factual accuracy.

## Conclusion

The `ReportVerifier` class provides a structured approach to verifying the factual correctness of extracted data. It integrates a powerful scoring mechanism, multi-threaded execution, and interaction with a provided agent to efficiently perform QA verification on a section of facts.
### FunctionDef __init__(self, agent)
**__init__**: The function of __init__ is to initialize the ReportVerifier object with a given agent and configure a RougeScorer instance for evaluating text similarity.

**parameters**: The parameters of this Function.
- agent: An object that is assigned to the `agent` attribute of the ReportVerifier class.

**Code Description**: 
The `__init__` function is the constructor method for the `ReportVerifier` class. When an instance of `ReportVerifier` is created, the method takes in a parameter `agent` and assigns it to the instance's `agent` attribute. This allows the `ReportVerifier` object to interact with or use the agent throughout its lifecycle.

In addition to initializing the `agent`, the method also initializes a `rouge_scorer.RougeScorer` object. The `RougeScorer` is configured to evaluate the Rouge-L metric, which is used to assess the quality of text summaries by comparing them with reference texts. The `use_stemmer=True` argument is passed to the `RougeScorer` to ensure that stemming is applied during the comparison process. Stemming reduces words to their base or root form, enhancing the robustness of the text comparison by ignoring minor variations in word forms.

**Note**: The `agent` parameter must be an object that is compatible with the functionality intended in the `ReportVerifier` class. The `RougeScorer` instance will always be configured with the Rouge-L metric and stemming enabled, which is crucial for ensuring consistent evaluation results when performing text similarity comparisons.
***
### FunctionDef verify_section(self, context, extracted_facts)
**verify_section**: The function of verify_section is to perform factual verification of a series of questions based on a given context and extracted facts, returning an accuracy score.

**parameters**: The parameters of this Function.
· context: str - A string representing the context in which the questions are to be verified.
· extracted_facts: List[Dict] - A list of dictionaries, where each dictionary contains a question, its expected answer, and the format of the question.

**Code Description**: The verify_section method is designed to initiate the verification process for a set of factual questions. It begins by printing a message indicating the start of the verification process and the total number of questions to be verified. The method defines an inner function, verify_single_question, which takes a single fact as input. This inner function constructs a dictionary containing the context, user question, and its format, and then prints the details of the question being verified.

The method utilizes an agent's chat_with_template function to interact with a predefined template for factual verification. The response from this interaction is then checked against the expected answer using the _check_answer method. The results of these checks are collected in a list.

To optimize the verification process, the method employs a ThreadPoolExecutor to handle multiple questions concurrently, allowing for up to 20 workers. Each question is submitted to the executor, and the results are gathered as they are completed. The tqdm library is used to provide a progress bar, enhancing user experience by visually indicating the verification progress.

Once all questions have been verified, the method calls the _calculate_score function, passing the results and the total number of questions to compute an overall accuracy score. This score is then returned as the output of the verify_section method.

The verify_section method is called by the process_single_task function, which manages the execution of a single task. Within this function, after generating content for a section, the verify_section method is invoked to assess the factual accuracy of that content against the extracted facts. The accuracy score obtained from verify_section is then appended to the agent's training data, providing feedback on the quality of the generated content.

**Note**: It is crucial to ensure that the extracted_facts parameter is populated with accurate and relevant data to facilitate effective verification. The performance of the verification process may vary based on the complexity and clarity of the questions being assessed.

**Output Example**: Assuming the extracted_facts contain the following data:
```json
[
    {"question": "What is the capital of France?", "answer": "Paris", "format": "simple"},
    {"question": "What is the largest planet?", "answer": "Jupiter", "format": "simple"}
]
```
The output might look like:
```
Total questions to verify: 2
Verifying Question: What is the capital of France?
Format: simple
Verifying Question: What is the largest planet?
Format: simple
Accuracy Score: 95.0%
```
#### FunctionDef verify_single_question(fact)
**verify_single_question**: The function of verify_single_question is to verify a single question's answer by interacting with a model and comparing the model's response to the expected answer.

**parameters**: The parameters of this Function.
· fact: A dictionary containing the question, expected answer, and format of the question.

**Code Description**:  
The `verify_single_question` function is responsible for verifying a single question by interacting with a model, providing it with a question, its expected format, and checking the model’s response against the expected answer.

The function begins by creating a dictionary called `qa_data`, which contains the following keys:
- `"context"`: A context variable, though it is not provided within this specific function, likely defined elsewhere in the class.
- `"user_question"`: The question extracted from the `fact` dictionary passed into the function.
- `"constrained_format"`: The expected format of the answer, also taken from the `fact` dictionary.

Then, the function prints out the question and its format to the console for tracking and debugging purposes.

Following this, the function calls the `chat_with_template` method of the `agent` object. This method is responsible for generating a response from the model based on the provided template (`"factQA_verifier.txt"`) and the data contained in the `qa_data` dictionary. The method does not save conversation history, as indicated by `save_history=False`. The `chat_with_template` method processes the input and returns a model-generated response, which is then passed to the `_check_answer` method along with the expected answer from the `fact` dictionary.

The `_check_answer` function is designed to evaluate the model's answer against the expected answer, checking for an exact match or calculating a ROUGE-L score for partial matches. It returns a tuple containing:
- A boolean indicating whether the model’s answer is correct.
- A floating-point value representing the ROUGE-L score if there is a partial match.

Finally, `verify_single_question` returns the result from `_check_answer`, providing the verification outcome of the model’s response.

This function relies heavily on the `chat_with_template` and `_check_answer` methods, with the former generating the response and the latter evaluating it. 

**Note**:  
- The `verify_single_question` function assumes that the `fact` dictionary passed to it will contain the keys `"question"`, `"format"`, and `"answer"`. 
- It is essential that the template (`"factQA_verifier.txt"`) exists in the system and is correctly formatted for the model to generate an appropriate response. 
- This function does not save history by default (`save_history=False`), but this behavior can be changed if required by modifying the relevant parameter.

**Output Example**:  
An example of the return value could look like this:
```
(True, 0.0)
```
Or for a partial match:
```
(False, 75.56)
```
***
***
### FunctionDef _normalize_text(self, text)
**_normalize_text**: The function of _normalize_text is to standardize the input text by retaining only alphanumeric characters, converting the text to lowercase, and removing any spaces.

**parameters**: The parameters of this Function.
· text: The input string that needs to be standardized.

**Code Description**: 
The _normalize_text function is responsible for normalizing an input string by performing the following operations:
1. It removes any non-alphanumeric characters using a regular expression (`re.sub(r'[^a-zA-Z0-9]', '', text)`), which ensures that only letters (both uppercase and lowercase) and numbers remain in the string.
2. It converts the resulting string to lowercase using the `lower()` method, ensuring case uniformity.
3. It then returns the transformed string.

This function is primarily used within the context of answer verification. For example, the function is called by `_check_answer`, where it plays a key role in standardizing both the model's predicted answer and the ground truth answer. After extracting specific parts of the answers (using a regular expression to find content inside `\boxed{}`), `_normalize_text` is applied to both the model's and the ground truth answers before performing any further comparisons. This standardization ensures that the comparison is made in a consistent format, eliminating discrepancies due to case differences, spacing, or punctuation.

**Note**: 
- The function only retains alphanumeric characters, so punctuation and spaces are completely discarded. Ensure that the input text is appropriate for this kind of transformation.
- This function may be useful in scenarios where exact matches are required and formatting
***
### FunctionDef _check_answer(self, model_answer, ground_truth)
**_check_answer**: The function of _check_answer is to evaluate the model's answer against the expected answer, providing an exact match result or calculating a ROUGE-L score for partial matches.

**parameters**: The parameters of this Function.
· model_answer: A string representing the answer generated by the model.
· ground_truth: A string representing the correct or expected answer.

**Code Description**: 
The `_check_answer` function is designed to compare a model's answer (`model_answer`) with the expected correct answer (`ground_truth`). It begins by checking if the `model_answer` is `None`, in which case it immediately returns `False` (indicating no match) and a score of `0.0`.

To perform the comparison, the function first uses a regular expression to extract content enclosed in `\boxed{}` from both the `model_answer` and `ground_truth`. These are stored in the lists `model_boxed` and `ground_truth_boxed`, respectively. If both lists are non-empty, the function proceeds to normalize the answers.

The normalization step involves the `_normalize_text` method, which standardizes both the model’s and ground truth answers by removing non-alphanumeric characters, converting them to lowercase, and eliminating any spaces. This ensures that the comparison is made on a consistent, normalized version of the answers, free from case or formatting discrepancies.

After the answers are normalized, the function performs a comparison to check for an exact match. If the model's answer exactly matches the ground truth, it sets `is_correct` to `True` and the `rouge_score` remains at `0.0`. If the answers do not match, the function calculates a ROUGE-L score, which measures the similarity between the two answers, providing a score that indicates the level of partial match.

The function then prints detailed output, including whether the match was exact or partial, along with the original and normalized versions of both the expected answer and the model's answer. The print statements are useful for debugging or analyzing the performance of the model.

Finally, the function returns a tuple: `is_correct` (a boolean indicating whether the model's answer matches the expected answer) and `rouge_score` (a floating-point value representing the ROUGE-L score for partial matches).

The `_check_answer` function is called by the `verify_single_question` function, which is responsible for verifying individual questions by interacting with a model. The `verify_single_question` function gathers the question and its expected answer from a dictionary (`fact`) and passes them to the model. After the model generates an answer, `verify_single_question` calls `_check_answer` to compare the model's answer to the expected answer and return the results.

**Note**: 
- The function relies on the `_normalize_text` method for standardizing the answers. Ensure that the text passed to `_check_answer` contains content enclosed in `\boxed{}` to match the expected structure.
- If either the model's answer or the ground truth answer does not contain content within `\boxed{}`, the function will not proceed with the comparison and will return a score of `0.0`.
- This function is useful in scenarios where exact answer matching is required, and it also supports partial matches through the ROUGE-L score.

**Output Example**: 
An example of the return value could look like this:
```
(is_correct=True, rouge_score=0.0)
```
Or for a partial match:
```
(is_correct=False, rouge_score=75.56)
```
***
### FunctionDef _calculate_score(self, results, total)
**_calculate_score**: The function of _calculate_score is to compute a final accuracy score based on the results of a verification process.

**parameters**: The parameters of this Function.
· results: List - A list of tuples where each tuple contains a boolean indicating whether the answer was correct and the corresponding ROUGE-L score for partial matches.  
· total: int - An integer representing the total number of questions that were verified.

**Code Description**: The _calculate_score function is responsible for calculating a weighted accuracy score based on the verification results of a series of questions. It first counts the number of exact matches by summing up the boolean values from the results list, where a value of `True` indicates a correct answer. Next, it extracts the ROUGE-L scores for the answers that were not exact matches. The average ROUGE-L score is computed by dividing the total of these scores by the total number of questions, ensuring that if there are no ROUGE scores, it defaults to zero.

The final accuracy score is calculated as a weighted average, where 70% of the score is derived from the proportion of exact matches to the total number of questions, and 30% is derived from the average ROUGE-L score. This approach allows for a balanced evaluation of both exact correctness and partial correctness.

The function also includes logging statements that utilize the RichPrinter class to provide a structured output of the verification results. It prints a summary that includes the total number of questions, the number of exact matches, the average ROUGE-L score for partial matches, and the final weighted score. This output is formatted to enhance readability and clarity for users reviewing the verification results.

The _calculate_score function is called by the verify_section method, which is responsible for verifying a series of factual questions. After the verification process is completed, the results are passed to _calculate_score to obtain the overall accuracy score. This score is then returned to indicate the effectiveness of the verification process.

**Note**: It is important to ensure that the results list accurately reflects the verification outcomes, as the accuracy score is directly dependent on the correctness of the data provided. Proper handling of the total parameter is also crucial to avoid division errors.

**Output Example**: 
Assuming the results list contains the following data: `[(True, 0.9), (False, 0.7), (True, 0.85)]` and the total is 3, the output might look like:
```
Total Questions: 3
Exact Matches: 2/3 (66.67%)
Average ROUGE-L for Partial Matches: 70.00%
Final Weighted Score: 76.67%
```
***
