"""
Django Web UI Views for Task 1:
- Home Dashboard
- CSV Upload & Harvesting Interface
- Natural Language Semantic Search Interface
- SQLite Raw Data Inspector
- Individual URL Detailed Inspector
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import TemplateView
from .models import HarvestedURL, URLChunk, ScrapingLog
from .scraper import scrape_url, parse_csv_for_urls
from .vector_db import kb_vector_db
from .query_engine import execute_semantic_query


def home_view(request):
    """Dashboard homepage showing system metrics and quick actions."""
    total_urls = HarvestedURL.objects.count()
    indexed_urls = HarvestedURL.objects.filter(is_indexed=True).count()
    total_chunks = URLChunk.objects.count()
    recent_urls = HarvestedURL.objects.all()[:6]
    faiss_count = kb_vector_db.index.ntotal if kb_vector_db.index else 0

    return render(request, 'home.html', {
        'total_urls': total_urls,
        'indexed_urls': indexed_urls,
        'total_chunks': total_chunks,
        'faiss_count': faiss_count,
        'recent_urls': recent_urls,
    })


def upload_view(request):
    """Web interface for uploading CSV files or submitting URLs."""
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        raw_urls_text = request.POST.get('raw_urls', '')
        urls = []

        if csv_file:
            content = csv_file.read().decode('utf-8', errors='ignore')
            urls = parse_csv_for_urls(content)
        elif raw_urls_text.strip():
            urls = parse_csv_for_urls(raw_urls_text)

        if not urls:
            messages.error(request, "No valid URLs found. Please upload a valid CSV file or paste URLs.")
            return render(request, 'upload.html')

        total_scraped = 0
        total_chunks = 0

        for url in urls:
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
            chunks = kb_vector_db.ingest_url(url_obj)
            total_chunks += chunks
            total_scraped += 1

        messages.success(request, f"Successfully processed {total_scraped} URLs and ingested {total_chunks} chunks into Vector DB!")
        return redirect('url_list')

    return render(request, 'upload.html')


def search_view(request):
    """Natural Language & Semantic Search Interface."""
    query = request.GET.get('q', '').strip()
    top_k = int(request.GET.get('top_k', 5))
    search_results = None

    if query:
        search_results = execute_semantic_query(query=query, top_k=top_k)

    return render(request, 'search.html', {
        'query': query,
        'top_k': top_k,
        'results': search_results,
        'total_vectors': kb_vector_db.index.ntotal if kb_vector_db.index else 0
    })


def url_list_view(request):
    """Data table for viewing raw harvested SQLite database entries."""
    urls = HarvestedURL.objects.all().order_by('-created_at')
    return render(request, 'url_list.html', {
        'urls': urls,
        'total_count': urls.count()
    })


def url_detail_view(request, pk):
    """Detailed view of a single harvested URL."""
    url_obj = get_object_or_404(HarvestedURL, pk=pk)
    chunks = url_obj.chunks.all().order_by('chunk_index')
    return render(request, 'url_detail.html', {
        'url_obj': url_obj,
        'chunks': chunks
    })


def trigger_ingest_view(request):
    """Manually re-ingest all unindexed URLs."""
    total_new = kb_vector_db.ingest_all_unindexed()
    messages.info(request, f"Ingested {total_new} chunks into FAISS vector database.")
    return redirect('home')
