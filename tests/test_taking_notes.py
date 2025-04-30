
import pytest
from criticsearch.base_agent import BaseAgent
from criticsearch.utils import extract_notes

def test_extract_notes():
    # 测试基本的note提取功能
    test_response = """
    <answer>[
        "<note>First note content with <citation>http://example1.com</citation></note>",
        "<note>Second note content with <citation>http://example2.com</citation></note>"
    ]</answer>
    """
    notes = extract_notes(test_response)
    assert len(notes) == 2
    assert "First note content with <citation>http://example1.com</citation>" in notes
    assert "Second note content with <citation>http://example2.com</citation>" in notes

def test_taking_notes_integration():
    # 测试完整的taking notes功能
    agent = BaseAgent()
    agent.receive_task("Test task")
    
    # 模拟搜索结果
    test_web_results = """
    Some search results about the topic...
    Source: http://example1.com
    Content: Important information 1
    
    Source: http://example2.com
    Content: Important information 2
    """
    
    # 第一次添加笔记
    agent.taking_notes(test_web_results)
    first_memo_size = len(agent.memo)
    assert first_memo_size > 0, "Should have added notes to memo"
    
    # 再次添加相同的笔记
    agent.taking_notes(test_web_results)
    second_memo_size = len(agent.memo)
    assert second_memo_size == first_memo_size, "Should not add duplicate notes"
    
    # 验证memo中的内容格式
    for note in agent.memo:
        assert "<note>" not in note, "Raw note should not contain <note> tags"
        assert "</note>" not in note, "Raw note should not contain </note> tags"
        assert "<citation>" in note, "Note should contain citation"
        assert "</citation>" in note, "Note should contain citation"

def test_empty_notes():
    # 测试空的笔记情况
    test_response = "<answer>[]</answer>"
    notes = extract_notes(test_response)
    assert len(notes) == 0

def test_malformed_notes():
    # 测试格式不正确的笔记
    test_response = """
    <answer>[
        "<note>Incomplete note
        "note>Another incomplete note</note>"
    ]</answer>
    """
    notes = extract_notes(test_response)
    assert len(notes) == 0

if __name__ == "__main__":
    pytest.main([__file__])