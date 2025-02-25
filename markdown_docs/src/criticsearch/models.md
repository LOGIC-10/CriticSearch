## ClassDef HistoryItem
**HistoryItem**: The function of HistoryItem is to represent an individual entry in a conversation history.

**attributes**: The attributes of this Class.
· role: Literal["user", "assistant", "tool", "critic"]  
   This attribute defines the role of the entity in the conversation, such as "user", "assistant", "tool", or "critic". The role helps categorize the message within the conversation history.  
· content: Optional[str]  
   This attribute holds the actual content of the message. It is optional and may be `None` if not provided.  
· tool_calls: Optional[List[ChatCompletionMessageToolCall]]  
   This attribute stores a list of tool calls associated with the message. It is optional and only used when the message involves invoking tools.  
· tool_call_id: Optional[str]  
   This attribute holds a unique identifier for a tool call. It is optional and is used to track the specific tool call in case the message involves a tool.  
· name: Optional[str]  
   This attribute is used to store the name associated with the history item. It is optional and can be used to provide additional context about the message.

**Code Description**:  
The `HistoryItem` class is a data model that encapsulates a single entry within a conversation. It has a `role` attribute that defines who or what is contributing to the conversation, such as the user, assistant, tool, or critic. The `content` attribute contains the message's text, and it can be optional if no message content is provided. The `tool_calls` attribute, also optional, is used when a message involves calling a tool or a function, storing details about the tool calls made. Similarly, the `tool_call_id` serves as a unique identifier for each tool call, providing a way to trace or reference specific tool interactions. Finally, the `name` attribute can store a custom name for the entry, providing further context if required.

This class plays a vital role in managing conversation history, particularly in the context of applications where various entities interact through a series of messages. It integrates directly with the `ConversationManager` class, which manages the overall conversation history and tools used within it. Specifically, the `HistoryItem` class is used when appending new entries to the conversation history, either through regular messages or tool calls, ensuring that each entry is well-defined with relevant context (such as role, content, tool calls, etc.).

In the `ConversationManager` class, the `HistoryItem` is instantiated and appended to the `history` attribute whenever a new message is added to the conversation. For instance, the `append_to_history` method in `ConversationManager` creates a new `HistoryItem` with the given role and content, and then adds it to the history list. The `serialize_history` method, which handles the serialization of the conversation history, processes these `HistoryItem` instances to ensure that the history is accurately saved, potentially excluding any `None` values during serialization.

Furthermore, in specific cases where tool calls are involved, the `HistoryItem` can hold a list of `tool_calls` and a `tool_call_id`, providing a way to capture the specific details of any tools or functions invoked during the conversation.

**Note**:  
- The `content` attribute can be omitted for certain roles, such as "tool" or "critic", where the primary focus is on the interaction rather than the message content.  
- The use of `tool_calls` and `tool_call_id` is essential when the conversation involves automated tools or functions, ensuring that these interactions are tracked and referenced correctly.  
- The optional nature of many attributes (like `content`, `tool_calls`, `tool_call_id`, and `name`) allows for flexibility, enabling this class to accommodate various types of messages and interactions in a conversation history.
## ClassDef ConversationManager
**ConversationManager**: The function of ConversationManager is to manage and maintain the conversation history, including the ability to serialize this history, append new messages, and handle tool calls within the conversation.

**attributes**: The attributes of this Class.
· history: List[HistoryItem]  
   This attribute stores the conversation history as a list of HistoryItem instances, which represent individual entries in the conversation.

· max_history_length: int  
   This attribute defines the maximum number of entries to retain in the conversation history, limiting the size of the history to the most recent entries.

· available_tools: List  
   This attribute holds a list of tools that can be utilized during the conversation, allowing for integration of various functionalities.

· save_path: Path  
   This attribute specifies the file path where the conversation history will be saved in JSON Lines format.

· delete_on_init: bool  
   This attribute is a flag that indicates whether to delete the existing conversation history file upon initialization of the ConversationManager.

**Code Description**: The ConversationManager class is designed to facilitate the management of conversation history in applications that involve interactions between users and automated systems. It extends from BaseModel, allowing it to leverage data modeling capabilities. Upon initialization, the class checks if the specified save_path exists and deletes it if the delete_on_init flag is set to True. This ensures that any previous conversation history is cleared when a new instance is created.

