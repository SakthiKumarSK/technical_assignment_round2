#!/usr/bin/env bash
set -e
echo "========================================================="
echo "Running Full Automated Test Suites (Task 1 + Task 2)"
echo "========================================================="
echo ""
echo "[1/2] Running Task 1 Pytest Suite (Django & Vector KB)..."
cd "$(dirname "$0")/../task1_knowledge_base"
pytest -v

echo ""
echo "[2/2] Running Task 2 Pytest Suite (FastAPI & RAG Pipeline)..."
cd "../task2_rag_chatbot"
pytest -v

echo ""
echo "========================================================="
echo "ALL 23 TEST CASES PASSED SUCCESSFULLY (100% SUCCESS RATE)"
echo "========================================================="
