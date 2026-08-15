# Implementation Plan: Technical Assignment – Round 2

## Project Overview
This repository contains the complete implementation for Technical Assignment – Round 2, addressing:
1. **Task 1 – Knowledge Base from CSV URLs**: Django + DRF + SQLite + FAISS Vector DB + Web Scraper & Harvesting Pipeline + Person/Executive Search + Web UI + `/api/urls/` REST endpoint.
2. **Task 2 – Local LLM Document Q&A Chatbot (RAG)**: FastAPI + Ollama Local LLM Integration + Multi-format Document Ingestion + FAISS Vector Store + Grounded Generation with Source Citations + Web Chatbot UI.
3. **Packaging, Testing, & Documentation**: Docker containerization, automated pytest test suites, sample data files, run scripts, and documentation.

## Execution Steps
- [x] **Step 0**: Initialize repository, configure environment, dependencies, `.gitignore`, and `PLAN.md`.
- [ ] **Step 1**: Task 1 - Django project setup, SQLite models (`HarvestedURL`, `URLChunk`, `ScrapingLog`), resilient scraping engine (`scraper.py`), text cleaner & executive/role metadata extractor.
- [ ] **Step 2**: Task 1 - FAISS Vector Database integration (`vector_db.py`), chunking pipeline, embedding generation (`all-MiniLM-L6-v2`), and semantic query engine (`query_engine.py`).
- [ ] **Step 3**: Task 1 - Django REST Framework API endpoints (`GET /api/urls/`, `POST /api/upload/`, `POST /api/harvest/`, `POST /api/search/`, etc.) & serializers.
- [ ] **Step 4**: Task 1 - Web Interface (Upload CSV, Scrape & Ingest progress, Semantic Search UI, SQLite Raw Data inspection table) with responsive design.
- [ ] **Step 5**: Task 1 - Comprehensive automated test suite (`tests/`) & verification.
- [ ] **Step 6**: Task 2 - FastAPI project setup, multi-format document loader (`loader.py` for PDF, TXT, MD, DOCX, CSV), smart chunker (`chunker.py`), and FAISS vector indexer (`vector_store.py`).
- [ ] **Step 7**: Task 2 - Grounded RAG engine (`rag_service.py`), Ollama client & local fallback engine (`ollama_client.py`), source citation formatting.
- [ ] **Step 8**: Task 2 - FastAPI routes (`POST /api/chat`, `POST /api/chat/stream`, `POST /api/documents/upload`, `GET /api/documents`, `GET /api/health`, `GET /api/models`).
- [ ] **Step 9**: Task 2 - Modern Single-Page Chatbot Web Interface (real-time chat, source citation modals, upload drawer, model selector).
- [ ] **Step 10**: Task 2 - Comprehensive automated test suite (`tests/`) & verification.
- [ ] **Step 11**: Sample datasets (`sample_data/` for CSV URLs and RAG documents), Docker setup (`Dockerfile.task1`, `Dockerfile.task2`, `docker-compose.yml`), run scripts (`scripts/`).
- [ ] **Step 12**: Documentation (`DOCUMENTATION.md`, `ARCHITECTURE.md`, `API_REFERENCE.md`, `README.md`).
- [ ] **Step 13**: Final verification, walkthrough artifact generation, and submission packaging.