The class provides methods to append messages to the history, including the append_to_history method, which allows adding new entries with specified roles (user, assistant, tool, or critic) and optional content. It also includes specialized methods for handling tool calls, such as append_tool_call_to_history and append_tool_call_result_to_history, which ensure that interactions with tools are accurately recorded in the history.

Serialization of the conversation history is handled through the serialize_history method, which prepares the history for saving by excluding any None values and limiting the output to the most recent entries based on max_history_length. Additionally, the custom_serialize method allows for context-specific serialization, particularly for formats like ShareGPT, transforming the history into a structured format suitable for sharing.

The write method is responsible for saving the conversation history to the specified file, handling both the creation of the file and the appending of new data to existing content. The _auto_save method ensures that the most recent entry in the history is automatically saved after each update.

The ConversationManager is utilized within the BaseAgent class, where it serves as a central component for managing conversation interactions. The BaseAgent class creates an instance of ConversationManager, allowing it to append messages and tool calls to the history as part of its operations. This integration ensures that all interactions, whether user prompts or tool responses, are systematically recorded, providing a comprehensive log of the conversation flow.

**Note**: It is important to ensure that the max_history_length is set appropriately to avoid excessive memory usage, especially in long-running applications. The delete_on_init flag should be used with caution, as it will permanently remove any existing conversation history upon initialization.

**Output Example**: A possible appearance of the code's return value when serializing the conversation history might look like this:
```json
{
  "conversations": [
    {"from": "human", "value": "Hello, how can I help you?"},
    {"from": "function_call", "value": "{\"name\": \"search\", \"arguments\": {\"query\": \"latest news\"}}"},
    {"from": "observation", "value": "{\"result\": \"Here are the latest news articles...\"}"}
  ],
  "tools": "[{\"name\": \"search\", \"description\": \"Search for information\"}]"
}
```
### FunctionDef __init__(self)
**__init__**: The function of __init__ is to initialize the object and manage file deletion if certain conditions are met.

**parameters**: 
· data: This parameter is passed as keyword arguments (**kwargs**) to initialize the base class.

**Code Description**: 
The `__init__` function in this case is a constructor that serves to initialize an object. It first calls the constructor of the superclass using `super().__init__(**data)` to ensure that any initialization defined in the parent class is executed. The keyword arguments passed to this constructor are forwarded to the parent class.

The function then checks the condition `if self.delete_on_init and self.save_path.exists()`. If the `delete_on_init` flag is set to `True` and a file at the path specified by `self.save_path` exists, the function attempts to delete the file using `self.save_path.unlink()`. If the file is successfully deleted, a log message is created with the information that the file was deleted. If the deletion operation fails (e.g., due to insufficient permissions or other issues), the function catches the exception and logs an error message containing the exception details.

After attempting the deletion, the function sets `self.delete_on_init = False` to ensure that no further deletion attempts are made in subsequent invocations of the object. This is done to prevent repeated deletions of the same file unless explicitly required elsewhere in the class.

**Note**: 
- The method assumes that `self.save_path` is a valid file path object that supports `.exists()` and `.unlink()` methods.
- It is important that the `delete_on_init` flag is properly managed to avoid unintended file deletion during object initialization.
- The use of `logger` for logging information and errors is crucial for debugging and understanding the state of the file deletion process.
***
### FunctionDef serialize_history(self, history)
**serialize_history**: The function of serialize_history is to convert a list of conversation history items into a serialized format, excluding any attributes that are set to None.

**parameters**: The parameters of this Function.
· history: List[HistoryItem]  
   This parameter represents a list of `HistoryItem` objects that encapsulate individual entries in a conversation history.

**Code Description**: The `serialize_history` method is designed to process a list of `HistoryItem` instances, which represent entries in a conversation. The method takes a single parameter, `history`, which is expected to be a list of `HistoryItem` objects. The function first initializes an empty list called `serialized_history` to hold the serialized representations of the history items.

The method then iterates over the last `max_history_length` number of items from the `history` list. This is achieved by slicing the list with `history[-self.max_history_length :]`, which ensures that only the most recent entries are considered for serialization. For each `HistoryItem` in this sliced list, the method calls the `model_dump` method on the item, passing `exclude_none=True` as an argument. This call to `model_dump` is responsible for converting the `HistoryItem` into a dictionary format while omitting any attributes that have a value of None.

