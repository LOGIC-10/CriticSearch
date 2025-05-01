## FunctionDef flatten_outline(section, depth, path)
**flatten_outline**: The function of flatten_outline is to flatten a hierarchical outline structure into a list of sections, each annotated with its depth and path.

**parameters**: The parameters of this Function.
· section: A dictionary representing a section of the outline, which may contain a title and potentially children sections.
· depth: An integer indicating the current depth level in the outline hierarchy, defaulting to 1.
· path: A list that tracks the path of titles leading to the current section, defaulting to None.

**Code Description**: The flatten_outline function is designed to transform a nested outline structure, typically represented in JSON format, into a flat list. Each entry in this list contains a dictionary with three keys: "path", "section", and "depth". The "path" key holds a list of titles leading to the current section, the "section" key contains the original section data, and the "depth" key indicates how deep the section is within the hierarchy.

The function begins by checking if the path parameter is None; if so, it initializes it as an empty list. It then constructs a dictionary for the current section, appending the section's title to the path and setting the depth. This dictionary is added to a list called flat, which will ultimately be returned.

If the current section contains children (indicating that it is not a leaf node), the function iterates over each child section. For each child, it recursively calls flatten_outline, increasing the depth by one and passing the updated path. The results from these recursive calls are extended into the flat list.

The flatten_outline function is called within the main function of the project, specifically after the outline has been generated from search results. The resulting flat_sections list is then used to generate content for each section in parallel, allowing for efficient processing of potentially large outlines. This integration highlights the function's role in transforming complex hierarchical data into a manageable format for further processing.

**Note**: It is important to ensure that the input section is structured correctly as a JSON object with the expected keys ("title" and "children") for the function to operate effectively.

**Output Example**: An example return value of flatten_outline might look like this for a given outline:
[
    {"path": ["Introduction"], "section": {"title": "Introduction", "children": [...]}, "depth": 1},
    {"path": ["Introduction", "Background"], "section": {"title": "Background", "children": [...]}, "depth": 2},
    {"path": ["Introduction", "Background", "Details"], "section": {"title": "Details"}, "depth": 3}
]
## FunctionDef generate_content_for_section(common_agent, section, TASK)
**generate_content_for_section**: The function of generate_content_for_section is to generate detailed textual content for a specified section based on a search query and a given task.

**parameters**: The parameters of this Function.
· common_agent: An instance of the BaseAgent class that facilitates search and chat functionalities.
· section: A dictionary containing information about the section, specifically its title.
· TASK: A string representing the overarching task or topic under which the content is to be generated.

**Code Description**: The generate_content_for_section function is designed to create content for a specific section of a report or document. It begins by extracting the title from the provided section dictionary. Using this title, it formulates a search query that prompts the common_agent to generate relevant search queries related to the title within the context of the specified TASK. The search results obtained from the common_agent's search_and_browse method are then utilized to construct a detailed prompt for generating content.

This prompt instructs the common_agent to write one or several paragraphs that logically present data and facts about the section's title, ensuring that all information is cited correctly using a specified format. The content is generated through the common_agent's common_chat method, which processes the prompt and returns the generated paragraphs.

The function is called within a multi-threaded context in the main function of the project. Specifically, it is invoked for each section of a flattened outline generated from initial search results. This allows for parallel content generation across multiple sections, enhancing efficiency and reducing the overall time required to compile the report. The results from each call to generate_content_for_section are collected and later reconstructed into a coherent markdown format.

**Note**: It is important to ensure that the common_agent is properly initialized and that the section parameter contains a valid title to avoid errors during content generation. Additionally, the function's output should be formatted correctly to maintain consistency in citation style.

