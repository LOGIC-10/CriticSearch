import tiktoken
import re

def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """
    Calculate the number of tokens in a text string.
    
    Args:
        text: The text to tokenize
        model: The model to use for tokenization (default: "gpt-3.5-turbo")
            Some common options: "gpt-3.5-turbo", "gpt-4", "text-embedding-ada-002"
    
    Returns:
        int: The number of tokens in the text
    
    Example:
        >>> count_tokens("Hello, world!")
        4
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        # Fall back to cl100k_base encoding if model not found
        encoding = tiktoken.get_encoding("cl100k_base")
    
    return len(encoding.encode(text))

def extract_queries_from_response(response_text: str) -> list:
    """
    从响应文本中提取查询列表
    
    Args:
        response_text: 包含<\queries>[...]<\queries>格式的响应文本
        
    Returns:
        list: 提取的查询列表,如果未找到则返回空列表
    """
    queries_pattern = r'<\\queries>\[(.*?)\]<\\queries>'
    queries_match = re.search(queries_pattern, response_text, re.DOTALL)
    if queries_match:
        queries_str = queries_match.group(1)
        # 将字符串转换为Python列表
        return [q.strip().strip('"\'') for q in queries_str.split(',')]
    return []

def extract_thought_from_response(response_text: str) -> str:
    """
    从响应文本中提取thought内容
    
    Args:
        response_text: 包含<\thought>...<\thought>格式的响应文本
        
    Returns:
        str: 提取的thought内容,如果未找到则返回空字符串
    """
    thought_pattern = r'<\\thought>(.*?)<\\thought>'
    thought_match = re.search(thought_pattern, response_text, re.DOTALL)
    if thought_match:
        return thought_match.group(1).strip()
    return ""

def extract_answer_from_response(response_text: str) -> str:
    """
    从响应文本中提取answer内容
    
    Args:
        response_text: 包含<\answer>...<\answer>格式的响应文本
        
    Returns:
        str: 提取的answer内容,如果未找到则返回空字符串
    """
    answer_pattern = r'<\\answer>(.*?)<\\answer>'
    answer_match = re.search(answer_pattern, response_text, re.DOTALL)
    if answer_match:
        return answer_match.group(1).strip()
    return ""

def extract_citations(text: str) -> set:
    """
    从文本中提取所有引用的URLs并去重
    
    Args:
        text: 包含<\citation>URL<\citation>格式的文本
        
    Returns:
        set: 提取的URL集合,如果未找到则返回空集合
    """
    citations = set()
    pattern = r'<\\citation>(.*?)<\\citation>'
    matches = re.findall(pattern, text)
    if matches:
        citations.update(matches)
    return citations

if __name__ == "__main__":

    text = "你好，世界！"
    print(count_tokens(text))  # 4