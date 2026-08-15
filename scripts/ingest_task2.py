#!/usr/bin/env python
"""
Standalone ingestion CLI for Task 2 (Local LLM RAG Chatbot).

Regenerates the RAG FAISS vector store from a directory of documents without
going through the FastAPI upload endpoint. Uses the same code path as
`POST /api/documents/upload` via `app.rag_service.rag_service.ingest_document`.

Examples:
    python scripts/ingest_task2.py
    python scripts/ingest_task2.py --dir sample_data/documents --clear
    python scripts/ingest_task2.py --dir ~/my_docs --glob "*.pdf"
"""
import sys
import argparse
import logging
from pathlib import Path
from typing import List

REPO_ROOT = Path(__file__).resolve().parents[1]
TASK2_DIR = REPO_ROOT / 'task2_rag_chatbot'
sys.path.insert(0, str(TASK2_DIR))

from app.rag_service import rag_service  # noqa: E402
from app.vector_store import rag_vector_store  # noqa: E402

logging.basicConfig(level=logging.WARNING, format='%(levelname)s %(name)s: %(message)s')
logger = logging.getLogger('ingest_task2')

DEFAULT_GLOB = '*'
SUPPORTED_SUFFIXES = {'.pdf', '.docx', '.txt', '.md', '.csv'}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rebuild the Task 2 RAG FAISS vector store from a directory of documents."
    )
    parser.add_argument(
        '--dir',
        default=str(REPO_ROOT / 'sample_data' / 'documents'),
        help="Directory containing source documents (default: sample_data/documents)."
    )
    parser.add_argument(
        '--clear',
        action='store_true',
        help="Clear all existing documents and vectors before ingesting."
    )
    parser.add_argument(
        '--glob',
        default=DEFAULT_GLOB,
        help=f"Glob pattern for candidate files (default: {DEFAULT_GLOB!r}); "
             f"matches are filtered to {', '.join(sorted(SUPPORTED_SUFFIXES))}."
    )
    return parser.parse_args()


def resolve_dir(raw_path: str) -> Path:
    """Resolves a directory path relative to the repository root when not absolute."""
    doc_dir = Path(raw_path).expanduser()
    if not doc_dir.is_absolute():
        doc_dir = (REPO_ROOT / doc_dir).resolve()
    return doc_dir


def collect_files(doc_dir: Path, pattern: str) -> List[Path]:
    files = [
        p for p in sorted(doc_dir.glob(pattern))
        if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES
    ]
    return files


def main() -> int:
    args = parse_args()
    doc_dir = resolve_dir(args.dir)

    if not doc_dir.is_dir():
        print(f"ERROR: Document directory not found: {doc_dir}")
        return 1

    print("=========================================================")
    print("Task 2 Ingestion: Documents -> Chunks -> FAISS Vector Store")
    print("=========================================================")
    print(f"Source directory : {doc_dir}")
    print(f"Glob pattern     : {args.glob}")

    if args.clear:
        rag_vector_store.clear_all()
        print("Vector store cleared (all documents and vectors removed).")

    files = collect_files(doc_dir, args.glob)
    if not files:
        print(f"ERROR: No supported documents matched in {doc_dir}.")
        return 1

    print(f"Documents found  : {len(files)}")
    print("---------------------------------------------------------")

    total_chunks = 0
    ingested = 0
    failed = 0

    for position, file_path in enumerate(files, start=1):
        file_bytes = file_path.read_bytes()
        try:
            doc_info = rag_service.ingest_document(
                file_bytes=file_bytes,
                file_name=file_path.name,
                file_size=len(file_bytes)
            )
        except Exception as exc:
            failed += 1
            logger.error(f"Failed to ingest {file_path.name}: {exc}", exc_info=True)
            print(f"[{position}/{len(files)}] FAILED {file_path.name} | {exc}")
            continue

        total_chunks += doc_info.total_chunks
        ingested += 1
        print(
            f"[{position}/{len(files)}] {doc_info.file_name} "
            f"| doc_id={doc_info.doc_id} "
            f"| type={doc_info.file_type} "
            f"| chunks={doc_info.total_chunks} "
            f"| {doc_info.file_size_bytes} bytes"
        )

    stats = rag_vector_store.get_stats()

    print("---------------------------------------------------------")
    print("Ingestion Summary")
    print(f"  Documents ingested  : {ingested}")
    print(f"  Documents failed    : {failed}")
    print(f"  Chunks indexed      : {total_chunks}")
    print(f"  Total documents     : {stats['total_documents']}")
    print(f"  Total chunks        : {stats['total_chunks']}")
    print(f"  Total FAISS vectors : {stats['total_vectors']}")
    print("=========================================================")
    return 1 if failed and not ingested else 0


if __name__ == '__main__':
    sys.exit(main())
