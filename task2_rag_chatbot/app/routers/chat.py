"""
Chat Router for Task 2 RAG.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from ..models import ChatRequest, ChatResponse
from ..rag_service import rag_service

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse, summary="Execute Grounded RAG Chat Query")
async def chat_endpoint(request: ChatRequest):
    """
    Accepts user question, retrieves relevant context from FAISS,
    generates grounded response using local LLM, and returns answer + source citations.
    """
    try:
        response = await rag_service.answer_question(request)
        return response
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/stream", summary="Stream Grounded RAG Response via SSE")
async def stream_chat_endpoint(request: ChatRequest):
    """
    Streams generated tokens and source citations in real time via Server-Sent Events.
    """
    try:
        return StreamingResponse(
            rag_service.stream_answer(request),
            media_type="text/event-stream"
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
