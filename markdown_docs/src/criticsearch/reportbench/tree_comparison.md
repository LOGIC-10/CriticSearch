## FunctionDef parse_tree(node, current_depth, levels)
**parse_tree**: The function of parse_tree is to recursively parse a tree-like data structure and organize its elements by their depth level.

**parameters**: The parameters of this Function.
- node: A dictionary representing a node in the tree, which may contain a 'title' and optionally 'children', a list of child nodes.
- current_depth: An integer representing the current depth level in the tree being parsed. It defaults to 0.
- levels: A defaultdict of lists used to store the titles of nodes grouped by their depth levels. It defaults to None.

**Code Description**: The `parse_tree` function processes a tree-like structure represented by a nested dictionary. It starts at a given node (the root of the tree) and recursively explores all its descendants, accumulating the titles of nodes at each depth level.

- If the `levels` parameter is not provided, it initializes it as a `defaultdict` to store lists, which will hold the titles of nodes at different depths.
- If the node has a 'title', it adds that title to the list corresponding to its current depth (`current_depth`).
- If the node has a 'children' key, the function recursively calls itself on each child node, increasing the depth by 1.
- The function eventually returns the `levels` dictionary, which maps each depth level to a list of titles of nodes at that level.

This function is utilized by the `tree_similarity` function to process and compare two tree-like structures (`std_tree` and `student_tree`). It is called on both the standard tree and the student tree to build depth-based structures of node titles. These structures are then used to calculate the semantic similarity between nodes at corresponding depths, as well as to compute penalties based on the number of nodes at each level. 

**Note**: This function assumes that nodes are represented as dictionaries, each potentially containing a 'title' and 'children' key. It is important that the input tree structures follow this format for the function to operate correctly. 

**Output Example**: 
For a tree like:

```
{
  'title': 'Root',
  'children': [
    {'title': 'Child 1', 'children': []},
    {'title': 'Child 2', 'children': [{'title': 'Grandchild 1', 'children': []}]}
  ]
}
```

The output of the `parse_tree` function would be:

```
{
  0: ['Root'],
  1: ['Child 1', 'Child 2'],
  2: ['Grandchild 1']
}
```
## FunctionDef text_similarity(text1, text2)
**text_similarity**: The function of text_similarity is to compute the similarity between two text inputs using natural language processing (NLP) techniques.

**parameters**:
· text1: A string containing the first text to be compared.
· text2: A string containing the second text to be compared.

**Code Description**:  
The `text_similarity` function calculates the similarity between two given text inputs (`text1` and `text2`). This is achieved by processing each text input using a natural language processing model (`nlp`), which converts the text into a document object. The `similarity` method of the `spacy` document object is then used to compute a similarity score, which ranges from 0 to 1, where 1 indicates identical content and 0 indicates no similarity. This function returns the similarity score between the two documents.

In the broader context of the project, the `text_similarity` function is invoked by the `level_similarity` function. The `level_similarity` function uses `text_similarity` to compute a similarity matrix between two sets of nodes (`nodes_A` and `nodes_B`). These nodes are presumably elements in some data structure, and `level_similarity` calculates the overall similarity between two groups of nodes by comparing each pairwise combination of nodes. The `text_similarity` function is called within nested loops iterating over these nodes, and its output is used to populate a similarity matrix. Once the matrix is constructed, the `linear_sum_assignment` function is applied to optimize the assignment of nodes based on the similarity values, and the final similarity score is computed by summing the similarities of the assigned pairs.

Thus, `text_similarity` serves as a key component for comparing individual nodes at the text level within the `level_similarity` function, which ultimately computes a similarity score between entire groups of nodes.

**Note**:  
- The `text_similarity` function assumes that the `nlp` model (likely a `spaCy` model) has already been initialized before being called.
- Both `text1` and `text2` must be valid text strings. If either of them is empty or malformed, the function may not behave as expected.
- The returned similarity score is a floating-point number between 0 and 1, with higher values indicating greater textual similarity.

**Output Example**:  
For example, if `text1` is "Hello, how are you?" and `text2` is "Hi, how are you doing?", the function might return a similarity score like `0.89`, indicating that the two texts are highly similar, but not identical.
## FunctionDef level_similarity(nodes_A, nodes_B)
**level_similarity**: The function of level_similarity is to compute the similarity score between two sets of nodes based on their textual content.

**parameters**: 
· nodes_A: A list of nodes representing the first group of elements to be compared. Each node is expected to contain textual content.  
· nodes_B: A list of nodes representing the second group of elements to be compared. Each node is also expected to contain textual content.

**Code Description**: The `level_similarity` function calculates a similarity score between two groups of nodes, `nodes_A` and `nodes_B`, by utilizing a similarity matrix derived from the textual content of each node. Initially, the function checks if both input lists are empty; if so, it returns a similarity score of 1.0, indicating a perfect match due to the absence of nodes. 

Next, a similarity matrix is created with dimensions corresponding to the lengths of `nodes_A` and `nodes_B`. The function then iterates through each node in `nodes_A` and `nodes_B`, calculating the textual similarity between each pair of nodes using the `text_similarity` function. This function employs natural language processing techniques to derive a similarity score for each pair, which is stored in the similarity matrix.

