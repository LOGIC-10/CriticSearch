import pytest
from criticsearch.utils import extract_citations

@pytest.mark.parametrize("input_text, expected", [
    # 无 citation
    ("This is a text without citations.", []),
    # 单个 citation
    ("Some info <citation>http://example.com</citation> end.", ["http://example.com"]),
    # 多个不同 citation
    ("A<citation>https://a.com</citation>B and <citation>https://b.com</citation>.", ["https://a.com", "https://b.com"]),
    # 重复 citation，只保留第一次
    ("X<citation>dup.com</citation>Y<citation>dup.com</citation>Z", ["dup.com"]),
    # 包含空白与换行
    ("<citation>\n https://newline.com \n</citation>", ["https://newline.com"]),
    # 忽略大小写标签
    ("<CITATION>UpCase.com</CITATION>", ["UpCase.com"]),
])
def test_extract_citations(input_text, expected):
    assert extract_citations(input_text) == expected

if __name__ == "__main__":
    pytest.main(["-q", __file__])