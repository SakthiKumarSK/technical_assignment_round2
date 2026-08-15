"""
Local FAISS Vector Store Manager for Task 2 RAG.
Provides vector persistence, document indexing, deletion, and cosine similarity search.
"""
import os
import pickle
import logging
import hashlib
from typing import List, Dict, Any, Optional
import numpy as np
import faiss
from .config import settings

logger = logging.getLogger(__name__)

# Global singleton embedding model
_EMBEDDER = None


def get_task2_embedder():
    """
    Loads SentenceTransformer model with fallback.
    """
    global _EMBEDDER
    if _EMBEDDER is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading SentenceTransformer for RAG: {settings.EMBEDDING_MODEL_NAME}...")
            _EMBEDDER = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
            logger.info("SentenceTransformer for RAG loaded successfully.")
        except Exception as exc:
            logger.warning(f"Could not load SentenceTransformer ({exc}), initializing robust local fallback embedder.")

            class FallbackEmbedder:
                def __init__(self, dim=384):
                    self.dim = dim

                def encode(self, texts, show_progress_bar=False, normalize_embeddings=True):
                    if isinstance(texts, str):
                        texts = [texts]
                    vectors = []
                    for t in texts:
                        rng = np.random.RandomState(int(hashlib.md5(t.encode('utf-8')).hexdigest()[:8], 16))
                        vec = rng.randn(self.dim).astype(np.float32)
                        for word in t.lower().split():
                            w_idx = int(hashlib.md5(word.encode('utf-8')).hexdigest()[:4], 16) % self.dim
                            vec[w_idx] += 2.0
                        if normalize_embeddings:
                            norm = np.linalg.norm(vec)
                            if norm > 0:
                                vec = vec / norm
                        vectors.append(vec)
                    return np.array(vectors, dtype=np.float32)

            _EMBEDDER = FallbackEmbedder(dim=settings.EMBEDDING_DIMENSION)

    return _EMBEDDER


class LocalVectorStore:
    """
    Persistent FAISS Vector Store for Document Chunks.
    """
    def __init__(self):
        self.index_path = str(settings.FAISS_INDEX_PATH)
        self.meta_path = str(settings.METADATA_STORE_PATH)
        self.dimension = settings.EMBEDDING_DIMENSION
        self.index = None
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.chunks: List[Dict[str, Any]] = []
        self._load_or_create()

    def _load_or_create(self):
        """Loads index and metadata from disk if available."""
        if os.path.exists(self.index_path) and os.path.exists(self.meta_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.meta_path, 'rb') as f:
                    data = pickle.load(f)
                    self.documents = data.get("documents", {})
                    self.chunks = data.get("chunks", [])
                logger.info(f"Loaded existing RAG FAISS index: {self.index.ntotal} vectors across {len(self.documents)} documents.")
                return
            except Exception as exc:
                logger.error(f"Failed to load RAG index: {exc}. Creating new index.")

        self.index = faiss.IndexFlatIP(self.dimension)
        self.documents = {}
        self.chunks = []

    def save(self):
        """Persists the FAISS index and metadata state to disk."""
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, 'wb') as f:
            pickle.dump({
                "documents": self.documents,
                "chunks": self.chunks
            }, f)
        logger.info(f"RAG vector store saved ({self.index.ntotal} vectors).")

    def add_document(
        self,
        doc_id: str,
        doc_name: str,
        file_type: str,
        file_size: int,
        chunks: List[Dict[str, Any]],
        uploaded_at: str
    ) -> int:
        """
        Adds and indexes chunks for a document into FAISS.
        """
        if not chunks:
            return 0

        # Remove existing document if already present
        if doc_id in self.documents:
            self.delete_document(doc_id)

        texts = [c["text"] for c in chunks]
        embedder = get_task2_embedder()
        vectors = embedder.encode(texts, normalize_embeddings=True)
        vectors = np.array(vectors, dtype=np.float32)

        start_vector_id = self.index.ntotal
        self.index.add(vectors)

        for i, chunk in enumerate(chunks):
            chunk["vector_id"] = start_vector_id + i
            self.chunks.append(chunk)

        self.documents[doc_id] = {
            "doc_id": doc_id,
            "file_name": doc_name,
            "file_type": file_type,
            "file_size_bytes": file_size,
            "total_chunks": len(chunks),
            "uploaded_at": uploaded_at
        }

        self.save()
        logger.info(f"Successfully added document '{doc_name}' ({len(chunks)} chunks). Total vectors: {self.index.ntotal}")
        return len(chunks)

    def delete_document(self, doc_id: str) -> bool:
        """
        Removes a document and rebuilds the FAISS index.
        """
        if doc_id not in self.documents:
            return False

        del self.documents[doc_id]
        remaining_chunks = [c for c in self.chunks if c.get("doc_id") != doc_id]

        # Rebuild index with remaining chunks
        self.index = faiss.IndexFlatIP(self.dimension)
        self.chunks = []

        if remaining_chunks:
            texts = [c["text"] for c in remaining_chunks]
            embedder = get_task2_embedder()
            vectors = embedder.encode(texts, normalize_embeddings=True)
            vectors = np.array(vectors, dtype=np.float32)
            self.index.add(vectors)

            for i, chunk in enumerate(remaining_chunks):
                chunk["vector_id"] = i
                self.chunks.append(chunk)

        self.save()
        logger.info(f"Deleted document '{doc_id}'. Remaining vectors: {self.index.ntotal}")
        return True

    def clear_all(self):
        """Clears all indexed vectors and documents."""
        self.index = faiss.IndexFlatIP(self.dimension)
        self.documents = {}
        self.chunks = []
        self.save()

    def similarity_search(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """
        Performs cosine similarity search against indexed chunks.
        Returns ranked list of matching chunks with similarity scores.
        """
        if self.index is None or self.index.ntotal == 0 or not self.chunks:
            return []

        embedder = get_task2_embedder()
        query_vector = embedder.encode([query], normalize_embeddings=True)
        query_vector = np.array(query_vector, dtype=np.float32)

        k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(query_vector, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.chunks):
                continue

            chunk_meta = self.chunks[idx]
            sim_score = float(score)
            sim_percent = round(max(0.0, sim_score) * 100, 1)

            results.append({
                "document_id": chunk_meta.get("doc_id"),
                "document_name": chunk_meta.get("doc_name"),
                "chunk_index": chunk_meta.get("chunk_index"),
                "page_number": chunk_meta.get("page_number", 1),
                "similarity_score": sim_score,
                "similarity_percentage": sim_percent,
                "snippet": chunk_meta.get("text")
            })

        return results

    def list_documents(self) -> List[Dict[str, Any]]:
        return list(self.documents.values())

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_documents": len(self.documents),
            "total_chunks": len(self.chunks),
            "total_vectors": self.index.ntotal if self.index else 0
        }


# Global Singleton Vector Store
rag_vector_store = LocalVectorStore()
