"""
Document Ingestion & Management Router for Task 2.
"""
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from ..models import DocumentInfo, DocumentUploadResponse
from ..rag_service import rag_service
from ..vector_store import rag_vector_store

router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentUploadResponse, summary="Upload & Ingest Documents")
async def upload_documents(files: List[UploadFile] = File(...)):
    """
    Accepts one or more documents (PDF, DOCX, TXT, MD, CSV), extracts text,
    splits into chunks, generates vector embeddings, and stores in FAISS.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided for upload.")

    processed = []
    total_new_chunks = 0

    for f in files:
        try:
            content = await f.read()
            if not content:
                continue

            doc_info = rag_service.ingest_document(
                file_bytes=content,
                file_name=f.filename,
                file_size=len(content)
            )
            processed.append(doc_info)
            total_new_chunks += doc_info.total_chunks
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Failed processing file '{f.filename}': {str(exc)}"
            )

    stats = rag_vector_store.get_stats()
    return DocumentUploadResponse(
        message=f"Successfully indexed {len(processed)} document(s) with {total_new_chunks} chunks.",
        documents_processed=processed,
        total_new_chunks=total_new_chunks,
        total_vector_count=stats["total_vectors"]
    )


@router.get("", response_model=List[DocumentInfo], summary="List Ingested Documents")
async def list_documents():
    """
    Returns list of all documents stored in the vector database.
    """
    docs = rag_vector_store.list_documents()
    return [DocumentInfo(**d) for d in docs]


@router.delete("/{doc_id}", summary="Delete Document from Vector Store")
async def delete_document(doc_id: str):
    """
    Removes a document and its chunks from the FAISS vector index.
    """
    success = rag_vector_store.delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found.")
    return {"message": f"Document '{doc_id}' deleted successfully.", "stats": rag_vector_store.get_stats()}


@router.delete("", summary="Clear All Documents from Vector Store")
async def clear_all_documents():
    """
    Resets and clears the entire vector database.
    """
    rag_vector_store.clear_all()
    return {"message": "All documents and vectors cleared.", "stats": rag_vector_store.get_stats()}