**Output Example**: A possible appearance of the code's return value could be:
"Climate change is a pressing global issue that affects various aspects of life on Earth. According to the Intergovernmental Panel on Climate Change (IPCC), the average global temperature has risen by approximately 1.2 degrees Celsius since the late 19th century<\cite>https://www.ipcc.ch/report/ar6/wg1/#:~:text=The%20average%20global%20temperature%20has%20risen%20by%20approximately%201.2%20degrees%20Celsius%20since%20the%20late%2019th%20century<\cite>. This increase has led to more frequent and severe weather events, including hurricanes, droughts, and floods<\cite>https://www.ncdc.noaa.gov/sotc/global/202012#climate<\cite>."
## FunctionDef reconstruct_markdown(outline, flat_contents)
**reconstruct_markdown**: The function of reconstruct_markdown is to generate a final Markdown document based on a hierarchical outline and corresponding content.

**parameters**: The parameters of this Function.
- outline: A dictionary that represents the hierarchical structure of the document, including sections and their titles.
- flat_contents: A list of tuples where each tuple contains a dictionary representing a section and the corresponding content for that section.

**Code Description**: 
The `reconstruct_markdown` function is responsible for assembling a Markdown document by combining the hierarchical structure of a document (provided in the `outline` parameter) with corresponding content (provided in the `flat_contents` parameter). It follows these steps:
1. **Mapping Content**: It first creates a dictionary (`content_map`) where each key is the full path of a section (represented as a tuple of strings), and the value is the content associated with that section. This is done by iterating over the `flat_contents` and extracting the path and content for each section.
   
2. **Recursive Content Generation**: The function defines a helper function `helper` that is recursively used to generate Markdown for each section of the outline. This function takes a section and the current path (starting as an empty list) as input.
   - For each section, it combines the title (from the `title` field) with the correct level of Markdown headers (`#` symbols based on the depth of the section in the outline).
   - If content for the section exists (i.e., its path is found in the `content_map`), the content is appended to the Markdown string for that section.
   - If the section has child sections (i.e., if `children` exist), the function recursively processes each child section, appending their corresponding Markdown to the current section.

3. **Result Construction**: The `helper` function is initially called for the top-level sections of the document, and the resulting Markdown for all sections is concatenated into the `result` string. If the `outline` contains a title, it is added at the beginning of the Markdown document with the appropriate header (`#`).

4. **Final Markdown Output**: After all sections and their content have been processed, the final Markdown string is returned.

This function is integral to the document generation pipeline. Specifically, it is used in the context of a broader workflow where an agent gathers search results and creates an outline, followed by generating content for individual sections. Once content is generated in parallel, `reconstruct_markdown` is called to structure that content into a final Markdown document that is later polished and saved.

The function is invoked within the `main` function as part of a multi-step document generation process. After gathering search results and content for individual sections, `reconstruct_markdown` is used to combine the content and hierarchical structure into a Markdown report, which is further polished and stored.

**Note**: The function relies on the assumption that `flat_contents` contains content for each section as a tuple where the first element is the section's metadata (containing a "path") and the second element is the content itself. The path is crucial for matching the content to the correct section in the `outline`. Additionally, the recursive nature of the `helper` function means that deeply nested sections are properly handled by the same logic.

**Output Example**: 
For an outline like:
```json
{
    "title": "Main Title",
    "children": [
        {
            "title": "Section 1",
            "children": [
                {"title": "Subsection 1.1", "children": []},
                {"title": "Subsection 1.2", "children": []}
            ]
        },
        {
            "title": "Section 2",
            "children": []
        }
    ]
}
```
and corresponding content for each section, the generated Markdown might look like:
```
# Main Title

## Section 1

### Subsection 1.1

Content for Subsection 1.1

### Subsection 1.2

Content for Subsection 1.2

## Section 2

Content for Section 2
```
### FunctionDef helper(section, path)
**helper**: The function of helper is to recursively generate Markdown text for a given section and its nested sub-sections.

**parameters**:
- parameter1: section (dict) - A dictionary representing a section, containing a title and possibly children, which are nested sections.
- parameter2: path (list, optional) - A list representing the current path of titles. Default is an empty list, and it is used to track the hierarchy of section titles.

