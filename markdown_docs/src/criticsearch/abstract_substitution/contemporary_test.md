## FunctionDef reorder_constrained_format(data)
**reorder_constrained_format**: The function of reorder_constrained_format is to rearrange the fields of each record in the input data such that the "constrained_format" field appears immediately after the "GroundTruth" field.

**parameters**: The parameters of this Function.
· data: A dictionary where each key is a unique identifier and each value is another dictionary representing a record containing various fields including "GroundTruth" and "constrained_format".

**Code Description**: The reorder_constrained_format function takes a dictionary called data as input. This dictionary is expected to contain multiple entries, each identified by a unique key. Each entry is itself a dictionary that may include fields such as "GroundTruth" and "constrained_format", along with potentially other fields.

The function initializes an empty dictionary called new_data to store the reordered entries. It then iterates through each key-value pair in the input data. For each entry, it retrieves the value associated with the "GroundTruth" key and the value associated with the "constrained_format" key. 

Next, it constructs a new dictionary called others that contains all other fields in the entry, excluding "GroundTruth" and "constrained_format". This is achieved using a dictionary comprehension that filters out these two keys.

The function then creates a new dictionary called reordered, starting with the "GroundTruth" field. If the "constrained_format" field is not None, it adds this field to the reordered dictionary immediately after "GroundTruth". Finally, it updates the reordered dictionary with any remaining fields stored in others.

The newly constructed entry is then added to the new_data dictionary using the original key. Once all entries have been processed, the function returns the new_data dictionary, which contains all the original records but with the specified fields reordered.

**Note**: It is important to ensure that the input data structure adheres to the expected format, with each entry containing the necessary fields. If an entry does not contain "GroundTruth" or "constrained_format", the function will still process it, but the output will reflect the absence of these fields accordingly.

**Output Example**: 
Given an input like:
{
    "record1": {
        "GroundTruth": "True",
        "constrained_format": "Format1",
        "other_field": "Value1"
    },
    "record2": {
        "GroundTruth": "False",
        "other_field": "Value2"
    }
}

The output of the function would be:
{
    "record1": {
        "GroundTruth": "True",
        "constrained_format": "Format1",
        "other_field": "Value1"
    },
    "record2": {
        "GroundTruth": "False",
        "other_field": "Value2"
    }
} 

In this example, the "constrained_format" field appears after "GroundTruth" in the first record, while the second record does not include "constrained_format" but retains the order of the other fields.
## FunctionDef find_all_wrong_items(data)
**find_all_wrong_items**: The function of find_all_wrong_items is to return a mapping of entries (question -> entry) where all models have answered incorrectly.

**parameters**:
- data: A dictionary where the keys are questions (strings) and the values are entries (dictionaries). Each entry contains information about the question, including responses from multiple models, with fields like "GroundTruth" and "constrained_format" excluded for the check.

**Code Description**:  
The `find_all_wrong_items` function processes a given dataset `data`, which consists of multiple question-answer entries. For each question, it examines the answers provided by various models. The function filters out the fields labeled "GroundTruth" and "constrained_format" from the analysis and checks if all models have answered incorrectly. A model's answer is considered incorrect if the value of its "is_correct" field is set to `False`.

The function performs the following steps:
1. Initializes an empty dictionary `wrong_items` to store the entries where all models answered incorrectly.
2. Iterates through each question (`q`) and its corresponding entry in the `data`.
3. For each entry, it filters out the fields "GroundTruth" and "constrained_format" to gather the model responses.
4. It checks if all the model responses contain the key "is_correct" set to `False`. If this condition is met, it considers the entire entry as wrong and adds it to the `wrong_items` dictionary.
5. Finally, it returns the `wrong_items` dictionary, which maps questions to entries where all models answered incorrectly.

**Note**:  
- The function assumes that each model's response is a dictionary, and the "is_correct" field within each model's response is a boolean that indicates whether the answer is correct or not.
- The "GroundTruth" and "constrained_format" fields are excluded from the analysis; only other model responses are considered.
- The function will not include any questions in the output where at least one model answered correctly (i.e., if any model has "is_correct" set to `True`).

**Output Example**:  
An example output could look like this:

```python
{
    "question_1": {
        "model_1": {"is_correct": False, "answer": "incorrect_answer"},
        "model_2": {"is_correct": False, "answer": "incorrect_answer"},
        "model_3": {"is_correct": False, "answer": "incorrect_answer"}
    },
    "question_2": {
        "model_1": {"is_correct": False, "answer": "incorrect_answer"},
        "model_2": {"is_correct": False, "answer": "incorrect_answer"},
        "model_3": {"is_correct": False, "answer": "incorrect_answer"}
    }
}
```  
In this example, both `question_1` and `question_2` are mapped in the output because all models for these questions have answered incorrectly.
