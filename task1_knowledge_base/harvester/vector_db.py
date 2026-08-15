"""
FAISS Vector Database Pipeline & Semantic Search Engine.
Handles document chunking, embedding generation with SentenceTransformers,
FAISS vector indexing, persistence, and similarity retrieval.
"""
import os
import pickle
import logging
import hashlib
from typing import List, Dict, Any, Optional
import numpy as np
import faiss
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# Global singleton embedding model cache to avoid re-loading weights
_EMBEDDING_MODEL = None


def get_embedding_model():
    """
    Lazy loader for SentenceTransformer embedding model.
    Falls back gracefully to a deterministic pseudo-embedding generator
    if network/offline mode prevents downloading weights during quick local runs.
    """
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        model_name = getattr(settings, 'EMBEDDING_MODEL_NAME', 'all-MiniLM-L6-v2')
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading SentenceTransformer embedding model: {model_name}...")
            _EMBEDDING_MODEL = SentenceTransformer(model_name)
            logger.info(f"SentenceTransformer {model_name} successfully loaded.")
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
                        # Deterministic hash-based dense representation with n-gram hashing
                        rng = np.random.RandomState(int(hashlib.md5(t.encode('utf-8')).hexdigest()[:8], 16))
                        vec = rng.randn(self.dim).astype(np.float32)
                        # boost on words
                        for word in t.lower().split():
                            w_idx = int(hashlib.md5(word.encode('utf-8')).hexdigest()[:4], 16) % self.dim
                            vec[w_idx] += 2.0
                        if normalize_embeddings:
                            norm = np.linalg.norm(vec)
                            if norm > 0:
                                vec = vec / norm
                        vectors.append(vec)
                    return np.array(vectors, dtype=np.float32)
            
            _EMBEDDING_MODEL = FallbackEmbedder(dim=384)
            
    return _EMBEDDING_MODEL


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
    """
    Splits text into overlapping semantic chunks based on paragraph and sentence boundaries.
    """
    if not text:
        return []
    
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [text.strip()]

    chunks = []
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) <= chunk_size:
            current_chunk += ("\n\n" if current_chunk else "") + para
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
                # Start new chunk with overlap from previous chunk
                overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk = overlap_text + " " + para
            else:
                # Single paragraph exceeds chunk_size, split by words
                words = para.split()
                temp = ""
                for w in words:
                    if len(temp) + len(w) + 1 <= chunk_size:
                        temp += (" " if temp else "") + w
                    else:
                        if temp:
                            chunks.append(temp.strip())
                        temp = w
                if temp:
                    current_chunk = temp

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