**Code Description**:  
The `helper` function is responsible for generating a Markdown representation of a section, including its title and any associated content. It handles nested sections by recursively calling itself for child sections, creating a hierarchical structure based on the depth of the section in the hierarchy. The function performs the following operations:

1. **Initialize Path**: The function begins by constructing a `current_path`, which combines the existing `path` with the title of the current section. This path is used to track the hierarchical level of the section.

2. **Path Key**: It then creates a `path_key`, which is a tuple formed by the `current_path`. This tuple is used to check if there is any associated content for the section in the `content_map`.

3. **Generate Markdown for the Title**: The depth of the section is determined by the length of the `current_path`. The number of hashtags (`#`) in the Markdown title is equal to the depth of the section. The function then constructs the section title in Markdown format (`# Title`).

4. **Include Content**: If there is any content mapped to the `path_key` in the `content_map`, this content is added below the section title. The content is added in Markdown format.

5. **Handle Child Sections**: If the current section has any children (i.e., sub-sections), the function iterates over them and recursively calls itself on each child, appending the generated Markdown to the result.

6. **Return the Result**: After processing the title, content, and children (if any), the function returns the generated Markdown string for the current section and its descendants.

**Note**: 
- The `content_map` must be defined elsewhere in the code, as it is used to retrieve the content associated with each section's path.
- The function is designed to handle hierarchical section structures where each section can have nested sub-sections. The depth of each section is represented in the generated Markdown by the number of `#` symbols in the title.
- The `path` parameter allows the function to track the nesting level of each section and ensures that the correct content is included at each level of the hierarchy.

**Output Example**:  
Given a sample input where `content_map` contains content for each section and its sub-sections, the output might look like this:

For a `section` with the structure:
```python
{
    "title": "Introduction",
    "children": [
        {
            "title": "Background",
            "children": []
        },
        {
            "title": "Objective",
            "children": []
        }
    ]
}
```

And assuming `content_map` has content for "Introduction", "Background", and "Objective", the generated output could look like:

```
# Introduction

This is the content for the Introduction section.

## Background

This is the content for the Background section.

## Objective

This is the content for the Objective section.
```

This example illustrates how the function constructs the hierarchy using `#` for titles and includes content where available.
***
## FunctionDef extract_citations(text)
**extract_citations**: The function of extract_citations is to extract all citations (URLs) enclosed in `<cite>` tags from a given text.

**parameters**:  
· text: The input string in which citations need to be extracted.

**Code Description**:  
The `extract_citations` function is responsible for identifying and extracting URLs that are enclosed within `<cite>` HTML tags in a given text. It uses a regular expression pattern to match these tags and captures the content inside them.

The function begins by initializing an empty list called `citations`, which will hold the URLs found in the input text. It then defines a regular expression pattern `r'<cite>(.*?)<\/cite>'`. This pattern looks for text between `<cite>` and `</cite>` tags. The `re.findall()` function is then used to search the provided text for all matches of this pattern. Each match found is a string containing the URL or citation within the `<cite>` tag. The function returns a list of all these matches.

The function is used within the `process_section` and `parse_markdown_to_structure` functions to handle paragraph-level citation extraction. In `process_section`, it extracts citations from each paragraph of a section, while in `parse_markdown_to_structure`, it performs citation extraction as paragraphs are processed while parsing a markdown text structure. In both cases, the `extract_citations` function helps to collect URLs in the specified `<cite>` tags for further processing or inclusion in the returned document structure.

**Note**: The function does not handle malformed or incomplete HTML tags and assumes that the input text will contain properly formatted `<cite>` tags. The function extracts all citations, regardless of the number or complexity of the tags, and returns them as a list.

**Output Example**:  
Given an input text:
```html
This is a reference to <cite>https://example.com</cite> in the text.
Another citation: <cite>https://another-example.com</cite>.
```

The output would be:
```python
['https://example.com', 'https://another-example.com']
```
## FunctionDef create_document_structure(outline_json, flat_contents)
**create_document_structure**: The function of create_document_structure is to generate a structured document based on a given outline and corresponding content.

