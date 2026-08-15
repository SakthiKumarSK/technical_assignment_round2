"""
Unit tests for FAISS Vector Database & Chunking (Task 1).
"""
import pytest
from harvester.models import HarvestedURL
from harvester.vector_db import chunk_text, get_embedding_model, FAISSKnowledgeBase


def test_chunk_text_basic():
    text = "Paragraph one with some information.\n\nParagraph two with executive leadership details.\n\nParagraph three."
    chunks = chunk_text(text, chunk_size=80, overlap=20)
    assert len(chunks) >= 2
    assert all(isinstance(c, str) for c in chunks)


def test_embedding_model_encode():
    embedder = get_embedding_model()
    vectors = embedder.encode(["Artificial intelligence executive leadership.", "Quantum computing algorithms."])
    assert len(vectors) == 2
    assert vectors.shape[1] == 384


@pytest.mark.django_db
def test_faiss_knowledge_base_search(db):
    kb = FAISSKnowledgeBase()
    kb.reset_index()

    url_obj = HarvestedURL.objects.create(
        url="https://example.com/leadership",
        page_title="Example Leadership Team",
        meta_description="Executives of Example Corp",
        cleaned_text=(
            "Sundar Pichai is the CEO of Alphabet and Google. "
            "Under his leadership, Google has expanded AI capabilities across Search, Cloud, and Workspace. "
            "Satya Nadella is the CEO of Microsoft, leading transformations in Cloud and Open AI partnerships."
        ),
        executive_details=[
            {"name": "Sundar Pichai", "role": "CEO", "bio": "CEO of Alphabet and Google"},
            {"name": "Satya Nadella", "role": "CEO", "bio": "CEO of Microsoft"}
        ]
    )

    # Ingest into vector KB
    chunks_count = kb.ingest_url(url_obj)
    assert chunks_count > 0
    assert kb.index.ntotal >= chunks_count

    # Semantic search query
    results = kb.search(query="Who is the CEO of Google?", top_k=3)
    assert len(results) >= 1
    assert "CEO" in results[0]['chunk_text'] or "Google" in results[0]['chunk_text']
