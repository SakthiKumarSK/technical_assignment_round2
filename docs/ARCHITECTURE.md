# System Architecture & Technical Specifications

## 1. High-Level Architecture Overview

```
                                  +-------------------------------------------------------------+
                                  |                    User Web Interfaces                     |
                                  |   (Task 1: URL KB Dashboard / Task 2: Grounded RAG Chat)    |
                                  +------------------------------+------------------------------+
                                                                 |
                                 +-------------------------------+-------------------------------+
                                 |                                                               |
                                 v                                                               v
                 +-------------------------------+                               +-------------------------------+
                 |  Task 1 Backend (Django / DRF)|                               |   Task 2 Backend (FastAPI)    |
                 +---------------+---------------+                               +---------------+---------------+
                                 |                                                               |
               +-----------------+-----------------+                           +-----------------+-----------------+
               |                                   |                           |                                   |
               v                                   v                           v                                   v
+-------------------------------+   +-----------------------------+   +-----------------------------+   +-----------------------------+
|    URL Scraper & Extractor    |   | SQLite Relational Database  |   |   Document Loader & Chunker |   |    Ollama Local LLM API     |
| (Requests + BeautifulSoup4)   |   |   (Raw HTML & Metadata)     |   | (PDF, DOCX, TXT, MD, CSV)   |   |  (Llama-3 / Mistral / Phi-3)|
+---------------+---------------+   +--------------+--------------+   +--------------+--------------+   +--------------+--------------+
                |                                  |                                 |                                 |
                +-----------------+----------------+                                 +-----------------+---------------+
                                  |                                                                    |
                                  v                                                                    v
                  +-------------------------------+                                    +-------------------------------+
                  |  Task 1 FAISS Vector Store    |                                    |   Task 2 FAISS Vector Store   |
                  | (384-dim Cosine IndexFlatIP)  |                                    | (384-dim Cosine IndexFlatIP)  |
                  +-------------------------------+                                    +-------------------------------+
```

---

## 2. Task 1: Pipeline & Data Flow

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant UI as Django Web UI / REST API
    participant Scraper as Scraper & Entity Extractor
    participant SQLite as SQLite3 DB (models.py)
    participant FAISS as FAISS Vector Store

    User->>UI: Upload CSV containing URLs
    UI->>Scraper: Parse CSV & fetch URLs concurrently
    Scraper->>SQLite: Store raw HTML, status code & metadata
    Scraper->>FAISS: Generate 500-char chunks & 384-dim embeddings
    FAISS-->>SQLite: Map Vector IDs to HarvestedURL & URLChunk records
    User->>UI: Natural Language Query ("Who is the CEO?")
    UI->>FAISS: Compute query embedding & run Cosine search
    FAISS-->>UI: Return top-K relevant chunks & executive cards
    UI-->>User: Render structured response & raw data inspector
```

---

## 3. Task 2: Grounded RAG Pipeline

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant WebUI as Chatbot UI
    participant FastAPI as FastAPI API Server
    participant Chunker as Document Loader & Chunker
    participant VectorStore as FAISS Vector Store
    participant Ollama as Local Ollama LLM

    User->>WebUI: Upload Document (PDF/DOCX/TXT/MD/CSV)
    WebUI->>FastAPI: POST /api/documents/upload
    FastAPI->>Chunker: Extract text & create overlapping chunks
    Chunker->>VectorStore: Ingest vectors with metadata (doc_name, chunk_id, page)
    User->>WebUI: Ask question ("What are the Q3 milestones?")
    WebUI->>FastAPI: POST /api/chat
    FastAPI->>VectorStore: Similarity search (top_k=4)
    VectorStore-->>FastAPI: Return matching chunks + similarity scores
    FastAPI->>Ollama: Send strict grounding prompt with context chunks
    Ollama-->>FastAPI: Stream / return factual answer
    FastAPI-->>WebUI: Return Answer + Structured Source Citations
    WebUI-->>User: Render formatted answer with clickable source badges
```

---

## 4. SQLite Schema (Task 1)

### `HarvestedURL` Table
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | BigAutoField (PK) | Unique URL identifier |
| `url` | URLField (2048) | Crawled target URL (Unique) |
| `http_status_code` | Integer | HTTP Response Code (e.g. 200, 404) |
| `raw_content` | TextField | Full raw HTML payload |
| `page_title` | CharField (512) | HTML `<title>` or OpenGraph title |
| `meta_description` | TextField | Meta description content |
| `cleaned_text` | TextField | Cleaned text extracted from DOM |
| `metadata_json` | JSONField | Response headers, content length, latency |
| `executive_details` | JSONField | Extracted persons, leadership roles & bios |
| `is_indexed` | Boolean | Whether vector embeddings are stored in FAISS |
| `total_chunks` | Integer | Total text chunks created |
| `created_at` | DateTimeField | Timestamp of harvesting |

### `URLChunk` Table
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | BigAutoField (PK) | Chunk primary key |
| `harvested_url_id` | ForeignKey | References `HarvestedURL.id` |
| `chunk_index` | Integer | Zero-based chunk position |
| `chunk_text` | TextField | 500-char semantic text chunk |
| `chunk_hash` | CharField (64) | SHA-256 hash for deduplication |
| `vector_id` | Integer | Corresponds to FAISS index vector index |
| `has_person_info` | Boolean | Flag for executive entity presence |
