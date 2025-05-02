## FunctionDef flatten_outline(section, depth, path)
**flatten_outline**: The function of flatten_outline is to flatten a hierarchical outline structure into a list of sections with their respective depth and path information.

**parameters**: The parameters of this Function.
· parameter1: section - A dictionary representing a section of the outline, which may contain a title and potentially a list of child sections.
· parameter2: depth - An integer indicating the current depth level in the outline hierarchy. It defaults to 1.
· parameter3: path - A list that keeps track of the titles of the sections leading up to the current section. It defaults to None and is initialized to an empty list within the function.

**Code Description**: The flatten_outline function takes a section of an outline and recursively processes it to create a flat representation of the outline. The function begins by checking if the path parameter is None; if it is, it initializes it to an empty list. It then constructs a dictionary called current, which contains the current section's title appended to the path, the section itself, and its depth level. This current dictionary is added to a list called flat, which will hold all flattened sections.

If the section contains any children (i.e., sub-sections), the function iterates over each child and recursively calls flatten_outline, increasing the depth by 1 and updating the path to include the current section's title. The results from these recursive calls are then extended into the flat list. Finally, the function returns the flat list, which contains all sections in a flattened format, along with their respective paths and depth levels.

**Note**: It is important to ensure that the input section has a valid structure, including a title and an optional list of children, to avoid errors during execution. The function is designed to handle outlines of varying depths and complexities.

**Output Example**: 
Given an input section structured as follows:
{
    "title": "Main Section",
    "children": [
        {
            "title": "Subsection 1",
            "children": []
        },
        {
            "title": "Subsection 2",
            "children": [
                {
                    "title": "Sub-subsection 1",
                    "children": []
                }
            ]
        }
    ]
}

The output of flatten_outline would be:
[
    {"path": ["Main Section"], "section": {"title": "Main Section", "children": [...]}, "depth": 1},
    {"path": ["Main Section", "Subsection 1"], "section": {"title": "Subsection 1", "children": []}, "depth": 2},
    {"path": ["Main Section", "Subsection 2"], "section": {"title": "Subsection 2", "children": [...]}, "depth": 2},
    {"path": ["Main Section", "Subsection 2", "Sub-subsection 1"], "section": {"title": "Sub-subsection 1", "children": []}, "depth": 3}
]
## FunctionDef generate_content_for_section(agent, section, task)
**generate_content_for_section**: The function of generate_content_for_section is to generate detailed content for a specified section based on search results related to a given task.

**parameters**: The parameters of this Function.
· agent: An instance of BaseAgent that facilitates the search and content generation process.  
· section: A dictionary containing details about the section, specifically the title for which content needs to be generated.  
· task: A string representing the background topic or task that contextualizes the content generation.

**Code Description**: The generate_content_for_section function is designed to create content for a specific section by leveraging the capabilities of an intelligent agent (BaseAgent). The function begins by extracting the title from the provided section dictionary. It then constructs a search query that asks the agent to generate search queries related to the section title within the context of the specified task. This search query is passed to the agent's search_and_browse method, which performs a search and retrieves relevant web content.

Once the search results are obtained, the function formulates a prompt that instructs the agent to write one or several detailed paragraphs about the section title, incorporating data and facts from the search results. The prompt explicitly requests that the content be formatted in plain text without summary sentences and emphasizes the need for proper citation of sources using a specified format.

The agent's chat method is then called with the constructed prompt to generate the actual content. After the content is generated, the function utilizes the printer's rule and print methods to display a header indicating that content has been generated for the specified title, followed by the generated content itself.

This function is closely related to the BaseAgent class, particularly its search_and_browse and chat methods. The search_and_browse method is responsible for executing the search based on the generated query, while the chat method handles the interaction with the conversational model to produce the final content. The generate_content_for_section function serves as a higher-level orchestration function that combines these capabilities to fulfill the specific requirement of generating section content.

