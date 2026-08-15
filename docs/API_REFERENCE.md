# REST API Reference Manual

Complete API specifications for both Task 1 (Django REST Framework) and Task 2 (FastAPI).

---

## Task 1: URL Knowledge Base REST API

### 1. `GET /api/urls/` (Primary Assignment Requirement)
Retrieves a paginated list of harvested URLs with raw HTML, status codes, and metadata.

**Query Parameters (Optional):**
- `status_code` (int): Filter by HTTP status code (e.g. `200`, `404`)
- `is_indexed` (bool): Filter by FAISS indexing status (`true`/`false`)
- `q` (string): Keyword search in title or URL

**Example Request:**
```bash
curl -X GET "http://127.0.0.1:8000/api/urls/" -H "Accept: application/json"
```

**Example Response (200 OK):**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "url": "https://en.wikipedia.org/wiki/Sundar_Pichai",
      "http_status_code": 200,
      "raw_content": "<!DOCTYPE html><html>...</html>",
      "page_title": "Sundar Pichai - Wikipedia",
      "meta_description": "Sundar Pichai is an Indian-American business executive...",
      "cleaned_text": "Sundar Pichai is the Chief Executive Officer of Alphabet and Google...",
      "metadata_json": {
        "content_type": "text/html; charset=UTF-8",
        "content_length": 184520,
        "latency_seconds": 0.34
      },
      "executive_details": [
        {
          "name": "Sundar Pichai",
          "role": "Chief Executive Officer",
          "bio": "Sundar Pichai is the CEO of Alphabet and Google...",
          "source": "text_pattern"
        }
      ],
      "is_indexed": true,
      "chunks_count": 8,
      "created_at": "2026-08-15T12:00:00Z"
    }
  ]
}
```

---

### 2. `POST /api/upload/`
Upload a CSV file containing URLs for batch scraping and automatic vector indexing.

```bash
curl -X POST "http://127.0.0.1:8000/api/upload/" \
  -F "file=@sample_data/executive_urls.csv"
```

---

### 3. `POST /api/search/`
Perform semantic vector search on the harvested knowledge base.

```bash
curl -X POST "http://127.0.0.1:8000/api/search/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Who is the CEO of Alphabet and Google?",
    "top_k": 3
  }'
```

---

## Task 2: Grounded RAG Chatbot REST API

### 1. `POST /api/chat`
Execute a grounded Q&A query against uploaded documents.

**Example Request:**
```bash
curl -X POST "http://127.0.0.1:8001/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the strategic AI roadmap outlined in the strategy document?",
    "model": "llama3",
    "top_k": 4,
    "temperature": 0.2
  }'
```

**Example Response (200 OK):**
```json
{
  "question": "What is the strategic AI roadmap outlined in the strategy document?",
  "answer": "Based on the provided strategy document, Apex Global is allocating $120M towards GPU compute clusters...",
  "model_used": "llama3",
  "citations": [
    {
      "document_id": "8f3b2a1c",
      "document_name": "ai_strategy_roadmap_2026.md",
      "chunk_index": 0,
      "page_number": 1,
      "similarity_score": 0.892,
      "similarity_percentage": 89.2,
      "snippet": "Apex Global is transforming its enterprise software suite by integrating autonomous agent architectures..."
    }
  ],
  "latency_seconds": 0.45,
  "retrieved_chunks_count": 4
}
```

---

### 2. `POST /api/documents/upload`
Upload and index multi-format files (PDF, DOCX, TXT, MD, CSV).

```bash
curl -X POST "http://127.0.0.1:8001/api/documents/upload" \
  -F "files=@sample_data/documents/ai_strategy_roadmap_2026.md" \
  -F "files=@sample_data/documents/executive_profiles_and_roles.txt"
```

---

### 3. `GET /api/health`
Check backend status and Ollama model availability.

```bash
curl -X GET "http://127.0.0.1:8001/api/health"
```
