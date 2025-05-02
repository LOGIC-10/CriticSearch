import ast
import json
import tiktoken
import re
from .rich_output import printer


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
    # 预处理文本
    response_text = response_text.strip()
    
    # 匹配两种可能的格式
    patterns = [
        # 匹配 <queries>List[str] = [...] </queries> 格式
        r'<queries>\s*List\[str\]\s*=\s*\[(.*?)\]\s*</queries>',
        # 匹配 <queries>[...] </queries> 格式
        r'<queries>\s*\[(.*?)\]\s*</queries>'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, response_text, re.DOTALL | re.IGNORECASE)
        if match:
            queries_str = match.group(1)
            # 处理查询列表
            queries = []
            # 使用正则表达式分割，考虑引号内的逗号
            parts = re.findall(r'"([^"]*?)"|\'([^\']*?)\'|([^,]+)', queries_str)
            for part in parts:
                # part是一个元组，包含三个捕获组，取非空的那个
                query = next((p.strip() for p in part if p.strip()), '')
                if query:
                    # 清理引号和多余空格
                    query = query.strip('"\'').strip()
                    if query:
                        queries.append(query)
            return queries
            
    return []

def extract_thought_from_response(response_text: str) -> str:
    """
    从响应文本中提取thought内容
    
    Args:
        response_text: 包含<thought>...</thought>格式的响应文本
        
    Returns:
        str: 提取的thought内容,如果未找到则返回空字符串
    """
    thought_pattern = r'<thought>(.*?)</thought>'
    thought_match = re.search(thought_pattern, response_text, re.DOTALL | re.IGNORECASE)
    if thought_match:
        return thought_match.group(1).strip()
    return ""

def extract_answer_from_response(response_text: str) -> str:
    """
    从响应文本中提取answer内容
    
    Args:
        response_text: 包含<answer>...</answer>格式的响应文本
        
    Returns:
        str: 提取的answer内容,如果未找到则返回空字符串
    """
    answer_pattern = r'<answer>(.*?)</answer>'
    answer_match = re.search(answer_pattern, response_text, re.DOTALL | re.IGNORECASE)
    if answer_match:
        return answer_match.group(1).strip()
    return ""

# 和上面的函数配合使用，上面是提取answer，下面是提取answer中的boxed内容
def extract_boxed_content(answer: str) -> str:
    """从答案中提取 boxed 内容
    
    Args:
        answer (str): 包含 boxed 内容的答案字符串，但是不包含answer的标签
    
    Returns:
        str: boxed中的内容,如果没有找到则返回原始答案
    """
    boxed_match = re.search(r"\\boxed{([^}]+)}", answer)
    return boxed_match.group(1).strip() if boxed_match else answer

def extract_citations(text: str) -> list:
    """
    从文本中提取所有 <citation>…</citation> 标签中的 URL，
    支持单个 URL 或者以 Python 列表形式包裹的多个 URL。

    Args:
        text: 包含 <citation>...</citation> 格式的文本

    Returns:
        list[str]: 按出现顺序提取的 citation 内容列表
    """
    pattern = r'<citation>(.*?)</citation>'
    matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)

    result = []
    for m in matches:
        content = m.strip()
        if not content:
            continue
        # 如果是列表形式，就解析成 Python list
        if content.startswith('[') and content.endswith(']'):
            try:
                # ast.literal_eval 只会执行字面量解析，比 eval 安全
                urls = ast.literal_eval(content)
                # 过滤并添加
                for u in urls:
                    if isinstance(u, str) and u.strip():
                        result.append(u.strip())
            except (SyntaxError, ValueError):
                # 解析失败时，退回当作普通字符串处理
                result.append(content)
        else:
            # 单个 URL 直接加入
            result.append(content)
    return result

def extract_notes(response_text: str) -> list:
    """
    从响应文本中提取notes列表
    
    Args:
        response_text: 包含<answer>[<note>...</note>]</answer>格式的响应文本
        
    Returns:
        list: 提取的notes列表,如果未找到则返回空列表
        要求返回的格式是：[
            "First note content with <citation>http://example1.com</citation>",
            "Second note content with <citation>http://example2.com</citation>"
        ]
    """
    # 只匹配格式完整的note内容
    note_pattern = r'<note>(.*?)</note>'
    matches = re.findall(note_pattern, response_text, re.DOTALL | re.IGNORECASE)
    valid_notes = []
    
    for note in matches:
        note = note.strip()
        # 验证笔记格式的完整性
        if (
            note 
            and "<citation>" in note 
            and "</citation>" in note
            and note.count("<citation>") == note.count("</citation>")
        ):
            valid_notes.append(note)
            
    return valid_notes

def extract_actions(text: str) -> set:
    """
    从文本中提取所有actions并去重
    
    Args:
        text: 包含<action>...</action>格式的文本
        
    Returns:
        set: 提取的action集合,如果未找到则返回空集合
    """
    actions = set()
    pattern = r'<action>(.*?)</action>'
    matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
    if matches:
        actions.update(match.strip() for match in matches)
    return actions

def extract_tag_content(text: str, tag: str) -> str:
    """
    通用的 <tag>…</tag> 提取函数
    
    Args:
        text: 包含指定标签的文本
        tag: 标签名称 (如 "question", "answer")
        
    Returns:
        str: 提取的标签内容，如果未找到则返回空字符串
    """
    pattern = rf'<{tag}>(.*?)</{tag}>'
    m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    return m.group(1).strip() if m else ""

def extract_and_validate_json(model_response: str):
    """
    Extract JSON content from a model response, whether it's wrapped in ```json``` fences
    or is just raw JSON text. Return the parsed object or None on failure.
    """
    # 1. Try to strip out any ```json``` fences (or ``` any-language ```)
    fence_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    m = re.search(fence_pattern, model_response, re.DOTALL | re.IGNORECASE)
    payload = m.group(1) if m else model_response
    payload = payload.strip()

    # 2. Attempt to parse as JSON
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        # 3. Fallback: remove any stray backticks and retry
        cleaned = payload.replace("```", "").strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            printer.print_exception(f"Invalid JSON content after cleanup: {exc}\n\n Original model content: {model_response}")
            return None

if __name__ == "__main__":

    text = "你好，世界！"
    print(count_tokens(text))  # 4