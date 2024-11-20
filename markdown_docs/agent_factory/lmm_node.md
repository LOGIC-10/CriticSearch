## ClassDef LLMNode
**LLMNode**: The function of LLMNode is to serve as a base class representing an LLM Node in the execution graph, handling execution and optimization of prompts using LLMs and TextGrad.

**attributes**: The attributes of this Class.
· name: Unique identifier for the node.  
· llm_model: Identifier for the LLM model to be used.  
· prompt_template: Template string for the LLM prompt.  
· config: Configuration dictionary for LLM settings.  
· router: Optional function to determine the next node based on state.  
· input_schema: Optional schema to validate input data.  
· output_schema: Optional schema to validate output data.  
· optimized: Boolean flag indicating if the node has been optimized.  
· frozen: Boolean flag indicating if the node is frozen and cannot be modified.  
· optimizer: Placeholder for the optimizer, to be initialized during optimization.  

**Code Description**: The LLMNode class is designed to facilitate the execution of tasks using large language models (LLMs) within an execution graph. It provides methods for executing tasks, optimizing prompts, and validating input and output data against specified schemas. The constructor initializes the node with essential parameters such as its name, the LLM model to be used, the prompt template, and configuration settings. The optional parameters allow for dynamic routing and validation of input and output data.

The `execute` method is responsible for running the node's task. It validates the input data, generates a prompt using the provided template, and then calls the LLM to obtain a response. If the node is frozen, execution is skipped, and a warning is logged. The method also handles exceptions, logging errors and returning an error message if execution fails.

The `optimize` method enhances the prompt template using TextGrad, a tool for gradient-based optimization. It initializes necessary variables, sets up the model, and iteratively adjusts the prompt based on performance evaluations until a stopping criterion is met. After optimization, the prompt template is updated, and the node is marked as frozen to prevent further modifications.

The `validate_input` and `validate_output` methods ensure that the data conforms to the specified schemas, raising exceptions if validation fails. The `adjust_prompt` method allows for modifications to the prompt template unless the node is frozen. Finally, the `route` method determines the next node to execute based on the current state, utilizing an optional routing function.

The LLMNode class serves as a foundational component for its subclasses, such as ConstrainedDecodingNode and SocraticRoutingNode. These subclasses inherit from LLMNode and extend its functionality by enforcing strict input/output types or facilitating dynamic routing based on context, respectively. This hierarchical structure allows for specialized behavior while maintaining the core execution and optimization capabilities provided by LLMNode.

**Note**: When using the LLMNode class, ensure that the input and output schemas are correctly defined to avoid validation errors. Additionally, be aware that once the node is optimized, the prompt template cannot be adjusted unless the node is unfrozen.

**Output Example**: A possible return value from the `execute` method could be:
```json
{
  "response": "This is the generated response from the LLM based on the input data."
}
```
### FunctionDef __init__(self, name, llm_model, prompt_template, config, router, input_schema, output_schema)
**__init__**: The function of __init__ is to initialize an instance of the LLMNode class with specified parameters.

**parameters**: The parameters of this Function.
· name: Unique identifier for the node.  
· llm_model: Identifier for the LLM model to be used.  
· prompt_template: Template string for the LLM prompt.  
· config: Configuration dictionary for LLM settings.  
· router: Optional function to determine the next node based on state.  
· input_schema: Optional schema to validate input data.  
· output_schema: Optional schema to validate output data.  

**Code Description**: The __init__ function is a constructor for the LLMNode class, which is responsible for setting up the initial state of an LLMNode object. It takes several parameters that define the characteristics and behavior of the node. The 'name' parameter serves as a unique identifier, allowing for easy reference to the node within a larger system. The 'llm_model' parameter specifies which language model will be utilized, while 'prompt_template' provides a string template that will be used to generate prompts for the model. The 'config' parameter is a dictionary that contains various settings related to the LLM's configuration, allowing for customization of its behavior.

Additionally, the constructor accepts optional parameters: 'router', which is a callable function that can determine the next node based on the current state; 'input_schema', which is a dictionary that defines the expected structure of input data; and 'output_schema', which outlines the expected structure of output data. These optional parameters enhance the flexibility and robustness of the LLMNode by allowing for validation and routing based on specific criteria.

The constructor also initializes several attributes, including 'optimized', 'frozen', and 'optimizer', which are set to default values. The 'optimized' and 'frozen' attributes are initialized to False, indicating that the node is not yet optimized or frozen in its current state. The 'optimizer' attribute is set to None, indicating that it will be initialized later during the optimization process.

