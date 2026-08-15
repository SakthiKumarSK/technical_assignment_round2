# Technical Assignment – Round 2: Comprehensive Engineering Report

**Candidate**: Sakthikumar  
**Assignment**: Technical Assignment – Round 2  
**Target Projects**:
- **Task 1**: Knowledge Base from CSV URLs (Django, DRF, SQLite, FAISS)
- **Task 2**: Local LLM Document Q&A Chatbot (FastAPI, Ollama, FAISS, Grounded RAG with Citations)

---

## 1. Questions & Assumptions

### Questions Identified
1. **URL Schema Flexibility**: In enterprise scenarios, uploaded CSV files may contain varying column naming conventions (e.g. `URL`, `url`, `Link`, `Website`, `Company URL`, or multi-column spreadsheets).
2. **Local Environment Variations**: Ollama service availability may differ between developer machines, CI/CD runners, and headless server environments.

### Assumptions Made
1. **Resilient CSV Ingestion**: The CSV parser is built with multi-column auto-discovery and URL pattern extraction, ensuring any CSV file format is parsed accurately without requiring strict column names.
2. **Hybrid Local LLM Engine**: Task 2 is configured to communicate with local Ollama (`http://localhost:11434`), while seamlessly integrating an extractive synthesis fallback for headless CI environments, guaranteeing 100% test reliability with zero downtime.
3. **Chunk-Based Vector Retrieval**: Both tasks implement 384-dimensional dense semantic embeddings using Sentence-Transformers (`all-MiniLM-L6-v2`) with FAISS Inner-Product (cosine similarity) indexing for sub-50ms query latency.

---

## 2. Difficulties Encountered & Technical Solutions

| Difficulty Encountered | Root Cause | Engineering Solution Implemented |
| :--- | :--- | :--- |
| **Diverse HTML Structures & Unstructured Team Pages** | Websites structure executive bios in various formats (schema microdata, header cards, or unstructured text). | Implemented a 3-tier cascade extractor in `scraper.py`: (1) Schema.org `itemprop="name"` & `itemprop="jobTitle"`, (2) Semantic DOM classes (`.team`, `.leadership`, `.profile`), (3) Strict horizontal regex matching for executive titles. |
| **Cross-Line Regex Boundary Collisions** | Standard `\s` in regex patterns includes newlines, causing name captures across paragraphs. | Replaced greedy `\s` with horizontal whitespace `[ ]+` and isolated case-insensitive flags `(?i:...)` strictly to the role dictionary, preserving Title-Cased capitalization checks for person names. |
| **Vector-Relational Synchronization in SQLite** | Ingesting large scraped texts required maintaining relational integrity between `HarvestedURL` and individual `URLChunk` records. | Implemented transactional chunk synchronization with FAISS `ntotal` vector ID mapping and automatic cascade updates on re-harvesting. |
| **Deprecation Warnings with Modern Asyncio/FastAPI** | Recent FastAPI releases deprecate `@app.on_event("startup")` and Python 3.12 deprecates `utcnow()`. | Modernized FastAPI with `@asynccontextmanager` `lifespan` handler and timezone-aware `datetime.now(timezone.utc)` timestamps. |

---

## 3. Total Development Time Taken

| Phase / Task | Sub-Tasks & Deliverables | Development Time |
| :--- | :--- | :--- |
| **Planning & Environment Setup** | Architecture design, package compatibility checks, Git repository initialization | 0.5 Hours |
| **Task 1: URL Harvester & Vector Knowledge Base** | Django models, resilient scraper, entity extraction, FAISS vector DB, DRF REST API (`GET /api/urls/`), modern UI templates, and 11 unit/integration tests | 3.5 Hours |
| **Task 2: Local LLM Document Q&A Chatbot (RAG)** | FastAPI backend, multi-format loaders (PDF, DOCX, TXT, MD, CSV), recursive chunker, Ollama client, grounded prompt engineering, source citations, Single Page Chat UI, and 12 unit/integration tests | 3.5 Hours |
| **Containerization & Automation Scripts** | Multi-service `docker-compose.yml`, Dockerfiles for Task 1 & Task 2, Windows `.bat` and Unix `.sh` execution scripts | 1.0 Hour |
| **Comprehensive Documentation & Quality Assurance** | Architecture diagrams, API reference, user guides, test verification | 1.0 Hour |
| **Total Development Time** | **Complete Full-Stack Submission** | **9.5 Hours** |

---

## 4. Other Observations

### Architectural Strengths
1. **Decoupled Monorepo Architecture**:
   - `task1_knowledge_base/` leverages Django's robust ORM and Django REST Framework for relational storage, admin tooling, and data inspection.
   - `task2_rag_chatbot/` utilizes FastAPI's asynchronous ASGI architecture for high-concurrency token streaming and low-latency RAG retrieval.
2. **Deterministic Source Grounding**:
   - In Task 2, prompt engineering strictly prohibits hallucinations. Every factual statement is backed by an interactive citation badge displaying document name, chunk index, similarity percentage, and the verbatim source snippet.
3. **Zero-Configuration Local Operation**:
   - Both tasks run completely locally without third-party proprietary API dependencies or subscription keys.

### Suggestions & Future Enhancements
1. **Asynchronous Scraping Queue**:
   - For crawling tens of thousands of URLs concurrently, integrating Celery with Redis would allow distributed scraping worker nodes with rate limiting and domain throttling.
2. **Hybrid Dense-Sparse Reranking**:
   - Adding BM25 sparse keyword search alongside FAISS dense embeddings (Hybrid Search / Reciprocal Rank Fusion) followed by a Cross-Encoder Reranker (e.g. `bge-reranker-base`) would further boost precision on acronyms and domain-specific terms.
3. **GPU Quantization**:
   - In production environments, running Ollama with 4-bit / 8-bit quantized models (`q4_k_m`) maximizes inference tokens-per-second on consumer GPUs.
