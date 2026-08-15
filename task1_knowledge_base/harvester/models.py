"""
Data models for URL Harvesting, SQLite persistence, and Vector Database metadata.
"""
from django.db import models


class HarvestedURL(models.Model):
    """
    Stores raw and structured harvested content from uploaded URLs.
    Fulfills Task 1 requirement: store raw scraped content in SQLite database
    and expose via GET /api/urls/.
    """
    url = models.URLField(max_length=2048, unique=True, db_index=True)
    http_status_code = models.IntegerField(null=True, blank=True, help_text="HTTP response status code (e.g., 200, 404)")
    raw_content = models.TextField(help_text="Raw HTML or raw response body from the URL")
    page_title = models.CharField(max_length=512, blank=True, default="")
    meta_description = models.TextField(blank=True, default="")
    cleaned_text = models.TextField(blank=True, default="", help_text="Cleaned, human-readable text extracted from HTML")
    metadata_json = models.JSONField(default=dict, blank=True, help_text="Response headers, content type, scrape latency, etc.")
    executive_details = models.JSONField(default=list, blank=True, help_text="Extracted person names, roles, executive bios, and leadership information")
    
    # Vector indexing tracking
    is_indexed = models.BooleanField(default=False, db_index=True, help_text="Whether this URL has been ingested into FAISS vector database")
    indexed_at = models.DateTimeField(null=True, blank=True)
    total_chunks = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Harvested URL'
        verbose_name_plural = 'Harvested URLs'

    def __str__(self):
        status = f"[{self.http_status_code}]" if self.http_status_code else "[PENDING]"
        return f"{status} {self.url}"


class URLChunk(models.Model):
    """
    Individual text chunks generated for vector database ingestion.
    Enables fine-grained chunk-based retrieval and relevance scoring.
    """
    harvested_url = models.ForeignKey(HarvestedURL, on_delete=models.CASCADE, related_name='chunks')
    chunk_index = models.IntegerField()
    chunk_text = models.TextField()
    chunk_hash = models.CharField(max_length=64, blank=True, default="")
    vector_id = models.IntegerField(null=True, blank=True, help_text="Index ID in the FAISS vector database")
    has_person_info = models.BooleanField(default=False, help_text="Flag indicating executive or person entity present")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['harvested_url', 'chunk_index']
        unique_together = ('harvested_url', 'chunk_index')
        verbose_name = 'URL Chunk'
        verbose_name_plural = 'URL Chunks'

    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.harvested_url.url}"


class ScrapingLog(models.Model):
    """
    Audit log for batch harvesting runs and ingestion processes.
    """
    batch_id = models.CharField(max_length=64, db_index=True)
    url = models.URLField(max_length=2048)
    status = models.CharField(max_length=32, choices=[
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('SKIPPED', 'Skipped'),
    ], default='PENDING')
    http_status = models.IntegerField(null=True, blank=True)
    message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.status}] {self.url} ({self.created_at})"