Finally, the constructor logs an informational message indicating that the LLMNode has been successfully initialized, which can be useful for debugging and tracking the state of the application.

**Note**: It is important to ensure that the parameters passed to the __init__ function are valid and conform to the expected types, as this will affect the behavior of the LLMNode instance. Proper validation of input and output schemas is recommended to maintain data integrity.
***
### FunctionDef execute(self, input_data)
**execute**: The function of execute is to perform the node's task using the LLM (Large Language Model) and return the output data.

**parameters**: The parameters of this Function.
· input_data: A dictionary containing input data for the node.

**Code Description**: The execute function is a critical method within the LLMNode class that orchestrates the execution of a task using a specified LLM. It begins by checking if the node is in a "frozen" state, which prevents any further execution. If the node is frozen, a warning is logged, and an empty dictionary is returned, indicating that no execution took place.

If the node is not frozen, the function proceeds to validate the input data against a predefined schema, if such a schema exists. This validation is performed by calling the validate_input method, which ensures that the input_data adheres to the expected format and constraints. This step is essential for maintaining data integrity and preventing errors during the execution process.

Next, the function generates a prompt for the LLM by formatting a prompt template with the provided input_data. This prompt is crucial as it guides the LLM in generating a relevant response. The generated prompt is logged for debugging purposes.

The function then calls an external helper function, call_llm, passing the necessary parameters such as the model, system prompt, user prompt, and configuration. This function is responsible for interacting with the LLM and obtaining a response based on the generated prompt. The response from the LLM is logged for further analysis.

After receiving the LLM's response, the function prepares the output data in a dictionary format. It then validates this output data against a predefined output schema, if available, by invoking the validate_output method. This validation ensures that the output conforms to the expected structure and constraints.

Finally, if the execution is successful, an informational log is generated, and the output data is returned. In the event of any exceptions during the execution process, an error message is logged, and a dictionary containing the error details is returned. This robust error handling mechanism ensures that any issues encountered during execution are clearly communicated.

The execute function is integral to the overall functionality of the LLMNode class, as it encapsulates the entire process of validating input, generating prompts, interacting with the LLM, and validating output, thereby ensuring a seamless execution flow.

**Note**: It is important to ensure that the input_data provided to the execute function is structured as a dictionary and that both input and output schemas are properly defined in the LLMNode instance. Failure to do so may result in validation errors, which will be logged and raised as exceptions.

**Output Example**: A possible return value from the execute function could be:
```json
{
    "response": "This is the generated response from the LLM based on the input data."
}
```
In the case of an error, the return value might look like:
```json
{
    "error": "Input validation error: <details of the validation issue>"
}
```
***
### FunctionDef optimize(self, sample_data, evaluator)
**optimize**: The function of optimize is to enhance the prompt of the node using the TextGrad optimization technique.

**parameters**: The parameters of this Function.
· sample_data: A dictionary containing sample input and expected output for the optimization process.  
· evaluator: An instance of the Evaluator class that is responsible for assessing the performance of the model during optimization.

**Code Description**: The optimize function is designed to improve the prompt template of a node by utilizing the TextGrad framework. The function begins by checking if the node has already been optimized or if it is in a frozen state, in which case it logs an informational message and exits early. If the node is eligible for optimization, it proceeds to initialize the necessary components for the optimization process.

The function sets the backward engine for TextGrad based on the configuration provided. It creates a prompt variable that is marked to require gradients, indicating that it will be adjusted during the optimization. A model instance of BlackboxLLM is created using the specified language model and system prompt. The optimizer is initialized with the prompt variable, and a loss function is defined based on a loss instruction from the configuration.

The optimization process is executed in a loop for a maximum number of steps defined by MAX_OPTIMIZATION_STEPS. In each iteration, the model generates a prediction based on the input data provided in sample_data. The loss is computed using the loss function, and a backward pass is performed to calculate gradients. The optimizer then updates the prompt variable based on the computed gradients.

After each optimization step, the accuracy of the prediction is evaluated against the expected output using the evaluator. If the evaluator determines that optimization should stop based on the accuracy, the process is terminated early. Once the optimization is complete, the prompt template is updated with the optimized prompt, and the node is marked as optimized and frozen to prevent further modifications.

Throughout the process, logging statements are used to provide insights into the optimization steps, including predictions, loss values, and accuracy metrics. In the event of an error during the optimization, an error message is logged to indicate the failure.

