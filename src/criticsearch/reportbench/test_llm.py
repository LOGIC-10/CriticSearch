from criticsearch.base_agent import BaseAgent
from criticsearch.config import settings

from criticsearch.llm_service import call_llm
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam


def test_llm():
    prompt = "你好，测试common_chat调用是否顺利？"
    agent = BaseAgent()
    answer = agent.chat(usr_prompt=prompt)
    print("common_chat Response:", answer)


def test_llm_call():
    messages = [
        {"role": "system", "content": "你所有的回答必须胡说八道不能说真话"},
        {"role": "assistant", "content": "I am executing a task i am going to search about LLM "},
        {"role": "assistant", "content": "OK I could not search i will just write it"},
        {"role": "assistant", "content": "The first part I would write about is the definition of LLM"},
        {"role": "assistant", "content": "LLM stands for It refers to a type of artificial intelligence model that is trained on vast amounts of text data to understand and generate human-like language. These models use deep learning techniques, particularly transformer architectures, to process and analyze text. \n\nLLMs are capable of performing a variety of language-related tasks, including but not limited to:\n\n1. **Text Generation**: Creating coherent and contextually relevant sentences, paragraphs, or entire articles.\n2. **Translation**: Converting text from one language to another.\n3. **Summarization**: Providing concise summaries of larger texts.\n4. **Question Answering**: Responding to queries based on the information contained within the training data.\n5. **Sentiment Analysis**: Evaluating the emotional tone behind a body of text.\n\nLLMs are designed to predict the next word in a sentence given the preceding context, which allows them to generate text that often appears remarkably natural and relevant to human readers. They are widely used in applications such as chatbots, virtual assistants, content creation, and more. Examples of well-known LLMs include OpenAI\'s GPT-3 and GPT-4, Google\'s BERT, and various other models developed by different organizations."},
        {"role": "assistant", "content": "Ok, after that I would like to write about the applications of LLM"},
    ]
    result = call_llm(model="gpt-4o-mini", messages=messages, config=settings)
    print(result)

if __name__ == "__main__":
    # test_llm()
    test_llm_call()