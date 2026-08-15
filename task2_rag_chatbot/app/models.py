"""
Pydantic data schemas for Task 2 RAG Chatbot.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., description="'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message content")


class SourceCitation(BaseModel):
    document_id: str
    document_name: str
    chunk_index: int
    page_number: Optional[int] = None
    similarity_score: float
    similarity_percentage: float
    snippet: str


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000, description="User question to answer")
    model: Optional[str] = Field(default="llama3", description="Ollama model name (e.g. llama3, mistral, phi3)")
    top_k: Optional[int] = Field(default=4, ge=1, le=15, description="Number of context chunks to retrieve")
    temperature: Optional[float] = Field(default=0.2, ge=0.0, le=1.0)
    history: Optional[List[ChatMessage]] = Field(default=[], description="Previous conversation turns")


class ChatResponse(BaseModel):
    question: str
    answer: str
    model_used: str
    citations: List[SourceCitation]
    latency_seconds: float
    retrieved_chunks_count: int


class DocumentInfo(BaseModel):
    doc_id: str
    file_name: str
    file_type: str
    file_size_bytes: int
    total_chunks: int
    uploaded_at: str


class DocumentUploadResponse(BaseModel):
    message: str
    documents_processed: List[DocumentInfo]
    total_new_chunks: int
    total_vector_count: int


class HealthResponse(BaseModel):
    status: str
    ollama_connected: bool
    ollama_base_url: str
    available_models: List[str]
    total_documents: int
    total_vectors: int
