# Technical Assignment – Round 2: Full-Stack Knowledge Base & Local RAG System

**Candidate**: Sakthikumar  
**GitHub**: [https://github.com/SakthiKumarSK](https://github.com/SakthiKumarSK)  
**Submission**: Complete Source Code, Documentation, Test Suites, Docker Configuration, and Sample Datasets.

---

## 🌟 Executive Summary

This repository contains the complete implementation for **Technical Assignment – Round 2**, featuring two enterprise-grade systems:

1. **Task 1 – Knowledge Base from CSV URLs**:
   - **Framework**: Django 5.x + Django REST Framework (DRF)
   - **Persistence**: SQLite (storing raw HTML, HTTP status codes, executive entities, and metadata)
   - **Vector Database**: FAISS (384-dimensional dense cosine index with `sentence-transformers`)
   - **Web UI**: Modern responsive dashboard, CSV upload dropzone, natural language semantic search with executive entity extraction, and SQLite raw data inspector.
   - **REST API**: Fully compliant `GET /api/urls/` endpoint + batch upload & semantic search APIs.

2. **Task 2 – Local LLM Document Q&A Chatbot (Grounded RAG)**:
   - **Framework**: FastAPI (Asynchronous ASGI backend)
   - **Local LLM**: Ollama (`llama3`, `mistral`, `phi3`, `qwen2.5`) with seamless local engine fallback
   - **Document Ingestion**: Multi-format parsing for **PDF, DOCX, TXT, Markdown (.md), and CSV**
   - **Vector Database**: FAISS persistent vector store with recursive chunking
   - **Grounded Responses & Citations**: Strict prompt grounding with interactive, collapsible source citation badges (document name, chunk index, similarity %, verbatim snippet).
   - **Web Chatbot UI**: Modern Single-Page Application with real-time response rendering, file upload drawer, and model switcher.

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python**: 3.10+ (Tested on Python 3.12)
- **Git**: Installed
- **Ollama** (Optional): Download from [ollama.com](https://ollama.com) and run `ollama pull llama3` (The app includes a local synthesizer fallback if Ollama is not active).

---

### Method A: Running Locally with Python (Recommended)

#### 1. Setup Environment & Dependencies
```bash
# Clone the repository
git clone https://github.com/SakthiKumarSK/technical_assignment_round2.git
cd technical_assignment_round2

# Install dependencies
pip install -r requirements.txt
```

#### 2. Run Task 1 (Django URL Knowledge Base)
```bash
# Windows
scripts\run_task1.bat

# Linux / macOS
chmod +x scripts/run_task1.sh
./scripts/run_task1.sh
```
- 🌐 **Web UI**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- 📄 **REST API Endpoint**: [http://127.0.0.1:8000/api/urls/](http://127.0.0.1:8000/api/urls/)

#### 3. Run Task 2 (FastAPI Local LLM RAG Chatbot)
```bash
# Windows
scripts\run_task2.bat

# Linux / macOS
chmod +x scripts/run_task2.sh
./scripts/run_task2.sh
```
- 💬 **Web Chatbot UI**: [http://127.0.0.1:8001/](http://127.0.0.1:8001/)
- 📖 **Interactive Swagger API Docs**: [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)

---

### Method B: Running with Docker Compose

```bash
docker-compose -f docker/docker-compose.yml up --build
```
- **Task 1 Web UI**: `http://localhost:8000/`
- **Task 2 Web UI**: `http://localhost:8001/`
- **Local Ollama Service**: `http://localhost:11434/`

---

## 🧪 Automated Test Suites (100% Pass Rate)

Run the comprehensive pytest suites covering both tasks:

```bash
# Run all tests (23 test cases)
scripts\run_all_tests.bat      # Windows
./scripts/run_all_tests.sh     # Linux / macOS
```

Or run individually:
```bash
# Task 1 Tests (11 tests: Scraper, SQLite models, FAISS vector DB, REST API)
pytest task1_knowledge_base -v

# Task 2 Tests (12 tests: Document Loaders, Chunker, Vector Store, RAG Service, FastAPI)
pytest task2_rag_chatbot -v
```

---

## 📁 Repository Structure

```
technical_assignment_round2/
├── task1_knowledge_base/                  # Task 1: Django + DRF + SQLite + FAISS
│   ├── manage.py
│   ├── kb_project/                        # Settings, ASGI/WSGI, Root URLs
│   ├── harvester/                         # Scraper, Models, FAISS Vector DB, DRF API Views
│   ├── templates/                         # Web UI (Dashboard, Upload, Search, SQLite Inspector)
│   ├── static/                            # CSS & JS Design System
│   └── tests/                             # 11 Unit & Integration Tests
│
├── task2_rag_chatbot/                     # Task 2: FastAPI + Ollama RAG + Citations
│   ├── app/
│   │   ├── main.py                        # FastAPI entrypoint
│   │   ├── loader.py                      # PDF, DOCX, TXT, MD, CSV loaders
│   │   ├── chunker.py                     # Recursive character chunker
│   │   ├── vector_store.py                # FAISS vector store
│   │   ├── ollama_client.py               # Ollama client & grounding engine
│   │   ├── rag_service.py                 # RAG orchestration service
│   │   └── routers/                       # Chat, Documents, Health endpoints
│   ├── static/                            # Modern Single-Page Chatbot Interface
│   └── tests/                             # 12 Unit & Integration Tests
│
├── sample_data/                           # Ready-to-use Sample Datasets
│   ├── executive_urls.csv                 # CSV with leadership & company URLs
│   ├── tech_leadership_batch.csv          # Additional batch CSV
│   └── documents/                         # Documents for Task 2 RAG testing
│       ├── ai_strategy_roadmap_2026.md
│       ├── executive_profiles_and_roles.txt
│       └── quarterly_financial_report.csv
│
├── docker/                                # Docker & Multi-Service Compose
│   ├── Dockerfile.task1
│   ├── Dockerfile.task2
│   └── docker-compose.yml
│
├── docs/                                  # Comprehensive Documentation
│   ├── DOCUMENTATION.md                   # Report (assumptions, difficulties, dev time breakdown, observations)
│   ├── ARCHITECTURE.md                    # Architecture flowcharts & SQLite schema
│   └── API_REFERENCE.md                   # REST API documentation with curl examples
│
├── scripts/                               # Run & Test Scripts (.bat & .sh)
├── requirements.txt                       # Consolidated Python dependencies
└── README.md                              # Master Overview
```

---

## 📚 Supporting Documentation
- 📄 [Engineering Documentation & Observations](docs/DOCUMENTATION.md)
- 🏗️ [System Architecture & Flowcharts](docs/ARCHITECTURE.md)
- 🔌 [Complete REST API Reference](docs/API_REFERENCE.md)
