**Specification Document for the Initial Framework**

**1. Overview**

The framework is designed to create and optimize agent workflows using Large Language Models (LLMs). It uses a hybrid Q* learning algorithm for exploring configurations and `text grad` for prompt optimization. The framework consists of:

- **LLM Nodes:** Basic units of computation, specialized for different tasks.
- **Planner:** Utilizes a large LLM to plan the execution graph based on inputs.
- **Evaluator:** Assesses the performance of nodes and determines when to stop optimization.
- **Global Context Notebook:** Maintains embeddings and a knowledge base to reuse optimized subgraphs.

**2. Components**

**2.1 LLMNode Class**

- **Description:** Base class representing a node in the execution graph, encapsulating an LLM and its behavior.
- **Specializations:**
  - **ConstrainedDecodingNode:** Enforces strict input/output types, used for tasks requiring precise outputs.
  - **SocraticRoutingNode:** Facilitates reasoning and decision-making, can dynamically route to other nodes based on context.

- **Attributes:**
  - `name`: Identifier for the node.
  - `llm_model`: The LLM instance used by the node.
  - `prompt_template`: Template for generating prompts.
  - `router`: Function or method that decides the next node(s) to execute.
  - `input_schema`: Defines expected input format (for constrained nodes).
  - `output_schema`: Defines expected output format (for constrained nodes).
  - `optimized`: Boolean indicating if the node has been optimized.
  - `frozen`: Boolean indicating if the node should no longer be modified.

- **Methods:**
  - `execute(input_data)`: Executes the node's logic and returns the output.
  - `optimize(sample_data, evaluator)`: Performs prompt optimization using `text grad`.
  - `route(state)`: Determines the next node(s) to execute based on the router logic.

**2.2 Planner Class**

- **Description:** Uses a large LLM to plan the execution graph and explore different configurations using the Q* learning algorithm.

- **Attributes:**
  - `llm_model`: The large LLM used for planning.
  - `goal`: The goal the agent is optimizing for.
  - `available_nodes`: List of LLM nodes that can be spawned.
  - `complexity`: Complexity parameter affecting the planning.
  - `global_context`: Reference to the global context notebook.
  - `evaluator`: Instance of the evaluator class.

- **Methods:**
  - `plan(initial_state)`: Generates the execution graph using Q* learning.
  - `get_actions(state)`: Uses the LLM to decide among tools and nodes for the next action.
  - `update_rewards(state, action, reward)`: Updates the reward based on performance.
  - `optimize_node(node, sample_data)`: Calls the node's optimize method.

**2.3 Evaluator Class**

- **Description:** Specialized agent that enforces constrained decoding and evaluates node performance.

- **Attributes:**
  - `evaluation_criteria`: Defines how to assess accuracy.
  - `cutoff_step_size`: Determines when diminishing returns occur in optimization.

- **Methods:**
  - `evaluate(node_output, expected_output)`: Returns accuracy metrics.
  - `should_stop_optimization(accuracy_history)`: Determines if optimization should stop.

**2.4 GlobalContextNotebook Class**

- **Description:** Maintains embeddings and a knowledge base to track and reuse optimized subgraphs.

- **Attributes:**
  - `text_embeddings`: Embeddings of processed text data.
  - `knowledge_graph`: Graph-based knowledge representation of explored paths.
  - `optimized_subgraphs`: Cache of optimized subgraphs for reuse.

- **Methods:**
  - `update(state, node)`: Updates the notebook with new information.
  - `find_related_paths(state)`: Retrieves related paths that could be reused.
  - `prune()`: Removes ineffective or redundant workflows.

**2.5 Framework Inputs and Outputs**

- **Inputs (JSON):**
  - `role`: The agent role (e.g., 'coder', 'researcher').
  - `NODES`: List of available LLM nodes.
  - `DATA_PATH`: Path to data accessible to the agent.
  - `Context`: Additional context appended to the system prompt.
  - `GOAL`: The goal for the agent to optimize for.
  - `SupervisedData`: Path to supervised data for cost function.

- **Outputs (JSON):**
  - `ACHIEVED_GOAL`: `TRUE` or `FALSE`.
  - `UTILIZATION`: Instructions or artifacts on how to use the output (e.g., saved pickle object).
  - `FEEDBACK`: Additional information if the goal was not achieved.

**3. Workflow**

**3.1 Planning Phase**

- The planner receives the input JSON and initializes the planning process.
- It uses the large LLM to generate possible execution graphs within the complexity constraints.
- `get_actions` method is called to decide among tools and nodes for each state.
- The planner evaluates actions using the Q* algorithm to optimize the path towards the goal.

**3.2 Node Execution and Optimization**

- Nodes execute their `execute` method when reached.
- If the node is not optimized, the planner calls `optimize_node` to perform prompt optimization using `text grad`.
- The evaluator assesses the node's performance after each optimization step.
- When diminishing returns are detected, the node is marked as optimized and frozen.

**3.3 Updating Global Context**

- After each node execution, the global context notebook is updated.
- The notebook tracks embeddings and updates the knowledge graph.
- If related paths are found, the planner may reuse optimized subgraphs to improve efficiency.

**3.4 Completion and Output Generation**

- Once the goal is achieved or no further actions are possible, the planner generates the output JSON.
- If the goal is achieved, the planner provides utilization instructions.
- If not, feedback is provided to explain why the goal was not met.

**4. Edge Case Handling**

- **Cycles Prevention:** The planner ensures that the execution graph remains acyclic to prevent infinite loops.
- **Complexity Limits:** If the planner cannot generate a valid plan within the complexity constraints, it returns feedback indicating the issue.
- **Dynamic Routing:** Nodes with routing capabilities are carefully designed to avoid introducing cycles and to ensure termination.
- **Error Handling:** Nodes include exception handling to manage unexpected inputs or execution errors gracefully.

**5. Implementation Notes**

- **LLM Integration:** The `llm_model` attribute represents an instance of an LLM capable of generating text based on prompts. This can be an API call or a local model.

- **Text Grad Optimization:** The `adjust_prompt` method in `LLMNode` is a placeholder for implementing `text grad`, which adjusts the prompt to improve performance.

- **State Representation:** The `state` object used in the planner should encapsulate all necessary information to determine progress towards the goal, including context, history, and any intermediate results.

- **Action Representation:** Actions represent transitions in the execution graph, such as executing a node or routing to another node.

- **Concurrency and Asynchronicity:** Depending on the implementation, consider handling node executions asynchronously to improve efficiency.

**6. Edge Cases and Error Handling**

- **Invalid Inputs/Outputs:** Nodes should validate inputs and outputs against their schemas to prevent propagation of errors.

- **Optimization Failures:** If a node fails to optimize within the maximum steps, it should be marked accordingly, and the planner should decide whether to proceed or adjust the plan.

- **Resource Constraints:** The planner should monitor resource usage (e.g., API call limits, execution time) and adjust planning accordingly to stay within budget.

- **Unhandled Exceptions:** Implement robust exception handling throughout the framework to catch and manage unexpected errors.