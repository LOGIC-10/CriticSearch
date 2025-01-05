# %%
from llm import query_perplexity

query = (
    "At which university does the biographer of John Clare teach English Literature?"
)
answer = query_perplexity(question=query)
print(answer)

# %%
from llm import query_evaluator

query = (
    "At which university does the biographer of John Clare teach English Literature?"
)
answer = "The biographer of John Clare, Jonathan Bate, teaches English Literature at the University of Oxford. Specifically, he is Professor of English Literature at the University of Oxford and also serves as the Provost of Worcester College, Oxford[1][2][3]."
gold = "University of Oxford"
int(query_evaluator(question=query, model_answer=answer, ground_truth=gold))

# %%
from criticsearch import run_tasks

query = [
    "At which university does the biographer of John Clare teach English Literature?"
]
answer = run_tasks(query, max_iterations=3)
print(answer)

# %%