**parameters**:
· outline_json: A JSON object representing the outline of the document, which contains hierarchical information about titles and subsections.
· flat_contents: A list of tuples where each tuple contains a dictionary with a "path" key representing the hierarchical path and a content string associated with that path.

**Code Description**:  
The function `create_document_structure` is designed to create a structured document based on an outline and flat content. It takes two inputs: `outline_json` and `flat_contents`.

- `outline_json` is a JSON object that represents the hierarchical structure of the document, including the document title, subsections, and children sections.
- `flat_contents` is a list of tuples, each of which pairs a dictionary containing the path to a section with the corresponding textual content for that section.

The function proceeds by first initializing a `document` dictionary with a title (extracted from `outline_json`), a level (set to 1), and an empty list of subsections. The main goal is to map each section in the outline to its respective content and organize this data in a structured way.

1. **Mapping Content to Paths**:  
   The function creates a `content_map` dictionary where each section's path is mapped to its respective content. The `path` is represented as a tuple derived from the "path" key in the input tuples of `flat_contents`.

2. **Processing Sections**:  
   The function defines an internal function `process_section` which is responsible for recursively processing each section of the outline. Each section is processed based on the depth of its position in the outline, and the content associated with that section is retrieved from `content_map` using the path.

   For each section, the function:
   - Retrieves the section title and assigns it to a new dictionary.
   - If content exists for the section (found using its path in `content_map`), it splits the content into paragraphs, each of which is processed further to extract any citations using a helper function `extract_citations`.
   - If the section contains children (subsections), the function recursively processes each child, appending the result to the `subsections` list for that section.

3. **Document Structure Construction**:  
   After processing all sections in the root of the outline (under the `children` key of `outline_json`), the function returns the fully constructed document, which consists of a hierarchical structure of titles, paragraphs, citations, and subsections.

**Note**: 
- The content is assumed to be divided into paragraphs by empty lines (`\n\n`).
- Citations within paragraphs are processed by a helper function `extract_citations`, although the implementation of this function is not provided here.
- The structure of the outline is assumed to be consistent, where each section may have a title and children, and content is mapped by its hierarchical path.

**Output Example**:  
A possible output of this function could look like the following:

```json
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
            "text": "This is the introduction paragraph.\n\nIt introduces the topic.",
            "citations": ["citation1", "citation2"]
          }
        ],
        "subsections": []
      },
      {
        "title": "Methodology",
        "level": 2,
        "paragraphs": [
          {
            "text": "In this section, we describe the methods used in the study.",
            "citations": []
          }
        ],
        "subsections": [
          {
            "title": "Data Collection",
            "level": 3,
            "paragraphs": [
              {
                "text": "Data was collected through surveys and interviews.",
                "citations": ["citation3"]
              }
            ],
            "subsections": []
          }
        ]
      }
    ]
  }
}
```
### FunctionDef process_section(section, depth, path)
**process_section**: The function of process_section is to process a section of content, extract paragraphs and citations, and recursively handle sub-sections.

**parameters**: The parameters of this Function.
- section: A dictionary representing a section, which contains keys like "title", "children", and possibly other content.
- depth: An integer representing the current depth level of the section in a hierarchical structure, default value is 1.
- path: A list used to track the path taken through the section hierarchy, default value is an empty list.

**Code Description**:  
The `process_section` function is responsible for processing a single section within a larger content structure, extracting its relevant details, including paragraphs and citations, and recursively processing any child sections (subsections).

1. **Section Title and Path Tracking**:
   - The function starts by constructing a list `current_path`, which tracks the path taken to the current section. It appends the current section's title to this path.
   - The `path_key` is formed as a tuple from the `current_path`. This key is then used to look up content for the section from a global `content_map`.

