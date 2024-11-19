from queue import PriorityQueue


class Planner:
    def __init__(self, llm_model, goal, available_nodes, complexity, global_context, evaluator):
        self.llm_model = llm_model
        self.goal = goal
        self.available_nodes = available_nodes
        self.complexity = complexity
        self.global_context = global_context
        self.evaluator = evaluator

    def plan(self, initial_state):
        # Implement Q* algorithm with LLM-based get_actions
        open_set = PriorityQueue()
        open_set.put((0, initial_state))
        came_from = {}
        cost_so_far = {initial_state: 0}

        while not open_set.empty():
            _, current_state = open_set.get()

            if self.is_goal(current_state):
                return self.reconstruct_path(came_from, current_state)

            actions = self.get_actions(current_state)
            for action in actions:

                # use the transition agent to get the next action node
                next_state = self.transition(current_state, action)
                # generate a reward function based off of optimization of that path
                reward = self.evaluator.evaluate_action(current_state, action)
                new_cost = cost_so_far[current_state] - reward  # Negative reward as cost

                if next_state not in cost_so_far or new_cost < cost_so_far[next_state]:
                    cost_so_far[next_state] = new_cost
                    priority = new_cost + self.heuristic(next_state)
                    open_set.put((priority, next_state))
                    came_from[next_state] = (current_state, action)
        return None  # No valid plan found

    def get_actions(self, state):
        # Use the LLM to decide among tools and nodes
        prompt = self.generate_action_prompt(state)
        action_descriptions = self.llm_model.generate(prompt)
        actions = self.parse_actions(action_descriptions)
        return actions

    def transition(self, state, action):
        # Apply action to state to get next state
        pass

    def is_goal(self, state):
        # Determine if the goal has been achieved
        return state.meets_goal(self.goal)

    def heuristic(self, state):
        # Estimate cost to reach goal from current state
        pass

    def reconstruct_path(self, came_from, current_state):
        # Reconstruct the path from start to goal
        pass

    def generate_action_prompt(self, state):
        # Generate prompt for the LLM to decide actions
        pass

    def parse_actions(self, action_descriptions):
        # Parse LLM output into actionable items
        pass
