"""
Unit tests for multi-format document loading in Task 2.
"""
from app.loader import load_txt_or_md_file, load_csv_file, load_document


def test_load_txt_file():
    content = b"This is a sample document about artificial intelligence.\nIt covers deep learning and neural networks."
    pages = load_txt_or_md_file(content, "ai_overview.txt")
    assert len(pages) == 1
    assert "artificial intelligence" in pages[0]["text"]
    assert pages[0]["file_name"] == "ai_overview.txt"


def test_load_csv_file():
    content = b"Name,Role,Department\nAlice Smith,VP of Engineering,Cloud\nBob Jones,Lead Scientist,AI"
    pages = load_csv_file(content, "employees.csv")
    assert len(pages) == 1
    assert "Alice Smith" in pages[0]["text"]
    assert "VP of Engineering" in pages[0]["text"]


def test_load_document_dispatcher():
    content = b"# Strategy Document\n\nQ3 Objectives: Deploy autonomous agents."
    pages = load_document(content, "strategy.md")
    assert len(pages) == 1
    assert "Strategy Document" in pages[0]["text"]