After populating the matrix, the function applies the `linear_sum_assignment` method from the SciPy library to find the optimal assignment of nodes that maximizes the total similarity score. The total similarity score is computed by summing the values in the similarity matrix corresponding to the optimal assignments. Finally, the function normalizes this score by dividing it by the maximum possible value, which is determined by the larger of the two input lists' lengths. If both lists are non-empty, the function returns the computed similarity score; otherwise, it returns 0.

The `level_similarity` function is called by the `tree_similarity` function, which is responsible for comparing two hierarchical tree structures. Within `tree_similarity`, the function first parses the trees into levels and then computes the similarity for each level using `level_similarity`. This integration allows `tree_similarity` to assess the overall structural and semantic similarity between two trees by evaluating their respective levels.

**Note**: 
- The `text_similarity` function, which is called within `level_similarity`, must be properly initialized with a natural language processing model before use.
- Both `nodes_A` and `nodes_B` should contain valid text nodes; otherwise, the function may not yield meaningful results.
- The returned similarity score is a floating-point number between 0 and 1, where higher values indicate greater similarity between the two sets of nodes.

**Output Example**: For instance, if `nodes_A` contains ["Node A1", "Node A2"] and `nodes_B` contains ["Node B1", "Node B2"], the function might return a similarity score of `0.75`, indicating a moderate level of similarity between the two groups of nodes.
## FunctionDef tree_similarity(std_tree, student_tree, depth_decay, alpha, beta, gamma)
**tree_similarity**: The function of tree_similarity is to calculate the semantic and structural similarity score between two hierarchical tree structures.

**parameters**: The parameters of this Function.
- **std_tree**: A dictionary representing the standard tree structure, which is compared against the student's tree structure.
- **student_tree**: A dictionary representing the student's tree structure, which is compared to the standard tree structure.
- **depth_decay**: A float (default is 0.8) that determines the decay factor for the weight assigned to each tree depth. Deeper levels of the tree are given higher weights.
- **alpha**: A float (default is 0.3) used in the penalty calculation for the difference in the number of nodes between corresponding levels of the trees.
- **beta**: A float (default is 0.02) that penalizes missing layers in the student's tree compared to the standard tree.
- **gamma**: A float (default is 0.02) that penalizes redundant layers in the student's tree compared to the standard tree.

**Code Description**: 
The `tree_similarity` function computes the overall similarity between two tree structures, `std_tree` and `student_tree`. It does so by first parsing both trees into levels using the `parse_tree` function. This process groups the nodes in each tree by their depth level. Then, the function compares these corresponding levels of the two trees by computing their semantic similarity using the `level_similarity` function. It also calculates penalties based on the differences in the number of nodes at each level and the presence of missing or redundant levels in the student's tree.

The function proceeds through the following steps:

1. **Tree Parsing**: The two input trees (`std_tree` and `student_tree`) are parsed into levels using the `parse_tree` function. This gives each tree a dictionary mapping depth levels to lists of nodes at those depths.

2. **Depth Calculation**: The function determines the maximum depth among the two trees, which will be the range of depths that the function iterates over. The comparison will be done from depth 0 up to the maximum depth in either tree.

3. **Iterative Comparison**: The function iterates over each depth level from 0 to the maximum depth. For each depth:
   - It checks if the current depth exists in both trees. If a depth exists in one tree but not the other, it counts as either a missing or redundant layer, depending on which tree lacks the depth.
   - The function calculates a weight for the depth based on the `depth_decay` factor. Deeper levels of the tree receive a higher weight.
   - For corresponding depths that exist in both trees, the function calculates the semantic similarity between the nodes at that level using the `level_similarity` function.
   - A penalty is applied for discrepancies in the number of nodes at each depth. If the number of nodes differs between the two trees, a penalty is computed based on the `alpha` factor, which reduces the structure's similarity score.

4. **Final Score Calculation**: After comparing all depths:
   - The function computes a weighted average of the similarity scores at each depth, adjusting for missing or redundant layers in the student's tree using the `beta` and `gamma` penalties.
   - The final score is computed by applying the structure penalty to the weighted average score.

The output is a final similarity score between the two trees, rounded to two decimal places. This score reflects how closely the student's tree structure matches the standard tree both semantically and structurally.

The `tree_similarity` function is used in the `evaluate_breadth` method of the `ReportEvaluation` class, which evaluates the similarity between the standard and student trees. The standard tree is fetched from `self.report_benchmark.breadth_gt`, and the student's tree is generated using `self.examinees_outline_generation()`. The resulting similarity score is returned as part of the evaluation process.

**Note**:
- The `parse_tree` function, which is called by `tree_similarity`, is responsible for parsing the tree structure and organizing it by depth levels.
- The `level_similarity` function, which is used to calculate semantic similarity at each level, relies on comparing the nodes' textual content to compute a similarity score.
- The parameters `depth_decay`, `alpha`, `beta`, and `gamma` influence how heavily the function weighs different aspects of the tree comparison, including the depth of nodes and the penalties for missing or redundant layers.
- The returned score is a floating-point value between 0 and 1, with higher values indicating a closer match between the two trees.
