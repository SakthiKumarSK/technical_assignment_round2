#!/usr/bin/env bash
set -e
echo "========================================================="
echo "Regenerating All Vector Stores (Task 1 + Task 2)"
echo "========================================================="
echo ""
echo "[1/2] Task 1: Harvesting sample CSV URLs into SQLite + FAISS..."
cd "$(dirname "$0")/.."
python scripts/ingest_task1.py --csv sample_data/executive_urls.csv --reset

echo ""
echo "[2/2] Task 2: Ingesting sample documents into RAG FAISS vector store..."
python scripts/ingest_task2.py --dir sample_data/documents --clear

echo ""
echo "========================================================="
echo "ALL MODEL ARTIFACTS REGENERATED SUCCESSFULLY"
echo "========================================================="
