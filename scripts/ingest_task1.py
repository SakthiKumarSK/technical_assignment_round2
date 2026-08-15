#!/usr/bin/env python
"""
Standalone ingestion CLI for Task 1 (URL Knowledge Base).

Regenerates the SQLite records and the FAISS vector index from a CSV of URLs
without going through the Django web UI or the REST API. The scraping and
indexing logic is the exact same code path used by
`harvester.api_views.CSVUploadAPIView`.

Examples:
    python scripts/ingest_task1.py
    python scripts/ingest_task1.py --csv sample_data/tech_leadership_batch.csv --reset
    python scripts/ingest_task1.py --limit 3 --skip-existing
"""
import os
import sys
import uuid
import argparse
import logging
from pathlib import Path
from typing import List

REPO_ROOT = Path(__file__).resolve().parents[1]
TASK1_DIR = REPO_ROOT / 'task1_knowledge_base'
sys.path.insert(0, str(TASK1_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kb_project.settings')

import django  # noqa: E402

django.setup()

from django.core.management import call_command  # noqa: E402

from harvester.models import HarvestedURL, ScrapingLog  # noqa: E402
from harvester.scraper import parse_csv_for_urls, scrape_url  # noqa: E402
from harvester.vector_db import kb_vector_db  # noqa: E402

logging.basicConfig(level=logging.WARNING, format='%(levelname)s %(name)s: %(message)s')
logger = logging.getLogger('ingest_task1')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rebuild the Task 1 knowledge base (SQLite + FAISS) from a CSV of URLs."
    )
    parser.add_argument(
        '--csv',
        default=str(REPO_ROOT / 'sample_data' / 'executive_urls.csv'),
        help="Path to the CSV file containing URLs (default: sample_data/executive_urls.csv)."
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help="Only process the first N URLs found in the CSV."
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help="Delete and recreate the FAISS index before ingesting."
    )
    parser.add_argument(
        '--skip-existing',
        action='store_true',
        help="Skip URLs that are already harvested and indexed in SQLite."
    )
    return parser.parse_args()


def resolve_csv_path(raw_path: str) -> Path:
    """Resolves a CSV path relative to the repository root when not absolute."""
    csv_path = Path(raw_path)
    if not csv_path.is_absolute():
        csv_path = (REPO_ROOT / csv_path).resolve()
    return csv_path


def load_urls(csv_path: Path, limit: int = None) -> List[str]:
    content = csv_path.read_text(encoding='utf-8', errors='ignore')
    urls = parse_csv_for_urls(content)
    if limit is not None:
        urls = urls[:limit]
    return urls


def main() -> int:
    args = parse_args()
    csv_path = resolve_csv_path(args.csv)

    if not csv_path.exists():
        print(f"ERROR: CSV file not found: {csv_path}")
        return 1

    print("=========================================================")
    print("Task 1 Ingestion: CSV URLs -> SQLite -> FAISS Vector Index")
    print("=========================================================")
    print(f"CSV source : {csv_path}")

    # Guarantees the SQLite schema exists on a fresh clone.
    call_command('migrate', interactive=False, verbosity=0)

    if args.reset:
        kb_vector_db.reset_index()
        print("FAISS index reset (existing vectors and metadata deleted).")

    urls = load_urls(csv_path, args.limit)
    if not urls:
        print("ERROR: No valid URLs detected in the CSV file.")
        return 1

    print(f"URLs found : {len(urls)}")
    print("---------------------------------------------------------")

    batch_id = str(uuid.uuid4())[:8]
    total_chunks = 0
    processed = 0
    skipped = 0

    for position, url in enumerate(urls, start=1):
        if args.skip_existing and HarvestedURL.objects.filter(url=url, is_indexed=True).exists():
            skipped += 1
            print(f"[{position}/{len(urls)}] SKIP (already indexed) {url}")
            continue

        scrape_res = scrape_url(url)

        url_obj, _ = HarvestedURL.objects.update_or_create(
            url=scrape_res['url'],
            defaults={
                'http_status_code': scrape_res['http_status_code'],
                'raw_content': scrape_res['raw_content'],
                'page_title': scrape_res['page_title'],
                'meta_description': scrape_res['meta_description'],
                'cleaned_text': scrape_res['cleaned_text'],
                'metadata_json': scrape_res['metadata_json'],
                'executive_details': scrape_res['executive_details'],
            }
        )

        chunks_indexed = kb_vector_db.ingest_url(url_obj)
        total_chunks += chunks_indexed
        processed += 1

        ScrapingLog.objects.create(
            batch_id=batch_id,
            url=url,
            status='SUCCESS' if scrape_res['http_status_code'] == 200 else 'FAILED',
            http_status=scrape_res['http_status_code'],
            message=f"Scraped {len(scrape_res['cleaned_text'])} chars. Indexed {chunks_indexed} chunks."
        )

        print(
            f"[{position}/{len(urls)}] {url} "
            f"| HTTP {scrape_res['http_status_code']} "
            f"| chunks={chunks_indexed} "
            f"| executives={len(url_obj.executive_details)}"
        )

    faiss_vectors = kb_vector_db.index.ntotal if kb_vector_db.index else 0

    print("---------------------------------------------------------")
    print("Ingestion Summary")
    print(f"  Batch ID              : {batch_id}")
    print(f"  URLs in CSV           : {len(urls)}")
    print(f"  URLs processed        : {processed}")
    print(f"  URLs skipped          : {skipped}")
    print(f"  Chunks indexed        : {total_chunks}")
    print(f"  Total FAISS vectors   : {faiss_vectors}")
    print(f"  Total URLs in SQLite  : {HarvestedURL.objects.count()}")
    print("=========================================================")
    return 0


if __name__ == '__main__':
    sys.exit(main())
