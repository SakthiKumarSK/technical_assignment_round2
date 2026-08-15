"""
Unit tests for URL Scraper and CSV Parser (Task 1).
"""
import pytest
from unittest.mock import patch, MagicMock
from harvester.scraper import parse_csv_for_urls, scrape_url, extract_executive_details
from bs4 import BeautifulSoup


def test_parse_csv_for_urls_single_column():
    csv_text = "https://example.com/one\nhttps://example.com/two\nhttps://example.com/three"
    urls = parse_csv_for_urls(csv_text)
    assert len(urls) == 3
    assert "https://example.com/one" in urls
    assert "https://example.com/two" in urls
    assert "https://example.com/three" in urls


def test_parse_csv_for_urls_with_header():
    csv_text = "Company,Website,Category\nAcme Corp,https://acme.org,Tech\nBeta Inc,https://beta.io,AI"
    urls = parse_csv_for_urls(csv_text)
    assert len(urls) == 2
    assert "https://acme.org" in urls
    assert "https://beta.io" in urls


def test_extract_executive_details():
    html = """
    <html>
      <body>
        <div class="team-card">
          <h3>Alice Johnson</h3>
          <p>Alice Johnson is the Chief Executive Officer leading our cloud computing strategy.</p>
        </div>
        <div class="leadership-profile">
          <h4>Bob Smith</h4>
          <p>Chief Technology Officer with 15 years in AI research.</p>
        </div>
      </body>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    execs = extract_executive_details(soup, "Alice Johnson Chief Executive Officer Bob Smith Chief Technology Officer")
    assert len(execs) >= 1
    names = [e['name'] for e in execs]
    assert "Alice Johnson" in names or "Bob Smith" in names


@patch('harvester.scraper.requests.get')
def test_scrape_url_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = """
    <html>
      <head><title>Sample Leadership Page</title></head>
      <body>
        <h1>Executive Leadership</h1>
        <p>Jane Doe is the Founder and CEO of FutureAI.</p>
      </body>
    </html>
    """
    mock_resp.headers = {'Content-Type': 'text/html'}
    mock_resp.url = 'https://futureai.test'
    mock_resp.history = []
    mock_get.return_value = mock_resp

    result = scrape_url('https://futureai.test')
    assert result['http_status_code'] == 200
    assert result['page_title'] == 'Sample Leadership Page'
    assert 'Jane Doe' in result['cleaned_text']
    assert len(result['executive_details']) >= 1
    assert result['executive_details'][0]['name'] == 'Jane Doe'
