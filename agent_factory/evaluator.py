# Specialized agent for handling node verification, validation, and performance

class Evaluator:
    def __init__(self, evaluation_criteria, cutoff_step_size):
        self.evaluation_criteria = evaluation_criteria
        self.cutoff_step_size = cutoff_step_size

    def evaluate(self, node_output, expected_output):
        # Compare node_output to expected_output based on criteria
        pass

    def should_stop_optimization(self, accuracy_history):
        # Determine if optimization should stop based on diminishing returns
        if len(accuracy_history) < 2:
            return False
        return (accuracy_history[-1] - accuracy_history[-2]) < self.cutoff_step_size

    def evaluate_action(self, state, action):
        # Evaluate the action's expected reward
        pass