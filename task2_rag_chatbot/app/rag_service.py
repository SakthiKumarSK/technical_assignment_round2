"""
RAG Orchestration Service.
Connects document loader, chunker, FAISS vector store, grounding prompts,
and LLM inference to fulfill grounded Q&A with source citations.
"""
import time
import uuid
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, AsyncGenerator

from .config import settings
from .models import ChatRequest, ChatResponse, SourceCitation, DocumentInfo
from .loader import load_document
from .chunker import create_document_chunks
from .vector_store import rag_vector_store
from .ollama_client import ollama_client, build_grounded_prompt

logger = logging.getLogger(__name__)


class RAGService:
    """
    Coordinates end-to-end RAG workflows.
    """
    async def answer_question(self, request: ChatRequest) -> ChatResponse:
        """
        Retrieves context chunks, queries local LLM, and formats grounded answer with citations.
        """
        start_time = time.time()
        top_k = request.top_k or settings.DEFAULT_TOP_K
        model = request.model or settings.DEFAULT_LLM_MODEL

        # 1. Semantic retrieval from FAISS
        raw_matches = rag_vector_store.similarity_search(
            query=request.question,
            top_k=top_k
        )

        # 2. Build structured citations
        citations: List[SourceCitation] = []
        for m in raw_matches:
            citations.append(SourceCitation(
                document_id=m.get("document_id", ""),
                document_name=m.get("document_name", "Unknown"),
                chunk_index=m.get("chunk_index", 0),
                page_number=m.get("page_number", 1),
                similarity_score=m.get("similarity_score", 0.0),
                similarity_percentage=m.get("similarity_percentage", 0.0),
                snippet=m.get("snippet", "")
            ))

        # 3. Construct grounded prompt
        prompt = build_grounded_prompt(
            question=request.question,
            context_chunks=raw_matches,
            history=request.history
        )

        # 4. Generate answer using local LLM
        answer = await ollama_client.generate_response(
            prompt=prompt,
            model=model,
            temperature=request.temperature or 0.2
        )

        latency = round(time.time() - start_time, 3)

        return ChatResponse(
            question=request.question,
            answer=answer,
            model_used=model,
            citations=citations,
            latency_seconds=latency,
            retrieved_chunks_count=len(citations)
        )

    async def stream_answer(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        """
        Streams response tokens and citations via Server-Sent Events (SSE).
        """
        top_k = request.top_k or settings.DEFAULT_TOP_K
        model = request.model or settings.DEFAULT_LLM_MODEL

        # 1. Retrieve context
        raw_matches = rag_vector_store.similarity_search(
            query=request.question,
            top_k=top_k
        )

        # 2. Yield Citations Event first
        citations = [
            {
                "document_id": m.get("document_id", ""),
                "document_name": m.get("document_name", ""),
                "chunk_index": m.get("chunk_index", 0),
                "page_number": m.get("page_number", 1),
                "similarity_score": m.get("similarity_score", 0.0),
                "similarity_percentage": m.get("similarity_percentage", 0.0),
                "snippet": m.get("snippet", "")
            }
            for m in raw_matches
        ]
        yield f"event: citations\ndata: {json.dumps(citations)}\n\n"

        # 3. Construct prompt
        prompt = build_grounded_prompt(
            question=request.question,
            context_chunks=raw_matches,
            history=request.history
        )

        # 4. Stream response tokens
        async for token in ollama_client.stream_response(
            prompt=prompt,
            model=model,
            temperature=request.temperature or 0.2
        ):
            yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"

        yield "event: done\ndata: [DONE]\n\n"

    def ingest_document(
        self,
        file_bytes: bytes,
        file_name: str,
        file_size: int
    ) -> DocumentInfo:
        """
        Loads, chunks, and indexes a single document into FAISS.
        """
        doc_id = str(uuid.uuid4())[:8]
        from datetime import timezone
        uploaded_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        file_type = file_name.split('.')[-1].upper() if '.' in file_name else "TXT"

        # 1. Extract pages
        pages = load_document(file_bytes, file_name)

        # 2. Chunk text
        chunks = create_document_chunks(
            pages=pages,
            doc_id=doc_id,
            doc_name=file_name,
            chunk_size=settings.DEFAULT_CHUNK_SIZE,
            chunk_overlap=settings.DEFAULT_CHUNK_OVERLAP
        )

        # 3. Index into vector database
        indexed_count = rag_vector_store.add_document(
            doc_id=doc_id,
            doc_name=file_name,
            file_type=file_type,
            file_size=file_size,
            chunks=chunks,
            uploaded_at=uploaded_at
        )

        return DocumentInfo(
            doc_id=doc_id,
            file_name=file_name,
            file_type=file_type,
            file_size_bytes=file_size,
            total_chunks=indexed_count,
            uploaded_at=uploaded_at
        )


rag_service = RAGService()
