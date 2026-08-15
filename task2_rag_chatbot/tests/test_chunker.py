"""
Unit tests for recursive text chunker in Task 2.
"""
from app.chunker import split_text_recursive, create_document_chunks


def test_split_text_recursive_small():
    text = "Short text under chunk size limit."
    chunks = split_text_recursive(text, chunk_size=100, chunk_overlap=20)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_split_text_recursive_multiparagraph():
    text = (
        "Paragraph one discusses generative AI and transformer architectures.\n\n"
        "Paragraph two discusses vector databases and cosine similarity search algorithms.\n\n"
        "Paragraph three discusses local LLMs deployed on Ollama servers."
    )
    chunks = split_text_recursive(text, chunk_size=90, chunk_overlap=20)
    assert len(chunks) >= 2


def test_create_document_chunks_metadata():
    pages = [
        {"text": "Page one text content about executive leadership and roles.", "page_number": 1},
        {"text": "Page two text content about quarterly earnings and financial milestones.", "page_number": 2}
    ]
    chunks = create_document_chunks(pages, doc_id="doc-123", doc_name="report.pdf", chunk_size=80, chunk_overlap=15)
    assert len(chunks) >= 2
    assert chunks[0]["doc_id"] == "doc-123"
    assert chunks[0]["doc_name"] == "report.pdf"
    assert chunks[0]["page_number"] in [1, 2]
