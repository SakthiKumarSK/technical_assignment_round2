"""
FastAPI Application Entrypoint for Task 2 (Local LLM RAG Chatbot).
"""
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .config import settings
from .routers import chat, documents, health

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(message)s"
)
logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Task 2 Local LLM RAG Chatbot Backend...")
    logger.info(f"Ollama Base URL: {settings.OLLAMA_BASE_URL}")
    logger.info(f"Embedding Model: {settings.EMBEDDING_MODEL_NAME}")
    yield
    logger.info("Shutting down Task 2 Backend...")

app = FastAPI(
    title="Local LLM Document Q&A Chatbot (RAG)",
    description=(
        "Production-grade Retrieval-Augmented Generation (RAG) backend utilizing "
        "local Ollama LLM, FAISS Vector Database, multi-format document ingestion, "
        "and strict source citations."
    ),
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware for open client communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health.router)
app.include_router(documents.router)
app.include_router(chat.router)

# Mount Static UI files
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
async def serve_root():
    """Serves the Chatbot Single Page Application."""
    index_path = STATIC_DIR / "index.html"
    return FileResponse(str(index_path))
