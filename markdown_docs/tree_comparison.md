## FunctionDef parse_tree(node, current_depth, levels)
**parse_tree**: The function of parse_tree is to recursively traverse a tree structure and organize its titles by their respective depth levels.

**parameters**: The parameters of this Function.
· parameter1: node - A dictionary representing a node in the tree, which may contain a 'title' and a list of 'children'.
· parameter2: current_depth - An integer indicating the current depth level in the tree during traversal, defaulting to 0.
· parameter3: levels - A defaultdict that stores lists of titles indexed by their depth levels, defaulting to None.

**Code Description**: The parse_tree function is designed to process a hierarchical tree structure represented as a nested dictionary. It begins by checking if the levels parameter is None, in which case it initializes it as a defaultdict of lists. The function then checks if the current node contains a 'title'; if so, it appends this title to the list corresponding to the current depth in the levels dictionary. If the node has children, the function recursively calls itself for each child, incrementing the current_depth by one. This process continues until all nodes in the tree have been processed, resulting in a structured representation of the titles organized by their depth levels.

The parse_tree function is called within the tree_similarity function, where it is used to extract and organize the titles from two different tree structures: std_tree and student_tree. By calling parse_tree on both trees, tree_similarity can compare the hierarchical structures and compute a similarity score based on the presence and arrangement of titles at various depths. This integration allows for a comprehensive analysis of how closely the student's tree resembles the standard tree, taking into account both semantic and structural differences.

**Note**: It is important to ensure that the input node is structured correctly, containing 'title' and 'children' keys where applicable, to avoid unexpected behavior during traversal.

**Output Example**: For a given input tree structure like:
{
    'title': 'Root',
    'children': [
        {'title': 'Child 1', 'children': []},
        {'title': 'Child 2', 'children': [
            {'title': 'Grandchild 1', 'children': []}
        ]}
    ]
}
The output of parse_tree would be:
{
    0: ['Root'],
    1: ['Child 1', 'Child 2'],
    2: ['Grandchild 1']
}
## FunctionDef text_similarity(text1, text2)
**text_similarity**: The function of text_similarity is to compute the similarity score between two text inputs.

**parameters**: The parameters of this Function.
· parameter1: text1 - A string representing the first text input for comparison.
· parameter2: text2 - A string representing the second text input for comparison.

**Code Description**: The text_similarity function utilizes a natural language processing (NLP) model (referred to as `nlp`) to analyze and compare two text strings, text1 and text2. It processes each text input into a document object using the NLP model, which allows for semantic analysis. The function then calculates and returns a similarity score between the two document objects using the built-in similarity method. This score is a floating-point number that indicates how similar the two texts are, with a value closer to 1.0 indicating high similarity and a value closer to 0 indicating low similarity.

The text_similarity function is called within the level_similarity function, which is responsible for comparing two sets of nodes (nodes_A and nodes_B). In level_similarity, a similarity matrix is constructed where each element represents the similarity score between corresponding nodes from the two sets, calculated using the text_similarity function. The linear_sum_assignment function is then used to find the optimal assignment of nodes that maximizes the total similarity score. The final output of level_similarity is the average similarity score, which is derived from the total similarity of the best matches divided by the maximum possible matches.

**Note**: It is important to ensure that the NLP model (`nlp`) is properly initialized and available in the scope where text_similarity is called. The quality of the similarity score is highly dependent on the capabilities of the NLP model being used.

**Output Example**: For example, if text1 is "The cat sits on the mat." and text2 is "A cat is resting on a mat.", the function might return a similarity score of approximately 0.85, indicating a high degree of similarity between the two sentences.
## FunctionDef level_similarity(nodes_A, nodes_B)
**level_similarity**: The function of level_similarity is to compute a similarity score between two sets of nodes based on the text similarity of their elements.

**parameters**: The parameters of this Function.
· parameter1: nodes_A - A list of nodes representing the first set of elements for comparison.
· parameter2: nodes_B - A list of nodes representing the second set of elements for comparison.

**Code Description**: The level_similarity function is responsible for computing the similarity between two sets of nodes, `nodes_A` and `nodes_B`. It begins by handling the case where both input sets are empty, in which case it returns a similarity score of 1.0, indicating perfect similarity. If either set is non-empty, the function proceeds to create a similarity matrix, `sim_matrix`, where each element represents the similarity score between corresponding nodes from `nodes_A` and `nodes_B`. These similarity scores are computed by calling the `text_similarity` function for each pair of nodes.

The `text_similarity` function (described separately) computes the semantic similarity between two individual nodes based on natural language processing techniques. This function is called for every pair of nodes between `nodes_A` and `nodes_B`, filling the similarity matrix with the results.

