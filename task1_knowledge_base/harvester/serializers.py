"""
Django REST Framework serializers for Task 1 REST API endpoints.
"""
from rest_framework import serializers
from .models import HarvestedURL, URLChunk, ScrapingLog


class URLChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = URLChunk
        fields = ['id', 'chunk_index', 'chunk_text', 'chunk_hash', 'vector_id', 'has_person_info', 'created_at']


class HarvestedURLSerializer(serializers.ModelSerializer):
    """
    Serializes harvested URL data meeting Task 1 REST API specification:
    - URL
    - HTTP status code
    - Raw HTML/content
    - Relevant metadata
    """
    chunks_count = serializers.IntegerField(source='total_chunks', read_only=True)

    class Meta:
        model = HarvestedURL
        fields = [
            'id',
            'url',
            'http_status_code',
            'raw_content',
            'page_title',
            'meta_description',
            'cleaned_text',
            'metadata_json',
            'executive_details',
            'is_indexed',
            'chunks_count',
            'indexed_at',
            'created_at',
            'updated_at'
        ]


class HarvestedURLListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for URL list endpoint with content preview.
    """
    raw_content_preview = serializers.SerializerMethodField()

    class Meta:
        model = HarvestedURL
        fields = [
            'id',
            'url',
            'http_status_code',
            'page_title',
            'raw_content',
            'raw_content_preview',
            'metadata_json',
            'executive_details',
            'is_indexed',
            'total_chunks',
            'created_at'
        ]

    def get_raw_content_preview(self, obj):
        if obj.raw_content:
            return obj.raw_content[:200] + ('...' if len(obj.raw_content) > 200 else '')
        return ''


class SemanticSearchRequestSerializer(serializers.Serializer):
    query = serializers.CharField(required=True, min_length=1, max_length=1000)
    top_k = serializers.IntegerField(default=5, min_value=1, max_value=20)
    filter_person = serializers.BooleanField(default=False)
    model = serializers.CharField(default='llama3.2', required=False)


class URLHarvestRequestSerializer(serializers.Serializer):
    urls = serializers.ListField(
        child=serializers.URLField(),
        required=True,
        allow_empty=False
    )
    auto_index = serializers.BooleanField(default=True)
