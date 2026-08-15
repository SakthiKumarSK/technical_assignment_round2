"""
Health and System Router for Task 2.
"""
from fastapi import APIRouter
from ..models import HealthResponse
from ..ollama_client import ollama_client
from ..vector_store import rag_vector_store

router = APIRouter(prefix="/api", tags=["Health"])


@router.get("/health", response_model=HealthResponse, summary="Backend & Ollama Health Check")
async def health_check():
    """
    Returns backend health status, Ollama daemon connectivity, and database stats.
    """
    ollama_ok = await ollama_client.is_available()
    models = await ollama_client.get_models()
    stats = rag_vector_store.get_stats()

    return HealthResponse(
        status="healthy",
        ollama_connected=ollama_ok,
        ollama_base_url=ollama_client.base_url,
        available_models=models,
        total_documents=stats["total_documents"],
        total_vectors=stats["total_vectors"]
    )


@router.get("/models", summary="List Available Ollama Models")
async def list_models():
    """
    Returns available models hosted in local Ollama.
    """
    models = await ollama_client.get_models()
    return {"models": models}