Finally, the method returns the `serialized_history` list, which contains the serialized representations of the selected `HistoryItem` instances. This serialized data can be useful for saving conversation history in a structured format, such as for storage in a database or for transmission over a network.

The `serialize_history` method is closely related to the `HistoryItem` class, which defines the structure of each entry in the conversation history. By utilizing the `model_dump` method from the `HistoryItem`, this function ensures that the serialization process respects the attributes defined in the `HistoryItem` class, providing a consistent and accurate representation of the conversation history.

**Note**: It is important to ensure that the `max_history_length` attribute is defined within the class that contains the `serialize_history` method, as it dictates how many of the most recent history items will be serialized. The method is particularly useful in scenarios where only a limited portion of the conversation history is needed, such as when displaying recent interactions to a user or when preparing data for logging purposes.

**Output Example**: A possible appearance of the code's return value could be as follows:
```json
[
    {
        "role": "user",
        "content": "What is the weather like today?",
        "tool_calls": null,
        "tool_call_id": null,
        "name": null
    },
    {
        "role": "assistant",
        "content": "The weather is sunny with a high of 75°F.",
        "tool_calls": null,
        "tool_call_id": null,
        "name": null
    }
]
```
***
### FunctionDef custom_serialize(self, handler, info)
**custom_serialize**: The function of custom_serialize is to apply custom serialization logic to handle different contexts, particularly focusing on transforming the history into a ShareGPT format when specified.

**parameters**:
· handler: A SerializerFunctionWrapHandler responsible for performing default serialization of the object.
· info: A SerializationInfo object containing the context information, which can determine whether the ShareGPT format should be applied.

**Code Description**:  
The `custom_serialize` function begins by invoking the `handler` to perform default serialization on the object. This results in the `result` variable, which contains the serialized data, including the `history` attribute.

If the `info` parameter contains a context with a key "sharegpt", the function processes the history attribute further to format it for the ShareGPT use case. The logic involves iterating over each item in the `history` and remapping the roles using a predefined `role_mapping` dictionary. The roles are mapped from:
- `"user"` to `"human"`
- `"assistant"` to `"function_call"`
- `"tool"` to `"observation"`
- `"critic"` to `"critic"`

For each item, the corresponding value (either content or tool call data) is extracted. If the role is `"function_call"`, the function checks if tool calls are associated with the item and formats them as JSON, including the function name and its arguments. If no tool calls are present, the value is directly assigned with the content associated with the "gpt" role.

For `"observation"` roles, the content is serialized as a JSON string.

After processing all items in the history, the `conversations` list is populated with the formatted role-value pairs. Finally, the `result` object is updated to include the conversations and a serialized version of the `available_tools` attribute. This final output is then returned.

**Note**:  
- The `result["history"]` is assumed to be a list that contains historical interactions with objects that have `role` and `content` attributes.
- The handling of tool calls in the `"function_call"` role relies on the presence of a `tool_calls` attribute, which is expected to be a list of tool call objects.
- The format of the final output is specifically structured to accommodate ShareGPT's data format, which includes the key `"conversations"` and `"tools"`.

**Output Example**:  
Here is a mock-up of what the final output might look like when the `sharegpt` context is provided:

```json
{
  "conversations": [
    {
      "from": "human",
      "value": "Hello, how are you?"
    },
    {
      "from": "gpt",
      "value": "I'm doing well, thank you for asking!"
    },
    {
      "from": "function_call",
      "value": "{\"name\": \"weatherApi.getForecast\", \"arguments\": {\"location\": \"New York\"}}"
    },
    {
      "from": "observation",
      "value": "{\"temperature\": 72, \"condition\": \"Sunny\"}"
    }
  ],
  "tools": "{\"weatherApi\": {\"name\": \"weatherApi\", \"description\": \"Provides weather data\"}}"
}
```
***
### FunctionDef write(self, data, path)
**write**: The function of write is to append data to a JSON file, creating the necessary directories and handling potential issues with existing file data.

**parameters**: The parameters of this Function.
· data: dict - A dictionary containing the data to be written to the file.
· path: Path | str - The path (as a string or Path object) to the file where the data will be saved.

**Code Description**: The `write` function is responsible for managing the process of appending data to a specified JSON file. The function first ensures that the provided file path is a `Path` object, converting it from a string if necessary. It then verifies that the parent directories of the file exist, creating them if needed. If the file already exists, it attempts to read the existing data and ensures that it is a list (or initializes it as an empty list if the data is invalid or absent). The new data is then appended to this list, and the updated list is written back to the file in a JSON format, ensuring that the data is properly formatted (with indentation for readability).

