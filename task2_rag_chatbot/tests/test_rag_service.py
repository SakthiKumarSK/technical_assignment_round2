"""
Unit tests for RAG orchestration and citations generation.
"""
import pytest
from app.models import ChatRequest
from app.rag_service import rag_service
from app.vector_store import rag_vector_store
from app.ollama_client import build_grounded_prompt


def test_build_grounded_prompt():
    chunks = [
        {
            "document_name": "quarterly_report.pdf",
            "page_number": 2,
            "chunk_index": 0,
            "snippet": "Q3 Revenue reached 45 million USD driven by enterprise cloud adoption."
        }
    ]
    prompt = build_grounded_prompt(
        question="What was Q3 Revenue?",
        context_chunks=chunks
    )
    assert "quarterly_report.pdf" in prompt
    assert "45 million USD" in prompt
    assert "GROUNDING RULES" in prompt


@pytest.mark.asyncio
async def test_rag_service_answer_with_citations():
    rag_vector_store.clear_all()

    # Ingest sample text
    sample_doc = b"Dr. Elena Vance is the Chief AI Scientist at QuantumCore Labs. She oversees neural model alignment."
    rag_service.ingest_document(
        file_bytes=sample_doc,
        file_name="quantum_team.txt",
        file_size=len(sample_doc)
    )

    request = ChatRequest(
        question="Who is Dr. Elena Vance and what is her role?",
        top_k=2
    )
    response = await rag_service.answer_question(request)

    assert response.question == "Who is Dr. Elena Vance and what is her role?"
    assert response.retrieved_chunks_count >= 1
    assert len(response.citations) >= 1
    assert response.citations[0].document_name == "quantum_team.txt"
    assert "Elena Vance" in response.citations[0].snippet
