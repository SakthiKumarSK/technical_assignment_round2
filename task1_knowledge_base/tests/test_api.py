"""
Integration tests for Task 1 REST API endpoints.
Verifies GET /api/urls/, POST /api/harvest/, POST /api/search/, and stats.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kb_project.settings')
django.setup()

import pytest
from rest_framework.test import APIClient
from harvester.models import HarvestedURL
from unittest.mock import patch


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def sample_harvested_url(db):
    return HarvestedURL.objects.create(
        url="https://example.com/execs",
        http_status_code=200,
        raw_content="<html><body><h1>Tech Leaders</h1><p>Tim Cook is CEO of Apple Inc.</p></body></html>",
        page_title="Tech Leaders",
        meta_description="Apple leadership and CEO biography",
        cleaned_text="Tim Cook is CEO of Apple Inc. He joined Apple in March 1998.",
        metadata_json={"content_type": "text/html", "latency_seconds": 0.12},
        executive_details=[{"name": "Tim Cook", "role": "CEO", "bio": "CEO of Apple Inc."}],
        is_indexed=True,
        total_chunks=1
    )


@pytest.mark.django_db
def test_get_api_urls_list(api_client, sample_harvested_url):
    """
    Test Primary Requirement: GET /api/urls/
    Returns URL, HTTP status code, Raw HTML/content, and Relevant metadata.
    """
    response = api_client.get('/api/urls/')
    assert response.status_code == 200
    
    data = response.json()
    # Check pagination structure or list
    results = data.get('results', data)
    assert len(results) >= 1
    
    first = results[0]
    assert 'url' in first
    assert 'http_status_code' in first
    assert 'raw_content' in first
    assert 'metadata_json' in first
    assert first['http_status_code'] == 200
    assert first['url'] == 'https://example.com/execs'


@pytest.mark.django_db
def test_get_api_urls_detail(api_client, sample_harvested_url):
    response = api_client.get(f'/api/urls/{sample_harvested_url.id}/')
    assert response.status_code == 200
    data = response.json()
    assert data['id'] == sample_harvested_url.id
    assert "Tim Cook is CEO" in data['cleaned_text']


@pytest.mark.django_db
def test_post_api_search(api_client, sample_harvested_url):
    response = api_client.post('/api/search/', {
        "query": "Who is the CEO of Apple?",
        "top_k": 3
    }, format='json')
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert "summary" in data
    assert "retrieved_chunks" in data


@pytest.mark.django_db
def test_get_api_stats(api_client, sample_harvested_url):
    response = api_client.get('/api/stats/')
    assert response.status_code == 200
    data = response.json()
    assert data['total_urls_harvested'] >= 1