The function handles potential errors that might occur during these operations, such as issues with file access or invalid data formats. In such cases, it logs the error message and raises the exception.

From a project perspective, the `write` function is utilized by other parts of the code to persist conversation history or similar data. For instance, it is called by the `_auto_save` method in the `ConversationManager` class, where it is used to save the most recent conversation history to a file, if the `save_path` attribute is set. Additionally, the `write` function is called in the `run_tasks` function, which processes a list of tasks and logs conversation data after each task is completed.

**Note**: When using this function, ensure that the path provided is correct, and be aware that it appends data to the file. This means that the file will grow in size over time as more data is added. Also, if the file contains corrupt or non-JSON data, the function will start with an empty list, potentially overwriting previous content.
***
### FunctionDef _auto_save(self)
**_auto_save**: The function of _auto_save is to automatically save the most recent entry in the conversation history to a specified file path, provided the save path is set.

**parameters**:  
- None

**Code Description**: The `_auto_save` method is a function within the `ConversationManager` class that is responsible for saving the most recent conversation history to a file, specifically the last entry in the `history` list. The method checks whether the `save_path` attribute is defined, and if it is, it uses the `write` method to persist the most recent entry in the conversation history. This entry is accessed using `self.history[-1]`, which fetches the last item in the `history` list, and then the `model_dump(exclude_none=True)` method is invoked on this entry to prepare it for saving. This method ensures that no `None` values are included in the saved data. The resulting data is then passed to the `write` method, which handles the task of appending this data to a file at the location specified by the `save_path`.

The `_auto_save` function is called automatically whenever a new message is added to the conversation history. Specifically, it is invoked by the `append_to_history` method, which adds new conversation entries to the `history` list. Once a new message is appended to the history, `_auto_save` is triggered to ensure that the updated history is saved immediately. This process facilitates the continuous preservation of the conversation data without requiring manual intervention from the user.

The `write` method, which is invoked by `_auto_save`, is responsible for appending data to a JSON file. It manages the creation of necessary directories, reads any existing data from the file, and ensures that the data is in the correct format before appending new content. This integration ensures that the conversation history is consistently updated and saved to disk.

**Note**: It is important to ensure that the `save_path` attribute is set correctly in order for the `_auto_save` function to work as expected. If the `save_path` is not provided or is invalid, no data will be saved. Additionally, the data being saved is the most recent entry in the `history` list, meaning only the latest message or event is preserved during each save operation.
***
### FunctionDef append_to_history(self, role, content)
### Function: `append_to_history`

**Purpose**:  
The `append_to_history` function is designed to add a new message to the conversation history in a `ConversationManager` instance.

**Parameters**:
- `role` (Literal["user", "assistant", "tool", "critic"]):  
  Specifies the role of the entity contributing to the conversation. The value can be one of the following:
  - `"user"`: Represents the user initiating the message.
  - `"assistant"`: Represents the assistant responding to the user.
  - `"tool"`: Represents an automated tool interacting within the conversation.
  - `"critic"`: Represents a critic providing feedback or evaluation.

- `content` (Optional[str]):  
  The actual content of the message. This is an optional parameter and can be set to `None` if no content is provided.

- `**kwargs`:  
  Additional optional keyword arguments that can be passed to the `HistoryItem` constructor. These arguments can be used for providing extra context, such as tool calls or identifiers.

**Functionality**:  
This method creates a new entry in the conversation history by instantiating a `HistoryItem` object with the provided `role`, `content`, and any additional keyword arguments. The newly created `HistoryItem` is appended to the `history` attribute, which is a list that stores the conversation history. After adding the new history item, the method triggers the `_auto_save` function to automatically save the updated conversation history.

**Usage**:  
This function is used to maintain and update the flow of a conversation by systematically adding new messages from different participants (user, assistant, tool, or critic) and ensuring that the history is saved for future reference. It plays a crucial role in tracking the progression of conversations over time.

**Example**:  
```python
conversation_manager.append_to_history(role="user", content="Hello, how can I assist you today?")
```

In this example, a new message from the user is added to the conversation history. The content of the message is "Hello, how can I assist you today?" and the role is set as `"user"`.