**Note**: It is important to ensure that the agent instance passed to the function is properly initialized and configured to perform searches and generate content effectively. The section dictionary should contain a valid title, and the task string should provide sufficient context for the content generation.

**Output Example**: A possible appearance of the code's return value when executing the function might look like this:
"Artificial Intelligence (AI) has significantly transformed various industries. In the context of healthcare, AI technologies are being utilized to enhance diagnostic accuracy and streamline patient care. For instance, machine learning algorithms can analyze medical images with remarkable precision, leading to earlier detection of diseases. <cite>https://www.example.com/ai-healthcare</cite>"
## FunctionDef reconstruct_markdown(outline, flat_contents)
**reconstruct_markdown**: The function of reconstruct_markdown is to generate a final Markdown text based on a flattened content structure and an original outline.

**parameters**: The parameters of this Function.
· outline: A dictionary representing the hierarchical structure of the document, which includes titles and potentially nested sections (children).
· flat_contents: A list of tuples, where each tuple contains a dictionary with a "path" key and the corresponding content string. The "path" key represents the unique path to the content in the outline.

**Code Description**: The reconstruct_markdown function constructs a Markdown representation of a document by combining an outline structure with corresponding content. It begins by creating a mapping of content using the complete path as a key to ensure uniqueness. The function defines a nested helper function that recursively processes each section of the outline. For each section, it generates a Markdown header based on the depth of the section in the hierarchy and appends any associated content if it exists in the content map. The function also handles nested sections by iterating through any children of the current section. The final Markdown text is built up and returned as a single string.

The process begins by initializing an empty string for the result. If the outline has a title, it adds it as the top-level header in the Markdown format. The function then iterates through the children of the outline, invoking the helper function for each child section, which constructs the Markdown recursively.

**Note**: It is important to ensure that the paths in flat_contents correspond accurately to the structure defined in the outline. Any discrepancies may result in missing content in the final Markdown output.

**Output Example**: 
Given an outline like:
{
    "title": "Document Title",
    "children": [
        {
            "title": "Section 1",
            "children": []
        },
        {
            "title": "Section 2",
            "children": [
                {
                    "title": "Subsection 2.1",
                    "children": []
                }
            ]
        }
    ]
}
And flat_contents like:
[
    ({"path": ["Document Title", "Section 1"]}, "Content for Section 1."),
    ({"path": ["Document Title", "Section 2", "Subsection 2.1"]}, "Content for Subsection 2.1.")
]
The output of reconstruct_markdown would be:
# Document Title

## Section 1

Content for Section 1.

## Section 2

### Subsection 2.1

Content for Subsection 2.1.
### FunctionDef helper(section, path)
**helper**: The function of helper is to recursively generate a Markdown representation of a structured document based on the provided section and its children.

**parameters**: The parameters of this Function.
· parameter1: section - A dictionary representing a section of the document, which includes a title and potentially child sections.
· parameter2: path - A list that keeps track of the current path of titles leading to the current section, defaulting to an empty list.

**Code Description**: The helper function constructs a Markdown string for a given section of a document. It begins by creating a new path that includes the title of the current section. This path is converted into a tuple, which serves as a key to look up content in a predefined `content_map`. The depth of the current section is determined by the length of the path, which is used to format the section title with the appropriate number of hash symbols for Markdown headers.

If the current section's path key exists in the `content_map`, the corresponding content is appended to the Markdown string. The function then checks if the section contains any child sections. If so, it iterates through each child and recursively calls itself, appending the resulting Markdown from each child to the current Markdown string. Finally, the complete Markdown string for the section and its children is returned.

**Note**: It is important to ensure that the `content_map` is defined and contains the necessary content for the sections being processed. The function assumes that the structure of the input section is consistent and that each section may have a "title" and optionally "children".

**Output Example**: An example output for a section with the title "Introduction" and a child section titled "Background" might look like this:

