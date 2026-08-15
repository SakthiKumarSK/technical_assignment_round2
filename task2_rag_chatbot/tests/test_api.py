"""
Integration tests for FastAPI endpoints in Task 2.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.vector_store import rag_vector_store


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "available_models" in data


@pytest.mark.asyncio
async def test_models_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/models")
        assert resp.status_code == 200
        data = resp.json()
        assert "models" in data


@pytest.mark.asyncio
async def test_document_upload_and_chat_flow():
    rag_vector_store.clear_all()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Upload a document
        files = {
            "files": ("company_strategy.txt", b"Apex Global announced expansion into autonomous AI agents in 2026.", "text/plain")
        }
        upload_resp = await client.post("/api/documents/upload", files=files)
        assert upload_resp.status_code == 200
        upload_data = upload_resp.json()
        assert upload_data["total_new_chunks"] >= 1

        # 2. List documents
        list_resp = await client.get("/api/documents")
        assert list_resp.status_code == 200
        docs = list_resp.json()
        assert len(docs) >= 1
        assert docs[0]["file_name"] == "company_strategy.txt"
        doc_id = docs[0]["doc_id"]

        # 3. Chat with RAG
        chat_payload = {
            "question": "What did Apex Global announce regarding autonomous AI?",
            "top_k": 2
        }
        chat_resp = await client.post("/api/chat", json=chat_payload)
        assert chat_resp.status_code == 200
        chat_data = chat_resp.json()
        assert "autonomous AI" in chat_data["answer"] or "Apex Global" in chat_data["answer"]
        assert len(chat_data["citations"]) >= 1
        assert chat_data["citations"][0]["document_name"] == "company_strategy.txt"

        # 4. Delete document
        del_resp = await client.delete(f"/api/documents/{doc_id}")
        assert del_resp.status_code == 200