**Related Methods**:  
- `_auto_save`: Automatically saves the most recent conversation entry to a file after the message is added to history.
***
### FunctionDef append_tool_call_to_history(self, tool_calls, content)
**append_tool_call_to_history**: The function of append_tool_call_to_history is to add a tool call entry to the conversation history.

**parameters**: The parameters of this Function.
· tool_calls: List[ChatCompletionMessageToolCall] - A list of tool call entries that are to be added to the conversation history.
· content: Optional[str] - An optional string that represents additional content related to the tool calls. If not provided, it defaults to None.

**Code Description**: The append_tool_call_to_history function is a method within the ConversationManager class that is responsible for appending tool call entries to the conversation history. It takes two parameters: a list of tool calls and an optional content string. The primary purpose of this function is to maintain a record of interactions that involve automated tools within the conversation flow.

When invoked, the function calls another method, append_to_history, passing along the role of "assistant", the list of tool calls, and any additional content. The append_to_history method is responsible for creating a new entry in the conversation history, which is stored as a list of HistoryItem objects. This ensures that every interaction involving tools is documented, allowing for a comprehensive view of the conversation's progression.

The append_tool_call_to_history function is called within the search_and_browse method of the BaseAgent class. In this context, it is used to log the tool calls generated during a search operation. If the search_with_tool_response contains tool calls, the function is invoked to append these calls to the conversation history. This is crucial for tracking the actions taken by the assistant and the tools it interacts with, ensuring that the conversation history remains accurate and up-to-date.

In summary, append_tool_call_to_history plays a vital role in maintaining the integrity of the conversation history by systematically recording tool interactions, which can be referenced later for analysis or debugging.

**Note**: It is important to ensure that the tool_calls parameter is always provided as a list of ChatCompletionMessageToolCall objects to avoid errors during the history appending process. Additionally, the content parameter is optional and can be omitted if there is no additional information to record.
***
### FunctionDef append_tool_call_result_to_history(self, tool_call_id, name, content)
**append_tool_call_result_to_history**: The function of `append_tool_call_result_to_history` is to add the result of a tool call to the conversation history.

**parameters**: The parameters of this function are:
- `tool_call_id`: A string representing the unique identifier of the tool call.
- `name`: A string representing the name of the tool involved in the call.
- `content`: A string representing the result or content generated from the tool call.

**Code Description**: 
The `append_tool_call_result_to_history` function is designed to add the result of a tool call to the conversation history in a structured manner. This is achieved by calling the `append_to_history` method, which is responsible for adding an entry to the conversation history. The `role` parameter in `append_to_history` is set to `"tool"`, signifying that the message is coming from an automated tool. Along with this, the `tool_call_id`, `name`, and `content` are passed as keyword arguments to ensure that the specific details of the tool call are included in the history entry.

This function is called within the `search_and_browse` method of the `BaseAgent` class, which handles the interaction between the agent and external tools. Specifically, after making a tool call to search or scrape data, the results are passed to `append_tool_call_result_to_history` to be logged into the conversation history. This is crucial for maintaining a structured log of tool activities in the ongoing conversation.

When tool calls occur during the search and web scraping processes, `append_tool_call_result_to_history` ensures that the relevant tool call results are captured and saved in the conversation history. This allows for easy tracking of the results generated by tools like search aggregators and content scrapers.

In summary, this function is used to log the results of tool calls in the conversation history, providing a complete and organized record of the interactions involving automated tools.

**Note**: The content parameter passed to this function should contain the result of the tool's operation (such as search results or web scraping data) and should be a string that accurately reflects the output generated by the tool.
***
### FunctionDef clear_history(self)
**clear_history**: The function of clear_history is to remove all entries from the conversation history.

**parameters**: The clear_history function does not take any parameters.

**Code Description**: The clear_history function is a method that belongs to a class, presumably related to managing conversations. When invoked, this method performs a single action: it clears the entire conversation history stored in the object's history attribute. The history attribute is expected to be a data structure that supports the clear operation, such as a list or a similar collection. By calling self.history.clear(), the method effectively empties this collection, ensuring that no previous conversation data remains accessible. This functionality is particularly useful in scenarios where a fresh start is required, such as resetting a chat interface or preparing for a new session without any prior context.

**Note**: It is important to be aware that once the clear_history method is executed, all conversation data will be permanently deleted and cannot be recovered. Therefore, it is advisable to use this method with caution, especially in applications where conversation history may be needed for reference or analysis.
***