```
# Introduction

This is the content for the Introduction section.

## Background

This is the content for the Background section.
```
***
## FunctionDef create_document_structure(outline_json, flat_contents)
**create_document_structure**: The function of create_document_structure is to create a structured document based on an outline and associated content.

**parameters**: The parameters of this Function.
· outline_json: A JSON object representing the outline structure of the document, including titles and hierarchical relationships.
· flat_contents: A list of tuples, where each tuple contains an item (with a path) and its corresponding content as a string.

**Code Description**: The create_document_structure function constructs a document structure by utilizing the provided outline and content. It initializes a document dictionary with a title and a level, setting up a place for subsections. The function then creates a mapping of content to paths derived from the flat_contents parameter, allowing for easy retrieval of content based on the section paths.

The core of the function is the nested process_section function, which recursively processes each section of the outline. It constructs a section_data dictionary that includes the title, level, and paragraphs for each section. If content exists for a given path, it splits the content into paragraphs based on double newlines, ignoring any empty paragraphs. Each paragraph is processed to extract citations, which are stored alongside the paragraph text.

The function also handles child sections by recursively calling process_section for each child, appending the resulting data to the current section's subsections. Finally, the function iterates through the root sections of the outline, processing each one and appending it to the main document structure before returning the complete document.

**Note**: It is important to ensure that the outline_json is well-structured and that the flat_contents accurately corresponds to the paths defined in the outline. The function assumes that paragraphs are separated by double newlines and that citations can be extracted from the paragraphs.

**Output Example**: A possible appearance of the code's return value could be as follows:
{
    "document": {
        "title": "Sample Document Title",
        "level": 1,
        "subsections": [
            {
                "title": "Introduction",
                "level": 2,
                "paragraphs": [
                    {
                        "text": "This is the first paragraph of the introduction.",
                        "citations": ["Citation1", "Citation2"]
                    },
                    {
                        "text": "This is the second paragraph of the introduction.",
                        "citations": []
                    }
                ],
                "subsections": []
            },
            {
                "title": "Methodology",
                "level": 2,
                "paragraphs": [],
                "subsections": []
            }
        ]
    }
}
### FunctionDef process_section(section, depth, path)
**process_section**: The function of process_section is to recursively process a section of a document, extracting its title, paragraphs, and any nested subsections.

**parameters**: The parameters of this Function are as follows:
· section: A dictionary representing a section of the document, which includes a title and potentially child sections.
· depth: An integer indicating the current depth of the section in the document hierarchy, defaulting to 1.
· path: A list that tracks the path of titles leading to the current section, defaulting to an empty list.

**Code Description**: The process_section function begins by constructing the current path of titles by appending the title of the current section to the existing path. This path is then converted into a tuple, which serves as a key to access content from a predefined content_map. The function initializes a dictionary, section_data, to store the title, depth level, and an empty list for paragraphs.

If the current path key exists in the content_map, the function retrieves the associated content and splits it into paragraphs based on double newlines, assuming that paragraphs are separated by empty lines. Each paragraph is processed to extract citations using the extract_citations function, which identifies URLs enclosed within <cite> tags. Non-empty paragraphs are added to the section_data dictionary, along with their corresponding citations.

The function then checks if the current section has any child sections. If so, it initializes a list for subsections and recursively calls process_section for each child, incrementing the depth by one and passing the updated path. Each child's processed data is appended to the subsections list within section_data.

Finally, the function returns the constructed section_data dictionary, which encapsulates the processed information of the section, including its title, depth, paragraphs, and any nested subsections.

This function is integral to the overall structure of the document processing system, as it organizes sections and their content into a structured format. It relies on the extract_citations function to ensure that citations are accurately captured and associated with their respective paragraphs.

**Note**: It is essential that the content_map contains properly formatted entries corresponding to the section titles for the function to retrieve and process content effectively. If the section does not have associated content or if the structure of the input data is incorrect, the function may return incomplete or empty section data.