**Note**: It is important to ensure that the node is not already optimized or frozen before calling this function. Proper configuration of the backward engine and loss instruction is necessary for effective optimization.

**Output Example**: The optimized prompt template might appear as follows: "What is the correct response to the input: [input data]?"
***
### FunctionDef validate_input(self, input_data)
**validate_input**: The function of validate_input is to validate the input data against a predefined input schema.

**parameters**: The parameters of this Function.
· input_data: A dictionary containing the input data that needs to be validated.

**Code Description**: The validate_input function is designed to ensure that the input data provided to the LLMNode instance adheres to a specified schema, which is stored in the instance variable self.input_schema. This validation process is crucial for maintaining data integrity and ensuring that the input data meets the expected format and constraints before any further processing occurs.

The function begins by attempting to validate the input_data against the json_schema, which is derived from self.input_schema. If a schema is defined, the function utilizes the jsonschema library to perform the validation. The validate function checks if the input_data conforms to the json_schema. If the validation is successful, a debug log is generated to indicate that the input data is valid.

However, if the input_data does not conform to the schema, a ValidationError is raised. This error is caught by the function, which logs an error message detailing the validation issue and raises a ValueError to signal that the input validation has failed. This mechanism ensures that any issues with the input data are clearly communicated and handled appropriately.

The validate_input function is called within the execute method of the LLMNode class. Before executing the main task of the node, the execute method checks if the node is frozen and if an input schema is defined. If both conditions are met, it calls validate_input to validate the input_data. This ensures that only valid input data is processed further, thereby preventing potential errors during execution and maintaining the robustness of the node's operations.

**Note**: It is important to ensure that the input_data provided to the validate_input function is structured as a dictionary and that the input schema is properly defined in self.input_schema. Failure to do so may result in validation errors, which will be logged and raised as exceptions.
***
### FunctionDef validate_output(self, output_data)
**validate_output**: The function of validate_output is to validate the output data against a predefined output schema.

**parameters**: The parameters of this Function.
· output_data: Dictionary containing output data.

**Code Description**: The validate_output function is responsible for ensuring that the output data generated by the node adheres to a specified schema, which is defined in the self.output_schema attribute. This validation process is crucial for maintaining data integrity and ensuring that the output meets the expected format and constraints.

When the function is called, it attempts to validate the provided output_data dictionary using the jsonschema library. If an output schema is defined (i.e., self.output_schema is not None), the function imports the validate and ValidationError classes from the jsonschema module. It then calls the validate function, passing the output_data and the schema for validation.

If the output_data does not conform to the schema, a ValidationError is raised. The function catches this exception, logs an error message that includes the name of the node and the details of the validation error, and subsequently raises a ValueError to indicate that the output validation has failed.

This function is called within the execute method of the LLMNode class. After generating the output data from the LLM response, the execute method checks if an output schema is defined. If so, it invokes validate_output to ensure that the output data is valid before proceeding. This relationship highlights the importance of validate_output in the overall execution flow, as it acts as a safeguard to ensure that only valid data is returned from the node's execution.

**Note**: It is important to ensure that the output schema is properly defined before calling this function, as the validation process relies on it. Additionally, users should handle the ValueError exception that may be raised if the output data fails validation, to ensure robust error handling in their applications.
***
### FunctionDef adjust_prompt(self, new_prompt)
**adjust_prompt**: The function of adjust_prompt is to modify the prompt template based on new input while considering the state of the object.

**parameters**: The parameters of this Function.
· new_prompt: A string representing the new prompt template that will replace the current one.

**Code Description**: The adjust_prompt function is designed to update the prompt template of an instance of the class it belongs to. It accepts a single parameter, new_prompt, which is expected to be a string. The function first checks if the instance is not in a "frozen" state, indicated by the self.frozen attribute. If the instance is not frozen, it assigns the new_prompt value to the prompt_template attribute of the instance and logs an informational message indicating that the prompt has been successfully adjusted for the specific node identified by self.name. If the instance is frozen, it logs a warning message stating that the prompt cannot be adjusted while in this state.

**Note**: It is important to ensure that the instance is not frozen before attempting to adjust the prompt. If the instance is frozen, any attempt to change the prompt will result in a warning, and the prompt will remain unchanged. This mechanism is crucial for maintaining the integrity of the prompt in scenarios where it should not be modified.
***
### FunctionDef route(self, state)
**route**: The function of route is to determine the next node to execute based on the current state.