2. **Paragraph Extraction and Citation Handling**:
   - If content for the section is available in `content_map` (as indicated by `path_key`), the content is retrieved and split into paragraphs based on two consecutive newline characters (`\n\n`).
   - For each paragraph, any non-empty paragraphs are processed. The function calls `extract_citations`, which extracts citations (URLs enclosed in `<cite>` tags) from the paragraph. The resulting citations are stored alongside the paragraph text.

3. **Handling Subsections**:
   - If the section contains child sections (subsections), the function creates a list under the key `"subsections"`. It then recursively calls `process_section` for each child, incrementing the `depth` by 1 and passing the updated `path`.

4. **Return Value**:
   - The function returns a dictionary containing:
     - `"title"`: The section's title.
     - `"level"`: The depth level of the section.
     - `"paragraphs"`: A list of dictionaries, each representing a paragraph with associated citation data.
     - `"subsections"`: A list of processed subsections, if any.

This function is designed to support nested sections, where each section can have multiple levels of sub-sections. It is useful for transforming a hierarchical content structure into a more structured format that includes both textual data and citations, making it easier to process or render in a desired output format.

The `process_section` function interacts with the `extract_citations` function to collect citations from paragraphs. This makes it particularly suited for handling structured content that includes references marked by `<cite>` tags.

**Note**: 
- The function assumes that the input data is well-formed, with sections containing a "title" and optional "children".
- The `content_map` must be pre-defined and should map section paths (as tuples) to corresponding content.
- The function handles nested sections and citations extraction, making it suitable for documents with complex structures.

**Output Example**:
Given the following input:
```python
section = {
    "title": "Introduction",
    "children": [
        {"title": "Background"},
        {"title": "Objective"}
    ]
}
```
Assuming the `content_map` contains the relevant content for the sections, the output might look like:
```python
{
    "title": "Introduction",
    "level": 1,
    "paragraphs": [
        {"text": "This is the introduction paragraph. <cite>https://example.com</cite>", "citations": ["https://example.com"]}
    ],
    "subsections": [
        {"title": "Background", "level": 2, "paragraphs": [], "subsections": []},
        {"title": "Objective", "level": 2, "paragraphs": [], "subsections": []}
    ]
}
```
***
## FunctionDef parse_markdown_to_structure(markdown_text)
### Function Documentation: `parse_markdown_to_structure`

#### Overview:
The `parse_markdown_to_structure` function parses a given markdown text and converts it into a structured document format, organizing sections, subsections, and paragraphs based on the markdown syntax. It identifies headers marked with `#` to define sections and handles paragraph content, extracting citations where applicable.

#### Parameters:
- **markdown_text** (str): The input markdown text to be parsed into a structured document. This text can contain headers (denoted by `#`) and paragraphs, with citations included in `<cite>` tags.

#### Returns:
- **document** (dict): A dictionary representing the parsed structure of the markdown text. It includes a top-level document object with a title, level, subsections, and paragraphs. Each section in the markdown is represented as a subsection in the structure.

#### Structure of the returned document:
- **document** (dict):
  - **title** (str): The title of the document, typically set from the first markdown header.
  - **level** (int): The level of the current section. This is determined by the number of `#` characters at the start of a header.
  - **subsections** (list): A list of subsections (if any), with each subsection being a dictionary containing:
    - **title** (str): The title of the subsection.
    - **level** (int): The level of the subsection based on its header.
    - **subsections** (list): Further nested subsections.
    - **paragraphs** (list): A list of paragraphs in the subsection, each represented as a dictionary with:
      - **text** (str): The paragraph text.
      - **citations** (list): A list of citations (URLs) extracted from the paragraph's text, if any.

