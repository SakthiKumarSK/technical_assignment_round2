"""
Django Admin registration for Task 1 models.
"""
from django.contrib import admin
from .models import HarvestedURL, URLChunk, ScrapingLog


@admin.register(HarvestedURL)
class HarvestedURLAdmin(admin.ModelAdmin):
    list_display = ('url', 'http_status_code', 'page_title', 'is_indexed', 'total_chunks', 'created_at')
    list_filter = ('http_status_code', 'is_indexed', 'created_at')
    search_fields = ('url', 'page_title', 'cleaned_text')
    readonly_fields = ('created_at', 'updated_at', 'indexed_at')


@admin.register(URLChunk)
class URLChunkAdmin(admin.ModelAdmin):
    list_display = ('id', 'harvested_url', 'chunk_index', 'vector_id', 'has_person_info', 'created_at')
    list_filter = ('has_person_info', 'created_at')
    search_fields = ('chunk_text', 'harvested_url__url')


@admin.register(ScrapingLog)
class ScrapingLogAdmin(admin.ModelAdmin):
    list_display = ('batch_id', 'url', 'status', 'http_status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('url', 'batch_id', 'message')