**parameters**: The parameters of this Function.
· state: A dictionary representing the current state of the system.

**Code Description**: The route function is responsible for determining the next node in a routing process based on the provided current state. It first checks if a router function is assigned to the instance. If a router is present, it attempts to call this router function with the current state as an argument. If the router successfully returns a value, this value represents the name of the next node to which the process should transition. The function logs a debug message indicating the routing action taken. In the event of an exception during the routing process, an error message is logged, and the function returns None, indicating that routing could not be performed. If no router is assigned, a debug message is logged stating that no routing action will be taken, and the function also returns None.

**Note**: It is important to ensure that the router function is properly defined and can handle the state input to avoid exceptions during execution. Additionally, the logging mechanism should be configured to capture debug and error messages for troubleshooting purposes.

**Output Example**: If the current state is processed correctly and the router function returns a valid next node, the output could be a string such as "next_node_1". If there is an error or no router is defined, the output will be None.
***
## ClassDef ConstrainedDecodingNode
**ConstrainedDecodingNode**: The function of ConstrainedDecodingNode is to enforce strict input and output types for tasks requiring precise outputs.

**attributes**: The attributes of this Class.
· name: Unique identifier for the node.  
· llm_model: Identifier for the LLM model to be used.  
· prompt_template: Template string for the LLM prompt.  
· config: Configuration dictionary for LLM settings.  
· input_schema: Schema to validate input data.  
· output_schema: Schema to validate output data.  

**Code Description**: The ConstrainedDecodingNode class is a specialized subclass of the LLMNode class, designed to ensure that both input and output data adhere to predefined schemas. This class is particularly useful in scenarios where the accuracy and format of the data are critical, such as in applications involving natural language processing tasks that require strict compliance with expected data structures.

Upon initialization, the ConstrainedDecodingNode inherits attributes and methods from its parent class, LLMNode. The constructor of ConstrainedDecodingNode accepts parameters such as name, llm_model, prompt_template, config, input_schema, and output_schema. These parameters are essential for defining the node's identity, the model it utilizes, the prompt it generates, and the validation schemas for input and output data.

The relationship with its parent class, LLMNode, is significant as it inherits the core functionalities that allow for the execution of tasks using large language models (LLMs). The LLMNode class provides methods for executing tasks, optimizing prompts, and validating data against schemas. The ConstrainedDecodingNode extends this functionality by enforcing strict validation rules through the input_schema and output_schema parameters. This ensures that any data processed by the node meets the specified criteria, thereby reducing the likelihood of errors during execution.

The ConstrainedDecodingNode is particularly beneficial in environments where data integrity is paramount. By utilizing this class, developers can create nodes that not only execute tasks but also guarantee that the data being processed conforms to expected formats, thus enhancing the reliability of the overall system.

**Note**: When using the ConstrainedDecodingNode, it is crucial to define the input and output schemas accurately to prevent validation errors. This class is intended for scenarios where strict adherence to data formats is necessary, and any deviations may lead to execution failures.
### FunctionDef __init__(self, name, llm_model, prompt_template, config, input_schema, output_schema)
**__init__**: The function of __init__ is to initialize the ConstrainedDecodingNode with specified parameters.

**parameters**: The parameters of this Function.
· name: Unique identifier for the node.  
· llm_model: Identifier for the LLM model to be used.  
· prompt_template: Template string for the LLM prompt.  
· config: Configuration dictionary for LLM settings.  
· input_schema: Schema to validate input data.  
· output_schema: Schema to validate output data.  

**Code Description**: The __init__ function is a constructor for the ConstrainedDecodingNode class. It is responsible for initializing an instance of the class with specific attributes that define its behavior and configuration. The function takes six parameters: `name`, `llm_model`, `prompt_template`, `config`, `input_schema`, and `output_schema`. Each of these parameters serves a distinct purpose in setting up the node. The `name` parameter provides a unique identifier for the node, which is essential for distinguishing it from other nodes in a larger system. The `llm_model` parameter specifies which language model will be utilized, allowing for flexibility in model selection. The `prompt_template` parameter is a string that serves as a template for generating prompts for the language model, ensuring that the input to the model is formatted correctly. The `config` parameter is a dictionary that contains various settings related to the language model, enabling customization of its behavior. The `input_schema` and `output_schema` parameters are dictionaries that define the structure and validation rules for the input and output data, respectively. This ensures that the data processed by the node adheres to expected formats, enhancing robustness and reliability.

