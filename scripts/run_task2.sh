#!/usr/bin/env bash
set -e
echo "========================================================="
echo "Starting Task 2: Local LLM Document Q&A Chatbot (FastAPI + RAG)"
echo "========================================================="
echo "Web Chatbot UI: http://127.0.0.1:8001/"
echo "Swagger API Docs: http://127.0.0.1:8001/docs"
cd "$(dirname "$0")/../task2_rag_chatbot"
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
