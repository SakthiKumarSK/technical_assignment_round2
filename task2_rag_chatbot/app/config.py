"""
Configuration and settings for Task 2 (Local LLM RAG Chatbot).
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings:
    # Server configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8001))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Ollama Local LLM Configuration
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    DEFAULT_LLM_MODEL: str = os.getenv("DEFAULT_LLM_MODEL", "llama3")
    OLLAMA_REQUEST_TIMEOUT: int = int(os.getenv("OLLAMA_REQUEST_TIMEOUT", 60))
    
    # Vector Database & Embeddings
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
    EMBEDDING_DIMENSION: int = 384
    DATA_DIR: Path = BASE_DIR / "data"
    FAISS_INDEX_PATH: Path = DATA_DIR / "rag_faiss.index"
    METADATA_STORE_PATH: Path = DATA_DIR / "rag_metadata.pkl"
    DOCUMENTS_DIR: Path = DATA_DIR / "uploaded_docs"
    
    # Chunking Parameters
    DEFAULT_CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", 500))
    DEFAULT_CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", 100))
    
    # Retrieval
    DEFAULT_TOP_K: int = int(os.getenv("TOP_K", 4))
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", 0.15))

    def __init__(self):
        os.makedirs(self.DATA_DIR, exist_ok=True)
        os.makedirs(self.DOCUMENTS_DIR, exist_ok=True)


settings = Settings()