**Output Example**: An example of the function's return value could be:
{
    "title": "Introduction",
    "level": 1,
    "paragraphs": [
        {
            "text": "This is the first paragraph of the introduction.<cite>http://example.com/citation1</cite>",
            "citations": ["http://example.com/citation1"]
        },
        {
            "text": "This is the second paragraph of the introduction.",
            "citations": []
        }
    ],
    "subsections": [
        {
            "title": "Background",
            "level": 2,
            "paragraphs": [],
            "subsections": []
        }
    ]
}
***
## FunctionDef parse_markdown_to_structure(markdown_text)
**parse_markdown_to_structure**: The function of parse_markdown_to_structure is to parse markdown text and extract its document structure, including titles, subsections, and paragraphs.

**parameters**: The parameters of this Function are as follows:
· markdown_text: A string containing the markdown text to be parsed.

**Code Description**: The parse_markdown_to_structure function processes a given markdown text and organizes it into a structured format. It begins by splitting the input markdown text into individual lines. A dictionary named `document` is initialized to hold the overall structure, which includes a title, a level, and subsections. The function maintains a stack called `section_stack` to keep track of the current section being processed, allowing for the hierarchical organization of subsections based on their levels.

As the function iterates through each line of the markdown text, it checks for non-empty lines. If a line starts with a hash symbol (#), it indicates a title. The function calculates the level of the title by counting the number of leading hash symbols and extracts the title text. If there is any accumulated paragraph text before encountering a new title, it processes that text by extracting citations using the extract_citations function and appending it to the current section's paragraphs.

The function dynamically adjusts the current section based on the title level, ensuring that subsections are correctly nested within their parent sections. If a line is empty, it signifies a break between paragraphs, prompting the function to process any collected paragraph text.

At the end of the iteration, the function ensures that any remaining paragraph text is processed and added to the current section. Finally, the structured document is returned.

The parse_markdown_to_structure function relies on the extract_citations function to identify and extract URLs enclosed within `<citation>` tags from the paragraph text. This integration is essential for maintaining the integrity of citations throughout the document processing workflow, ensuring that all relevant citations are captured and associated with their respective paragraphs.

**Note**: It is important to ensure that the input markdown text is properly formatted, with titles indicated by hash symbols and paragraphs separated by empty lines, for the function to successfully parse and structure the document.

**Output Example**: A possible return value from the parse_markdown_to_structure function could be:
```python
{
    "document": {
        "title": "",
        "level": 1,
        "subsections": [
            {
                "title": "Introduction",
                "level": 1,
                "subsections": [],
                "paragraphs": [
                    {"text": "This is the introduction paragraph.", "citations": []}
                ]
            },
            {
                "title": "Methods",
                "level": 1,
                "subsections": [
                    {
                        "title": "Data Collection",
                        "level": 2,
                        "subsections": [],
                        "paragraphs": [
                            {"text": "Data was collected from various sources.", "citations": ["http://example.com/citation1"]}
                        ]
                    }
                ],
                "paragraphs": []
            }
        ]
    }
}
```
## FunctionDef _model_action_decision(agent, search_results, task, current_section)
**_model_action_decision**: The function of _model_action_decision is to determine the next action for an agent based on the provided search results, task, and current section.

**parameters**: The parameters of this Function.
· agent: An instance of BaseAgent that represents the intelligent agent making the decision.  
· search_results: A string containing the results of previous searches relevant to the task.  
· task: A string that describes the current task the agent is working on.  
· current_section: A string indicating the current section of the task or document being processed.

**Code Description**: The _model_action_decision function is designed to facilitate decision-making for an intelligent agent by leveraging a conversational model. The function begins by invoking the agent's chat_with_template method, which loads a predefined template ("model_action_decision.txt") and renders it with the provided search results, task, and current section. This interaction generates a decision from the model, which is expected to include both a thought and a set of actions.

Once the decision is obtained, the function extracts the thought and actions using the helper functions extract_thought_from_response and extract_actions. It performs validation checks to ensure that the decision and actions are valid; if either is missing, a ValueError is raised, prompting a retry of the decision-making process.

The function then evaluates the first action from the extracted actions. Depending on the action type—SEARCH, BROWSE, or START_WRITING—the function returns the corresponding thought, action, and any additional data required for that action. For example, if the action is SEARCH, it also extracts queries from the decision response. If the action is BROWSE, it extracts citations, and if the action is START_WRITING, it returns None for the data.

This function is called by the _action_router function, which orchestrates the overall decision-making process for the agent. The _action_router function utilizes the output of _model_action_decision to determine the next steps, such as executing a new search, browsing web content, or generating written content based on the agent's thought and actions.

**Note**: It is crucial to ensure that the template "model_action_decision.txt" exists and is correctly formatted, as the function relies on it to generate the decision. Additionally, the input parameters must be valid and properly structured to avoid exceptions during the decision-making process.

**Output Example**: A possible appearance of the code's return value when executing the function could look like this:
```python
("I think we should search for more information.", "SEARCH", ["query1", "query2"])
```
## FunctionDef _action_router(agent, search_results, task, current_section, iteration, agent_report, guide_line, detailed_web_results)
**_action_router**: The function of _action_router is to manage the decision-making process for an intelligent agent, guiding it through various actions such as searching, browsing, or writing based on the provided context and results.

**parameters**: The parameters of this Function.
· agent: An instance of BaseAgent that represents the intelligent agent making the decisions.  
· search_results: A string containing the results of previous searches relevant to the task.  
· task: A string that describes the current task the agent is working on.  
· current_section: A string indicating the current section of the task or document being processed.  
· iteration: An integer representing the current iteration of the task.  
· agent_report: A string that holds the accumulated report generated by the agent so far.  
· guide_line: A string providing guidelines for the task at hand.  
· detailed_web_results: An optional string that contains detailed results from web scraping, defaulting to an empty string if not provided.

**Code Description**: The _action_router function orchestrates the decision-making process for an intelligent agent by determining the next steps based on the agent's thought process, the results of previous searches, and the current task context. It begins by invoking the _model_action_decision function, which assesses the agent's state and generates a thought, action, and any necessary data based on the provided search results, task, and current section.

Depending on the action determined by _model_action_decision, the function can execute one of three primary actions:

1. **SEARCH**: If the action is to search, the function performs a new search using the agent's search aggregator. It appends the new search results to the agent's training data and recursively calls _action_router to process the new results, allowing the agent to make further decisions based on the updated context.

2. **BROWSE**: If the action is to browse, the function utilizes the agent's content scraper to scrape web content from the URLs specified in the data. The results are appended to the detailed web results, and the function again recursively calls _action_router to allow the agent to decide on the next steps based on the newly scraped content.

3. **START_WRITING**: If the action is to start writing, the function generates the final content for the specified section by calling the agent's chat_with_template method. It constructs the content based on the task, current context, guidelines, and previously accumulated notes. The generated content is then logged and returned as the output of the function.

The _action_router function is called by the process_single_task function, which manages the execution of a single task by initializing the agent and processing the task through various steps. Additionally, it is invoked within the start_writing method of the Session class, which initiates the content generation process for a specific section.

**Note**: It is essential to ensure that the agent is properly initialized and that all input parameters are valid. The function relies on the correct functioning of the _model_action_decision function and the agent's methods for searching, browsing, and writing. Proper error handling should be in place to manage any exceptions that may arise during the execution of these actions.

**Output Example**: A possible appearance of the code's return value when executing the function could look like this:
```python
"The generated content for the specified section is: This is the introduction to the topic."
```
## FunctionDef process_single_task(task, file_name)
**process_single_task**: The function of process_single_task is to manage the execution of a single task by initializing an agent, processing the task, and generating a report based on the provided input.

**parameters**: The parameters of this Function.
· task: A string representing the user task description that needs to be processed.
· file_name: An optional string that specifies the name of the ground truth data file. If not provided, it defaults to None.

**Code Description**: The process_single_task function is designed to handle the core logic of processing a user-defined task within the CriticSearch pipeline. It begins by initializing an instance of the BaseAgent class, which serves as the foundation for managing interactions, search functionalities, and conversation history. The agent receives the task input through the receive_task method, which stores the original task for future reference.

The function sets up the agent's training data with the initial task and prepares a memoization structure to store unique notes extracted during the processing. It also initializes a ReportVerifier instance, which is responsible for verifying the factual accuracy of the generated content against a set of extracted facts.

Next, the function determines the path to the JSON file containing ground truth data, defaulting to "2024_Syrian_opposition_offensives.json" if no file name is provided. It then reads the JSON file and generates benchmark items using the ReportBenchmark class, which organizes the content into manageable sections for processing.

The agent's user question is set to the provided task, and the conversation history is updated to include the user's input. A progress bar is initialized to provide visual feedback during the processing of the task.

The function proceeds to evaluate the agent's confidence in generating a response. If the agent is confident, it generates a direct response. If not, it iterates through the sections of the benchmark outline, performing guided searches and extracting relevant information for each section. The agent's training data is updated with the results of these actions, including search thoughts, queries, and notes taken from the search results.

Finally, the generated report is compiled, and the function returns the training data, which includes the final report and any citations extracted during the process. The process_single_task function is called by the main function, which serves as the entry point for executing the CriticSearch pipeline. This establishes a clear relationship between user input and the underlying task execution logic.

**Note**: It is essential to ensure that the input task is well-defined and relevant to the agent's capabilities. The function relies on the proper initialization of the agent and the availability of the specified JSON file for accurate processing and report generation.

**Output Example**: A possible appearance of the code's return value when executing the function could look like this:
```json
[
    {"from": "human", "value": "What is the status of the Syrian opposition?"},
    {"from": "agent", "thought": "The current status is...", "action": "SEARCH", "action_content": ["query1", "query2"], "action_result": ["result1", "result2"]},
    {"from": "verifier", "section": "Section 1", "accuracy": 0.85},
    {"from": "agent", "final_report": "The comprehensive report is...", "citation": ["http://example.com/citation1"]}
]
```
## FunctionDef main
**main**: The function of main is to serve as the entry point for executing the CriticSearch pipeline, handling user input and managing task processing.

**parameters**: The parameters of this Function.
· task: A string representing the user task description that needs to be processed.
· file_name: An optional string that specifies the name of the ground truth data file. If not provided, it defaults to None.

**Code Description**: The main function initializes an argument parser using the argparse module to facilitate command-line interaction. It sets up the parser with a description of the application and defines the required positional argument "task" along with an optional argument for the file name, which can be abbreviated with "-f". 

Once the arguments are parsed, the function attempts to process the specified task by calling the process_single_task function, passing the task and file_name as parameters. This function is responsible for executing the core logic of the CriticSearch pipeline, which includes managing agents, processing user queries, and generating reports based on the provided task.

If the task processing is successful and returns a result, the main function prints the result to the console. In the event of an exception during the task processing, the function catches the exception and invokes the print_exception method from the RichPrinter class to log the error message and print the exception details. This ensures that any issues encountered during execution are communicated clearly to the user, and the application exits with a status code of 1 to indicate failure.

The main function serves as a critical component of the application, orchestrating the flow of data from user input to task execution and error handling. It directly interacts with the process_single_task function, which encapsulates the logic for processing the task, and the print_exception method, which enhances the application's robustness by providing informative error messages.

**Note**: It is essential for users to provide a well-defined task description when invoking the main function. The optional file_name parameter should also be specified if a specific ground truth data file is required for the task processing. Proper usage of command-line arguments is crucial for the successful execution of the CriticSearch pipeline.