Once the similarity matrix is populated, the function uses the `linear_sum_assignment` algorithm to find the optimal assignment of nodes that maximizes the total similarity. This algorithm solves the assignment problem in which the goal is to match nodes in a way that maximizes the sum of similarity scores.

After determining the optimal assignment, the function sums up the similarity scores of the best matches and divides the total by the maximum number of nodes between `nodes_A` and `nodes_B`. This division normalizes the result, ensuring that the final similarity score is in the range [0, 1], where 1 represents perfect similarity, and 0 represents no similarity.

The `level_similarity` function is called within the `tree_similarity` function, which compares two hierarchical tree structures (a standard tree and a student's tree). The `tree_similarity` function calls `level_similarity` to evaluate the similarity between corresponding levels in the two trees. This allows for the comparison of tree structures at each level and the calculation of an overall similarity score between the two trees.

**Note**: The behavior of `level_similarity` is highly dependent on the implementation of the `text_similarity` function, which must be properly initialized with a natural language processing model to accurately compute the similarity between text-based nodes.

**Output Example**: If `nodes_A` is a list containing ["apple", "banana"] and `nodes_B` is a list containing ["apple", "orange"], the `text_similarity` function might return similarity scores like 1.0 for "apple" and "apple", and 0.6 for "banana" and "orange". The function would then compute the optimal assignment and return a similarity score based on these values. The final output might be a value such as 0.8, indicating a moderate similarity between the two sets.
## FunctionDef tree_similarity(std_tree, student_tree, depth_decay, alpha, beta, gamma)
**tree_similarity**: The function of tree_similarity is to calculate a similarity score between two tree structures based on their hierarchical and semantic alignment.

**parameters**: The parameters of this Function.
· parameter1: std_tree - A tree structure representing the standard tree to be compared against.
· parameter2: student_tree - A tree structure representing the student's tree that is being evaluated.
· parameter3: depth_decay (default=0.8) - A factor that controls the weight assigned to different tree levels. Deeper levels receive higher weights.
· parameter4: alpha (default=0.3) - A factor that penalizes differences in the number of nodes between two corresponding levels.
· parameter5: beta (default=0.02) - A penalty applied for missing layers in the student's tree compared to the standard tree.
· parameter6: gamma (default=0.02) - A penalty applied for redundant layers in the student's tree that are not present in the standard tree.

**Code Description**: The `tree_similarity` function calculates the similarity between two hierarchical tree structures (the standard tree and the student's tree). The function first parses both trees to organize them into hierarchical levels using the `parse_tree` function. This function returns dictionaries where the keys represent tree depths, and the values are lists of node titles at each depth level.

The comparison starts by determining the maximum depth across both trees. It then iterates through each possible depth level, from 0 to the maximum depth, and compares the two trees at each level. For each level, the function checks if the level exists in both trees. If a level is missing in the student's tree, a "missing layer" penalty is incremented. Conversely, if a level exists in the student's tree but not the standard tree, a "redundant layer" penalty is counted. These penalties influence the final similarity score.

For each level where both trees have corresponding nodes, the function calculates a semantic similarity score using the `level_similarity` function. The `level_similarity` function compares nodes from both trees based on their textual similarity, leveraging a text similarity algorithm. Additionally, the number of nodes at each level is compared, and a penalty is applied for any difference in node count, weighted by the `alpha` factor.

The final similarity score is a weighted average of the scores across all levels, where deeper levels have more influence due to the `depth_decay` factor. The total score is adjusted with penalties for missing or redundant layers. If no valid layers are found, the function returns a score of 0.

The function serves as a key component of the broader evaluation process, which involves comparing a student's tree to a standard tree. The `tree_similarity` function is invoked in the `evaluate_breadth` method of the `ReportEvaluation` class. This method generates a student's tree, compares it to a benchmark tree (which serves as the "standard"), and returns the calculated similarity score.

**Note**: It is crucial that both the standard and student trees are structured consistently for accurate results. Each node should contain a 'title' and optionally a 'children' key, which will be used by the `parse_tree` function to process the hierarchical structure.

**Output Example**: 
For input trees with the following structure:

- Standard Tree:
  ```
  {
    'title': 'Root',
    'children': [
      {'title': 'Child 1', 'children': []},
      {'title': 'Child 2', 'children': [
        {'title': 'Grandchild 1', 'children': []}
      ]}
    ]
  }
  ```

- Student Tree:
  ```
  {
    'title': 'Root',
    'children': [
      {'title': 'Child 1', 'children': []},
      {'title': 'Child 3', 'children': []}
    ]
  }
  ```

The function would compare the trees and return a similarity score (e.g., 0.75), reflecting the degree of structural and semantic alignment between the two trees. The returned score is rounded to two decimal places.
