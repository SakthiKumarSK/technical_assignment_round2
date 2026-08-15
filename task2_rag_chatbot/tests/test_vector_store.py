"""
Unit tests for Task 2 FAISS Vector Store.
"""
from app.vector_store import LocalVectorStore


def test_vector_store_add_and_search(tmp_path):
    store = LocalVectorStore()
    store.clear_all()

    chunks = [
        {
            "doc_id": "test-doc-1",
            "doc_name": "ai_strategy.txt",
            "chunk_index": 0,
            "page_number": 1,
            "text": "Deep learning models require specialized GPU clusters and optimized CUDA libraries.",
            "char_count": 80,
            "word_count": 12
        },
        {
            "doc_id": "test-doc-1",
            "doc_name": "ai_strategy.txt",
            "chunk_index": 1,
            "page_number": 1,
            "text": "Retrieval Augmented Generation reduces hallucination by providing grounded context.",
            "char_count": 84,
            "word_count": 11
        }
    ]

    indexed_count = store.add_document(
        doc_id="test-doc-1",
        doc_name="ai_strategy.txt",
        file_type="TXT",
        file_size=200,
        chunks=chunks,
        uploaded_at="2026-08-15 12:00:00 UTC"
    )

    assert indexed_count == 2
    assert store.get_stats()["total_vectors"] >= 2

    # Similarity search
    matches = store.similarity_search("How does Retrieval Augmented Generation help?", top_k=2)
    assert len(matches) >= 1
    assert "Retrieval Augmented Generation" in matches[0]["snippet"]
    assert matches[0]["similarity_score"] > 0

    # Delete
    deleted = store.delete_document("test-doc-1")
    assert deleted is True
    assert store.get_stats()["total_documents"] == 0
