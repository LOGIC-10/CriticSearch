
from openai import APIConnectionError, OpenAI


def read_prompt_template(file_path):
  with open(file_path, 'r') as file:
    prompt = file.read()
  return prompt


def call_llm(model, sys_prompt, usr_prompt, config):

    client = OpenAI(
        api_key=config.get("models").get(model).get("api_key"),
        base_url=config.get("models").get(model).get("base_url"),
        timeout=config.get("timeout"),
        max_retries=config.get("max_retries"),
    )

    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": usr_prompt},
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=config.get("temperature"),
        # max_tokens=config.get("models").get(model).get("max_tokens","8192"),
    )

    response_message = response.choices[0].message

    return response_message.content