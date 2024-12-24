from .base_agent import BaseAgent
from .main import main

if __name__ == "__main__":
    MAX_ITERATION = 5

    Task = """Which interdisciplinary scholar, renowned for their contributions to both artificial intelligence and neuroethics, currently holds a faculty position in the Department of Cognitive Science at a university, and has co-authored a seminal paper on the ethical implications of AI in medical decision-making?"""
   
    main(Task, MAX_ITERATION)

    BaseAgent.conversation_manager.write(
        data=BaseAgent.conversation_manager.model_dump(context={"sharegpt": True}),
        path="conversation_history_sharegpt.jsonl",
    )
