"""
Django REST Framework API views for Task 1.
Implements:
- GET /api/urls/ (Primary Requirement)
- GET /api/urls/<id>/
- POST /api/upload/
- POST /api/harvest/
- POST /api/ingest/
- POST /api/search/
- GET /api/stats/
"""
import uuid
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import HarvestedURL, URLChunk, ScrapingLog
from .serializers import (
    HarvestedURLSerializer,
    HarvestedURLListSerializer,
    SemanticSearchRequestSerializer,
    URLHarvestRequestSerializer
)
from .scraper import scrape_url, parse_csv_for_urls
from .vector_db import kb_vector_db
from .query_engine import execute_semantic_query

logger = logging.getLogger(__name__)


class HarvestedURLListView(ListAPIView):
    """
    GET /api/urls/
    Task 1 Requirement: Expose a REST API endpoint returning harvested URL information:
    - URL
    - HTTP status code
    - Raw HTML/content
    - Relevant metadata
    """
    queryset = HarvestedURL.objects.all().order_by('-created_at')
    serializer_class = HarvestedURLSerializer
    parser_classes = [JSONParser, FormParser]

    def get_queryset(self):
        qs = super().get_queryset()
        status_code = self.request.query_params.get('status_code')
        indexed = self.request.query_params.get('is_indexed')
        q = self.request.query_params.get('q')

        if status_code:
            qs = qs.filter(http_status_code=status_code)
        if indexed is not None:
            qs = qs.filter(is_indexed=(indexed.lower() == 'true'))
        if q:
            qs = qs.filter(page_title__icontains=q) | qs.filter(url__icontains=q)
        return qs


class HarvestedURLDetailView(RetrieveAPIView):
    """
    GET /api/urls/<int:pk>/
    Retrieve full details of a single harvested URL including chunks.
    """
    queryset = HarvestedURL.objects.all()
    serializer_class = HarvestedURLSerializer


class CSVUploadAPIView(APIView):
    """
    POST /api/upload/
    Accepts CSV file upload, parses URLs, scrapes them, stores raw content in SQLite,
    and automatically indexes them into the FAISS vector database.
    """
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response(
                {"error": "No file provided. Please attach a 'file' parameter."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            content = file_obj.read().decode('utf-8', errors='ignore')
            urls = parse_csv_for_urls(content)

            if not urls:
                return Response(
                    {"error": "No valid URLs detected in uploaded file."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            batch_id = str(uuid.uuid4())[:8]
            processed_records = []
            new_chunks_count = 0

            for url in urls:
                scrape_res = scrape_url(url)
                
                # Save / update in SQLite database
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

                # Vector indexing into FAISS
                chunks_indexed = kb_vector_db.ingest_url(url_obj)
                new_chunks_count += chunks_indexed

                ScrapingLog.objects.create(
                    batch_id=batch_id,
                    url=url,
                    status='SUCCESS' if scrape_res['http_status_code'] == 200 else 'FAILED',
                    http_status=scrape_res['http_status_code'],
                    message=f"Scraped {len(scrape_res['cleaned_text'])} chars. Indexed {chunks_indexed} chunks."
                )

                processed_records.append({
                    "id": url_obj.id,
                    "url": url_obj.url,
                    "status_code": url_obj.http_status_code,
                    "title": url_obj.page_title,
                    "chunks_indexed": chunks_indexed,
                    "executives_count": len(url_obj.executive_details)
                })

            return Response({
                "message": f"Successfully processed {len(urls)} URLs.",
                "batch_id": batch_id,
                "total_urls": len(urls),
                "total_chunks_indexed": new_chunks_count,
                "processed_urls": processed_records
            }, status=status.HTTP_201_CREATED)

        except Exception as exc:
            logger.error(f"Error processing CSV upload: {exc}", exc_info=True)
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class URLHarvestAPIView(APIView):
    """
    POST /api/harvest/
    Harvests a provided list of raw URLs directly via JSON payload.
    """
    parser_classes = [JSONParser]

    def post(self, request, *args, **kwargs):
        serializer = URLHarvestRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        urls = serializer.validated_data['urls']
        auto_index = serializer.validated_data.get('auto_index', True)
        results = []

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

            chunks_indexed = 0
            if auto_index:
                chunks_indexed = kb_vector_db.ingest_url(url_obj)

            results.append({
                "id": url_obj.id,
                "url": url_obj.url,
                "status_code": url_obj.http_status_code,
                "title": url_obj.page_title,
                "chunks_indexed": chunks_indexed,
                "executives": url_obj.executive_details
            })

        return Response({
            "message": f"Harvested {len(urls)} URLs.",
            "results": results
        }, status=status.HTTP_200_OK)


class IngestVectorDBAPIView(APIView):
    """
    POST /api/ingest/
    Manually triggers vector database ingestion for all unindexed records.
    """
    def post(self, request, *args, **kwargs):
        total_chunks = kb_vector_db.ingest_all_unindexed()
        return Response({
            "message": f"Successfully ingested unindexed URLs into FAISS.",
            "total_new_chunks": total_chunks,
            "total_faiss_vectors": kb_vector_db.index.ntotal if kb_vector_db.index else 0
        }, status=status.HTTP_200_OK)


class SemanticSearchAPIView(APIView):
    """
    POST /api/search/
    Executes semantic search against the FAISS vector database.
    """
    parser_classes = [JSONParser]

    def post(self, request, *args, **kwargs):
        serializer = SemanticSearchRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        query = serializer.validated_data['query']
        top_k = serializer.validated_data.get('top_k', 5)
        model = serializer.validated_data.get('model', 'llama3.2')

        search_response = execute_semantic_query(query=query, top_k=top_k, model_name=model)
        return Response(search_response, status=status.HTTP_200_OK)


class SystemStatsAPIView(APIView):
    """
    GET /api/stats/
    Returns overview statistics of harvested URLs and vector store.
    """
    def get(self, request, *args, **kwargs):
        total_urls = HarvestedURL.objects.count()
        total_indexed = HarvestedURL.objects.filter(is_indexed=True).count()
        total_chunks = URLChunk.objects.count()
        faiss_vectors = kb_vector_db.index.ntotal if kb_vector_db.index else 0

        return Response({
            "total_urls_harvested": total_urls,
            "total_urls_indexed": total_indexed,
            "total_chunks_stored": total_chunks,
            "faiss_vector_count": faiss_vectors,
            "vector_index_status": "READY" if faiss_vectors > 0 else "EMPTY"
        })
