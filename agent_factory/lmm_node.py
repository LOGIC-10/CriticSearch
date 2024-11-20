# File: agent_factory/lmm_node.py

import json
import logging
from typing import Any, Callable, Dict, Optional

import textgrad as tg

from .utils import call_llm, read_prompt_template, MAX_OPTIMIZATION_STEPS
from agent_factory.evaluator import evaluator

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class LLMNode:
    """
    Base class representing an LLM Node in the execution graph.
    Handles execution and optimization of prompts using LLMs and TextGrad.
    """

    def __init__(
        self,
        name: str,
        llm_model: str,
        prompt_template: str,
        config: Dict[str, Any],
        router: Optional[Callable[[Dict[str, Any]], str]] = None,
        input_schema: Optional[Dict[str, Any]] = None,
        output_schema: Optional[Dict[str, Any]] = None,
    ):
        """
        Initializes the LLMNode.

        :param name: Unique identifier for the node.
        :param llm_model: Identifier for the LLM model to be used.
        :param prompt_template: Template string for the LLM prompt.
        :param config: Configuration dictionary for LLM settings.
        :param router: Optional function to determine the next node based on state.
        :param input_schema: Optional schema to validate input data.
        :param output_schema: Optional schema to validate output data.
        """
        self.name = name
        self.llm_model = llm_model
        self.prompt_template = prompt_template
        self.config = config
        self.router = router
        self.input_schema = input_schema
        self.output_schema = output_schema
        self.optimized = False
        self.frozen = False
        self.optimizer = None  # To be initialized during optimization

        logger.info(f"Initialized LLMNode: {self.name}")

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the node's task using the LLM.

        :param input_data: Dictionary containing input data for the node.
        :return: Dictionary containing the output data.
        """
        if self.frozen:
            logger.warning(f"Node {self.name} is frozen. Skipping execution.")
            return {}

        try:
            # Validate input data
            if self.input_schema:
                self.validate_input(input_data)

            # Generate the prompt
            prompt = self.prompt_template.format(**input_data)
            logger.debug(f"Node {self.name} prompt: {prompt}")

            # Call the LLM using the helper function
            llm_response = call_llm(
                model=self.llm_model,
                sys_prompt=self.config.get("system_prompt", ""),
                usr_prompt=prompt,
                config=self.config,
            )
            logger.debug(f"Node {self.name} LLM response: {llm_response}")

            # Validate output data
            output_data = {"response": llm_response}
            if self.output_schema:
                self.validate_output(output_data)

            # Log successful execution
            logger.info(f"Node {self.name} executed successfully.")
            return output_data

        except Exception as e:
            logger.error(f"Error executing node {self.name}: {e}")
            return {"error": str(e)}

    def optimize(self, sample_data: Dict[str, Any], evaluator: 'Evaluator') -> None:
        """
        Optimizes the node's prompt using TextGrad.

        :param sample_data: Dictionary containing sample input and expected output.
        :param evaluator: Instance of the Evaluator class for assessing performance.
        """
        if self.optimized or self.frozen:
            logger.info(f"Node {self.name} is already optimized or frozen.")
            return

        try:
            logger.info(f"Starting optimization for node {self.name}.")

            # Initialize TextGrad variables
            tg.set_backward_engine(tg.get_engine(self.config.get("backward_engine", "gpt-4o")))
            prompt_variable = tg.Variable(
                self.prompt_template,
                requires_grad=True,
                role_description="prompt template for the LLM",
            )

            model = tg.BlackboxLLM(
                engine=self.llm_model,
                system_prompt=self.config.get("system_prompt", ""),
                prompt_variable=prompt_variable,
            )

            optimizer = tg.TGD(parameters=[prompt_variable])
            loss_instruction = tg.Variable(
                self.config.get("loss_instruction", "Evaluate the correctness of the response."),
                requires_grad=False,
                role_description="loss function instruction",
            )

            loss_fn = tg.TextLoss(loss_instruction)

            for step in range(MAX_OPTIMIZATION_STEPS):
                # Generate prediction
                prediction = model(sample_data['input'])
                logger.debug(f"Optimization step {step}: Prediction: {prediction}")

                # Compute loss
                loss = loss_fn(prediction)
                logger.debug(f"Optimization step {step}: Loss: {loss}")

                # Backward pass and optimizer step
                loss.backward()
                optimizer.step()

                # Evaluate performance
                accuracy = evaluator.evaluate(prediction, sample_data['expected_output'])
                logger.info(f"Optimization step {step}: Accuracy: {accuracy}")

                # Check if optimization should stop
                if evaluator.should_stop_optimization(accuracy):
                    logger.info(f"Stopping optimization for node {self.name} at step {step}.")
                    break

            # Update the prompt template with the optimized prompt
            self.prompt_template = prompt_variable.value
            self.optimized = True
            self.frozen = True  # Mark as frozen after optimization

            logger.info(f"Optimization completed for node {self.name}.")

        except Exception as e:
            logger.error(f"Error optimizing node {self.name}: {e}")

    def validate_input(self, input_data: Dict[str, Any]) -> None:
        """
        Validates the input data against the input schema.

        :param input_data: Dictionary containing input data.
        :raises: ValueError if validation fails.
        """
        try:
            # Placeholder for schema validation logic
            # Implement actual validation based on self.input_schema
            json_schema = self.input_schema
            if json_schema:
                # For example, using jsonschema library
                from jsonschema import validate, ValidationError

                validate(instance=input_data, schema=json_schema)
                logger.debug(f"Input data for node {self.name} is valid.")

        except ValidationError as ve:
            logger.error(f"Input validation error in node {self.name}: {ve}")
            raise ValueError(f"Input validation error: {ve}")

    def validate_output(self, output_data: Dict[str, Any]) -> None:
        """
        Validates the output data against the output schema.

        :param output_data: Dictionary containing output data.
        :raises: ValueError if validation fails.
        """
        try:
            # Placeholder for schema validation logic
            # Implement actual validation based on self.output_schema
            json_schema = self.output_schema
            if json_schema:
                from jsonschema import validate, ValidationError

                validate(instance=output_data, schema=json_schema)
                logger.debug(f"Output data for node {self.name} is valid.")

        except ValidationError as ve:
            logger.error(f"Output validation error in node {self.name}: {ve}")
            raise ValueError(f"Output validation error: {ve}")

    def adjust_prompt(self, new_prompt: str) -> None:
        """
        Adjusts the prompt template based on optimization feedback.

        :param new_prompt: The new prompt template.
        """
        if not self.frozen:
            self.prompt_template = new_prompt
            logger.info(f"Prompt for node {self.name} adjusted.")
        else:
            logger.warning(f"Cannot adjust prompt for node {self.name} as it is frozen.")

    def route(self, state: Dict[str, Any]) -> Optional[str]:
        """
        Determines the next node to execute based on the current state.

        :param state: Current state dictionary.
        :return: Name of the next node or None.
        """
        if self.router:
            try:
                next_node = self.router(state)
                logger.debug(f"Node {self.name} routing to {next_node}.")
                return next_node
            except Exception as e:
                logger.error(f"Routing error in node {self.name}: {e}")
                return None
        else:
            logger.debug(f"Node {self.name} has no router. No routing performed.")
            return None

class ConstrainedDecodingNode(LLMNode):
    """
    LLMNode subclass that enforces strict input and output types.
    Used for tasks requiring precise outputs.
    """

    def __init__(
        self,
        name: str,
        llm_model: str,
        prompt_template: str,
        config: Dict[str, Any],
        input_schema: Dict[str, Any],
        output_schema: Dict[str, Any],
    ):
        """
        Initializes the ConstrainedDecodingNode.

        :param name: Unique identifier for the node.
        :param llm_model: Identifier for the LLM model to be used.
        :param prompt_template: Template string for the LLM prompt.
        :param config: Configuration dictionary for LLM settings.
        :param input_schema: Schema to validate input data.
        :param output_schema: Schema to validate output data.
        """
        super().__init__(
            name=name,
            llm_model=llm_model,
            prompt_template=prompt_template,
            config=config,
            input_schema=input_schema,
            output_schema=output_schema,
        )

class SocraticRoutingNode(LLMNode):
    """
    LLMNode subclass that facilitates reasoning and dynamic routing.
    Can decide the next node(s) based on the current context.
    """

    def __init__(
        self,
        name: str,
        llm_model: str,
        prompt_template: str,
        config: Dict[str, Any],
        router: Callable[[Dict[str, Any]], str],
    ):
        """
        Initializes the SocraticRoutingNode.

        :param name: Unique identifier for the node.
        :param llm_model: Identifier for the LLM model to be used.
        :param prompt_template: Template string for the LLM prompt.
        :param config: Configuration dictionary for LLM settings.
        :param router: Function to determine the next node based on state.
        """
        super().__init__(
            name=name,
            llm_model=llm_model,
            prompt_template=prompt_template,
            config=config,
            router=router,
            input_schema=None,
            output_schema=None,
        )
