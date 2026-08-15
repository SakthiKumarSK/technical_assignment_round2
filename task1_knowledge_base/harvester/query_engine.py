"""
Query & Retrieval Engine for Task 1.
Combines FAISS semantic search, structured executive extraction,
and LLM synthesis (Ollama / Local Structured Synthesizer).
"""
import time
import logging
import requests
from typing import Dict, Any, List
from .vector_db import kb_vector_db

logger = logging.getLogger(__name__)


def try_ollama_summarize(query: str, context: str, model: str = "llama3") -> str:
    """
    Attempts to call local Ollama instance for natural language synthesis.
    Returns generated text or None if Ollama is unreachable.
    """
    prompt = (
        f"You are a helpful knowledge assistant. Based on the following harvested web data, "
        f"answer the query with specific focus on executives, leadership roles, and company bios.\n\n"
        f"Context:\n{context}\n\n"
        f"Query: {query}\n\n"
        f"Provide a clear, structured, and factual response:"
    )

    try:
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2}
            },
            timeout=8
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("response", "").strip()
    except Exception:
        pass
    return None


def generate_extractive_summary(query: str, chunks: List[Dict[str, Any]], executives: List[Dict[str, Any]]) -> str:
    """
    Generates a structured, highly informative response without requiring an active external LLM daemon.
    Guarantees fast, robust, and grounded retrieval presentation.
    """
    if not chunks:
        return "No relevant information found in the harvested knowledge base. Please upload CSV URLs or try another query."

    parts = []
    if executives:
        parts.append("### Key Leadership & Executive Findings:")
        for exec_info in executives[:4]:
            name = exec_info.get("name", "Unknown")
            role = exec_info.get("role", "Leadership")
            bio = exec_info.get("bio", "").replace("\n", " ").strip()
            source = exec_info.get("source_url", "")
            parts.append(f"- **{name}** ({role}): {bio[:200]}... [Source: {source}]")
        parts.append("\n")

    parts.append("### Summary of Retrieved Context:")
    top_chunk = chunks[0]["chunk_text"].replace("\n", " ").strip()
    parts.append(f"{top_chunk}")

    if len(chunks) > 1:
        sec_chunk = chunks[1]["chunk_text"].replace("\n", " ").strip()
        parts.append(f"\n**Additional Context:** {sec_chunk}")

    return "\n".join(parts)


def execute_semantic_query(query: str, top_k: int = 5, model_name: str = "llama3") -> Dict[str, Any]:
    """
    Orchestrates vector search, executive entity aggregation, and answer synthesis.
    """
    start_time = time.time()
    
    # 1. Vector similarity search
    results = kb_vector_db.search(query=query, top_k=top_k)
    
    # 2. Extract and deduplicate person/executive details from matched results
    executives_found = []
    seen_exec_names = set()

    for item in results:
        url_execs = item.get('executive_details', [])
        source_url = item.get('url', '')
        for ex in url_execs:
            name = ex.get('name')
            if name and name not in seen_exec_names:
                seen_exec_names.add(name)
                ex_copy = dict(ex)
                ex_copy['source_url'] = source_url
                executives_found.append(ex_copy)

    # 3. Context assembly
    context_text = "\n\n---\n\n".join([
        f"Source ({r.get('url')} - {r.get('page_title')}):\n{r.get('chunk_text')}"
        for r in results
    ])

    # 4. Generate answer synthesis
    llm_summary = try_ollama_summarize(query, context_text, model=model_name)
    if not llm_summary:
        llm_summary = generate_extractive_summary(query, results, executives_found)

    latency = round(time.time() - start_time, 3)

    return {
        "query": query,
        "summary": llm_summary,
        "relevant_executives": executives_found,
        "retrieved_chunks": results,
        "total_results": len(results),
        "total_kb_vectors": kb_vector_db.index.ntotal if kb_vector_db.index else 0,
        "latency_seconds": latency
    }
