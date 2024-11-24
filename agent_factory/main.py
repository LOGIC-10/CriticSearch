from agent import BaseAgent

agent = BaseAgent()
result= agent.parallel_search(["why do we say google was facing challenges in 2019?", "what are the challenges google faced in 2019?"])
formatted_result = agent.format_parallel_search_to_string(result)
print(formatted_result)
