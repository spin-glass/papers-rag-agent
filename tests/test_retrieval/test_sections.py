import pytest

from src.retrieval.sections import build_sections


def test_build_sections_with_numbered_headings():
    content = """Abstract

This is a test paper.

1 Introduction

Introduction content here.

2 Methods

Methods content here.

3 Results

Results content here.
"""
    
    result = build_sections(content)
    
    assert "sections" in result
    assert "toc_flat" in result
    
    sections = result["sections"]
    assert len(sections) >= 3
    
    assert sections[0]["title"] == "Abstract"
    assert "number" in sections[0]
    assert "start_offset" in sections[0]
    assert "end_offset" in sections[0]
    assert "snippet" in sections[0]
    
    toc = result["toc_flat"]
    assert "Abstract" in toc
    assert any("Introduction" in h for h in toc)


def test_build_sections_with_named_headings():
    content = """Abstract

Test abstract.

Introduction

Introduction text.

Methodology

Methods text.

Conclusion

Conclusion text.
"""
    
    result = build_sections(content)
    
    sections = result["sections"]
    toc = result["toc_flat"]
    
    assert len(sections) >= 4
    assert "Abstract" in toc
    assert "Introduction" in toc
    assert "Methodology" in toc
    assert "Conclusion" in toc


def test_build_sections_snippet_truncation():
    long_content = "Abstract\n\n" + "A" * 1000
    
    result = build_sections(long_content, max_snippet_len=100)
    
    sections = result["sections"]
    if sections:
        assert len(sections[0]["snippet"]) <= 100


def test_build_sections_empty_content():
    result = build_sections("")
    
    assert result["sections"] == []
    assert result["toc_flat"] == []


def test_build_sections_no_headings():
    content = "Just some plain text without any headings."
    
    result = build_sections(content)
    
    assert result["sections"] == []
    assert result["toc_flat"] == []