The constructor also calls the superclass's __init__ method, passing along all parameters to ensure that any inherited properties or behaviors are properly initialized. This is crucial for maintaining the integrity of the object-oriented design and ensuring that the ConstrainedDecodingNode inherits any necessary functionality from its parent class.

**Note**: When using this constructor, it is important to ensure that all parameters are provided with valid values to avoid runtime errors. The schemas for input and output should be carefully defined to match the expected data structures, as this will affect the node's ability to process data correctly.
***
## ClassDef SocraticRoutingNode
**SocraticRoutingNode**: The function of SocraticRoutingNode is to facilitate reasoning and dynamic routing by deciding the next node(s) based on the current context.

**attributes**: The attributes of this Class.
· name: Unique identifier for the node.  
· llm_model: Identifier for the LLM model to be used.  
· prompt_template: Template string for the LLM prompt.  
· config: Configuration dictionary for LLM settings.  
· router: Function to determine the next node based on state.  
· input_schema: Optional schema to validate input data.  
· output_schema: Optional schema to validate output data.  
· optimized: Boolean flag indicating if the node has been optimized.  
· frozen: Boolean flag indicating if the node is frozen and cannot be modified.  
· optimizer: Placeholder for the optimizer, to be initialized during optimization.  

**Code Description**: The SocraticRoutingNode class is a specialized subclass of the LLMNode class, designed to enhance the functionality of LLM nodes by incorporating reasoning capabilities and dynamic routing based on contextual information. It inherits all attributes and methods from the LLMNode class, which serves as a foundational component for executing tasks using large language models (LLMs).

The constructor of SocraticRoutingNode initializes the node with essential parameters such as its name, the LLM model to be used, the prompt template, and configuration settings. Additionally, it accepts a router function that determines the next node to execute based on the current state. This dynamic routing capability allows for more flexible and context-aware execution flows within an execution graph.

By leveraging the existing methods of the LLMNode class, the SocraticRoutingNode can execute tasks, validate input and output data, and optimize its prompt template. The routing functionality provided by the router parameter enables the node to adapt its behavior based on the context, making it suitable for applications that require reasoning and decision-making.

The SocraticRoutingNode does not introduce new methods but extends the capabilities of its parent class, allowing it to participate in a more complex execution graph where the flow of execution can change dynamically based on the context provided by the router function.

**Note**: When utilizing the SocraticRoutingNode, it is essential to ensure that the router function is correctly implemented to facilitate accurate routing decisions. Additionally, the input and output schemas should be defined appropriately to avoid validation errors during execution.
### FunctionDef __init__(self, name, llm_model, prompt_template, config, router)
**__init__**: The function of __init__ is to initialize the SocraticRoutingNode with specified parameters.

**parameters**: The parameters of this Function.
· name: Unique identifier for the node.  
· llm_model: Identifier for the LLM model to be used.  
· prompt_template: Template string for the LLM prompt.  
· config: Configuration dictionary for LLM settings.  
· router: Function to determine the next node based on state.  

**Code Description**: The __init__ function is a constructor for the SocraticRoutingNode class. It is responsible for initializing an instance of the class with the provided parameters. The function takes five parameters: `name`, `llm_model`, `prompt_template`, `config`, and `router`. Each parameter serves a specific purpose in configuring the node's behavior and functionality. 

- The `name` parameter is a string that serves as a unique identifier for the node, allowing it to be referenced distinctly within a larger system. 
- The `llm_model` parameter specifies which language model (LLM) will be utilized by the node, ensuring that the correct model is employed for processing inputs.
- The `prompt_template` parameter is a string that defines the format of the prompt that will be sent to the LLM, allowing for customization of the input based on the context or requirements of the task.
- The `config` parameter is a dictionary that contains various settings and configurations related to the LLM, enabling fine-tuning of its behavior and performance.
- The `router` parameter is a callable function that takes a dictionary as input and returns a string. This function is crucial for determining the next node to which the process should route based on the current state, facilitating dynamic decision-making within the node network.

The constructor also calls the superclass's __init__ method, passing along the parameters along with `input_schema` and `output_schema`, which are set to None in this case. This ensures that the base class is properly initialized with the relevant attributes.

**Note**: It is important to ensure that the parameters passed to the __init__ function are correctly formatted and valid, as they directly influence the behavior of the SocraticRoutingNode. Proper configuration of the router function is essential for the effective routing of tasks within the node network.
***
