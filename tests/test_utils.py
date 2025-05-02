import pytest
from criticsearch.utils import extract_citations

def test_single_citation():
    text = "This is a test <citation>http://example.com</citation> end."
    assert extract_citations(text) == ["http://example.com"]

def test_multiple_citations_and_whitespace():
    text = (
        "Here are two:\n"
        "<citation>  https://foo.com/path  </citation>\n"
        "and\n"
        "<citation>\nhttps://bar.com\n</citation>"
    )
    assert extract_citations(text) == [
        "https://foo.com/path",
        "https://bar.com"
    ]

def test_duplicate_citations_are_preserved():
    text = (
        "<citation>dup</citation> first, then again <citation>dup</citation>"
    )
    # 目前实现不会去重，只保留出现顺序
    assert extract_citations(text) == ["dup", "dup"]

def test_no_citations_returns_empty_list():
    assert extract_citations("no tags here") == []