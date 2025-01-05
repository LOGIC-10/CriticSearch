import os
from typing import Optional

from openai import OpenAI


def chat_with_ai(api_key: str, model: str, messages, base_url: Optional[str] = None):
    client = OpenAI(api_key=api_key, base_url=base_url)
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
    )
    return completion.choices[0].message.content


def query_evaluator(question, ground_truth, model_answer, model="gpt-4o"):
    """
    Evaluate a model's answer to a question against a ground truth answer with default model Openai's gpt-4o.
    """

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY is not set in the environment variables."
        )

    messages = [
        {
            "role": "system",
            "content": (
                "You are a reasoning assistant. You are given a question, a ground truth answer, "
                "and a model's answer. You must determine if the model's answer fully and "
                "correctly answers the question according to the ground truth. "
                "If it does, respond with 'True'. If not, respond with 'False'. No explanations, elaborations, or additional information please."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Question: {question}\n"
                f"Ground Truth: {ground_truth}\n"
                f"Model Answer: {model_answer}\n\n"
                "Does the model answer match the ground truth fully and correctly?"
            ),
        },
    ]

    return chat_with_ai(api_key=api_key, model=model, messages=messages)


def query_perplexity(question, model="llama-3.1-sonar-small-128k-online"):
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "PERPLEXITY_API_KEY is not set in the environment variables."
        )

    base_url = "https://api.perplexity.ai"
    messages = [
        {
            "role": "system",
            "content": (
                "You are a reasoning assistant. You are given a question, a ground truth answer, "
                "and a model's answer. You must determine if the model's answer fully and "
                "correctly answers the question according to the ground truth. "
                "If it does, respond with 'True'. If not, respond with 'False'. No explanations, elaborations, or additional information please."
            ),
        },
        {"role": "user", "content": question},
    ]

    return chat_with_ai(
        api_key=api_key, base_url=base_url, model=model, messages=messages
    )