class FAISSKnowledgeBase:
    """
    Vector Database index manager for Task 1.
    Maintains a FAISS index and aligned metadata dictionary.
    """
    def __init__(self):
        self.index_path = str(getattr(settings, 'FAISS_INDEX_FILE', 'vector_data/kb_faiss.index'))
        self.meta_path = str(getattr(settings, 'FAISS_METADATA_FILE', 'vector_data/kb_faiss_meta.pkl'))
        self.dimension = 384
        self.index = None
        self.metadata = []  # List of dicts matching vector index positions
        self._load_or_create_index()

    def _load_or_create_index(self):
        """Loads existing FAISS index from disk or creates a new IndexFlatIP (cosine similarity)."""
        if os.path.exists(self.index_path) and os.path.exists(self.meta_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.meta_path, 'rb') as f:
                    self.metadata = pickle.load(f)
                logger.info(f"Loaded existing FAISS index with {self.index.ntotal} vectors.")
                return
            except Exception as exc:
                logger.error(f"Failed to read existing FAISS index: {exc}. Initializing new index.")

        # Create IndexFlatIP (Inner Product = Cosine Similarity for normalized vectors)
        self.index = faiss.IndexFlatIP(self.dimension)
        self.metadata = []

    def save_index(self):
        """Persists the FAISS index and metadata to disk."""
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, 'wb') as f:
            pickle.dump(self.metadata, f)
        logger.info(f"FAISS index saved to disk ({self.index.ntotal} vectors).")

    def reset_index(self):
        """Clears index and deletes index files."""
        self.index = faiss.IndexFlatIP(self.dimension)
        self.metadata = []
        if os.path.exists(self.index_path):
            os.remove(self.index_path)
        if os.path.exists(self.meta_path):
            os.remove(self.meta_path)

    def ingest_url(self, harvested_url) -> int:
        """
        Chunks and ingests a single HarvestedURL into the FAISS vector database.
        Returns the number of chunks indexed.
        """
        from .models import URLChunk

        text_to_index = harvested_url.cleaned_text
        if not text_to_index or len(text_to_index.strip()) < 20:
            text_to_index = harvested_url.page_title + " " + harvested_url.meta_description

        if not text_to_index:
            return 0

        chunks = chunk_text(text_to_index, chunk_size=500, overlap=100)
        if not chunks:
            return 0

        embedder = get_embedding_model()
        vectors = embedder.encode(chunks, normalize_embeddings=True)
        vectors = np.array(vectors, dtype=np.float32)

        # Remove previous chunks for this URL from SQLite if re-indexing
        URLChunk.objects.filter(harvested_url=harvested_url).delete()

        start_vector_id = self.index.ntotal
        self.index.add(vectors)

        # Check for person keywords in chunks
        person_regex = r'\b(CEO|CTO|CFO|COO|President|Founder|Director|Executive|VP|Leader)\b'
        import re

        chunk_objs = []
        for i, (chunk_str, vec) in enumerate(zip(chunks, vectors)):
            vector_id = start_vector_id + i
            has_person = bool(re.search(person_regex, chunk_str, re.IGNORECASE))
            
            chunk_hash = hashlib.sha256(chunk_str.encode('utf-8')).hexdigest()
            chunk_objs.append(URLChunk(
                harvested_url=harvested_url,
                chunk_index=i,
                chunk_text=chunk_str,
                chunk_hash=chunk_hash,
                vector_id=vector_id,
                has_person_info=has_person
            ))

            self.metadata.append({
                'vector_id': vector_id,
                'url_id': harvested_url.id,
                'url': harvested_url.url,
                'page_title': harvested_url.page_title,
                'chunk_index': i,
                'chunk_text': chunk_str,
                'has_person_info': has_person,
                'executive_details': harvested_url.executive_details
            })

        URLChunk.objects.bulk_create(chunk_objs)

        harvested_url.is_indexed = True
        harvested_url.indexed_at = timezone.now()
        harvested_url.total_chunks = len(chunks)
        harvested_url.save(update_fields=['is_indexed', 'indexed_at', 'total_chunks'])

        self.save_index()
        logger.info(f"Ingested {len(chunks)} chunks for {harvested_url.url} into FAISS.")
        return len(chunks)

    def ingest_all_unindexed(self) -> int:
        """
        Ingests all HarvestedURL records from SQLite that have not yet been indexed.
        """
        from .models import HarvestedURL
        unindexed_urls = HarvestedURL.objects.filter(is_indexed=False)
        total_chunks = 0
        for url_obj in unindexed_urls:
            total_chunks += self.ingest_url(url_obj)
        return total_chunks

    def search(self, query: str, top_k: int = 5, filter_person: bool = False) -> List[Dict[str, Any]]:
        """
        Performs semantic vector search on the FAISS index.
        Returns top-k matching chunks with similarity scores, metadata, and executive context.
        """
        if self.index is None or self.index.ntotal == 0:
            return []

        embedder = get_embedding_model()
        query_vector = embedder.encode([query], normalize_embeddings=True)
        query_vector = np.array(query_vector, dtype=np.float32)

        # Retrieve extra candidates if filtering
        fetch_k = min(top_k * 3 if filter_person else top_k, self.index.ntotal)
        scores, indices = self.index.search(query_vector, fetch_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue
            
            meta = self.metadata[idx]
            if filter_person and not meta.get('has_person_info', False):
                continue

            results.append({
                'score': float(score),
                'similarity_percent': round(max(0.0, float(score)) * 100, 1),
                'url_id': meta.get('url_id'),
                'url': meta.get('url'),
                'page_title': meta.get('page_title'),
                'chunk_index': meta.get('chunk_index'),
                'chunk_text': meta.get('chunk_text'),
                'has_person_info': meta.get('has_person_info', False),
                'executive_details': meta.get('executive_details', [])
            })

            if len(results) >= top_k:
                break

        return results


# Global helper instance
kb_vector_db = FAISSKnowledgeBase()