#### Functionality:
1. **Splitting the Markdown**: The function first splits the input markdown text by line breaks, processing each line to identify headers and paragraphs.
2. **Handling Headers**: Headers are identified by lines starting with `#`. The level of the header (i.e., how many `#` characters it contains) determines the depth of the section in the document structure. New sections are created as subsections of the current section. If the header level is less than or equal to the current section's level, the function adjusts the section stack to properly organize the hierarchy.
3. **Handling Paragraphs**: Text between headers is treated as paragraph content. Paragraphs are collected until an empty line or another header is encountered. Citations within paragraphs, enclosed in `<cite>` tags, are extracted using the `extract_citations` function.
4. **Final Processing**: After processing all lines, any remaining paragraph text is added to the document structure, ensuring that no content is missed.

#### Example:
Given the following markdown input:
```markdown
# Title of Document
## Introduction
This is an introduction paragraph with a citation <cite>https://example.com</cite>.
## Main Content
This is the main content, which also contains a citation <cite>https://another-example.com</cite>.
```

The function will return a document structure like this:
```python
{
    "document": {
        "title": "Title of Document",
        "level": 1,
        "subsections": [
            {
                "title": "Introduction",
                "level": 2,
                "subsections": [],
                "paragraphs": [
                    {
                        "text": "This is an introduction paragraph with a citation.",
                        "citations": ["https://example.com"]
                    }
                ]
            },
            {
                "title": "Main Content",
                "level": 2,
                "subsections": [],
                "paragraphs": [
                    {
                        "text": "This is the main content, which also contains a citation.",
                        "citations": ["https://another-example.com"]
                    }
                ]
            }
        ]
    }
}
```

#### Dependencies:
- **extract_citations**: The function relies on `extract_citations` to extract any citations embedded in `<cite>` HTML tags within paragraphs.

#### Usage:
The `parse_markdown_to_structure` function is typically used when there's a need to convert a markdown document into a structured format, such as when processing or analyzing documents with hierarchical content. The parsed structure can be used for further processing, such as generating reports or extracting specific information from different sections.
## FunctionDef main(TASK, MAX_ITERATION)
**main**: The function of main is to orchestrate the conversation process between a user and an intelligent agent, managing iterations of response generation, feedback, and content refinement.

**parameters**: The parameters of this Function.
· TASK: A string representing the user's question or task that the agent needs to address.  
· MAX_ITERATION: An integer specifying the maximum number of iterations for refining the agent's response.

**Code Description**: The main function serves as the central control point for the interaction between the user and the intelligent agent. It begins by initializing a common agent instance of the BaseAgent class and setting the user's question as the task. The function sets the logging level based on the configuration and logs the start of the conversation.

The conversation history is updated to include the user's initial question. The function then enters a loop that iterates up to the specified maximum number of iterations. During each iteration, it performs several key actions:

1. **Initial Setup**: On the first iteration, it checks the agent's confidence in answering the task. If the agent is confident, it generates a direct answer. If not, it performs a search to gather information, constructs a report outline, and generates content for each section in parallel using threading.

2. **Content Generation**: The content for each section is generated based on search results, and the responses are collected. The generated content is then polished to create a final report, which is saved in Markdown format.

3. **Feedback Loop**: After generating the initial response, the function evaluates the answer using a CriticAgent. The CriticAgent provides feedback, which may lead to further iterations of content refinement. If the feedback indicates that the process should stop, the function logs the total iterations and returns the final answer.

4. **Subsequent Iterations**: For iterations beyond the first, the function updates the answer based on the previous response and the latest search results, incorporating feedback from the CriticAgent. It continues to refine the answer until the maximum number of iterations is reached or a stopping condition is met.

The main function integrates various components of the project, including the BaseAgent for generating responses, the CriticAgent for evaluating those responses, and utility functions for content generation and Markdown reconstruction. This orchestration ensures a dynamic and iterative process that enhances the quality of the agent's responses through continuous feedback and refinement.

**Note**: It is essential to ensure that the TASK parameter is well-defined and relevant to the agent's capabilities. The MAX_ITERATION parameter should be set appropriately to balance between thoroughness and efficiency in response generation.

**Output Example**: A possible appearance of the code's return value when executing the main function might look like this:
```
"Based on the gathered information and feedback, here is the final answer to your question: ..."
```
