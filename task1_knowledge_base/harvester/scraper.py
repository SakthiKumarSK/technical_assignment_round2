"""
Resilient URL Scraper and Content Extraction Engine.
Extracts raw HTML, cleaned text, metadata, and structured executive/person details.
"""
import re
import time
import csv
import io
import logging
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Common leadership / executive role titles for entity extraction
LEADERSHIP_ROLES = [
    r"Chief Executive Officer", r"CEO",
    r"Chief Technology Officer", r"CTO",
    r"Chief Operating Officer", r"COO",
    r"Chief Financial Officer", r"CFO",
    r"Chief Information Officer", r"CIO",
    r"Chief Product Officer", r"CPO",
    r"Chief Marketing Officer", r"CMO",
    r"President", r"Founder", r"Co-Founder",
    r"Managing Director", r"Executive Director",
    r"Vice President", r"VP", r"Senior Vice President", r"SVP",
    r"Director of", r"Head of", r"General Counsel",
    r"Chairman", r"Board Member", r"Principal Architect"
]

ROLE_STR = '|'.join(LEADERSHIP_ROLES)
ROLE_REGEX = re.compile(r'\b(' + ROLE_STR + r')\b', re.IGNORECASE)

# Pre-compiled name & role patterns
PATTERN_NAME_THEN_ROLE = re.compile(
    r'\b([A-Z][a-z]+(?:[ ]+[A-Z][a-z]+){1,3})[ ]*(?:,|-|[ ]+(?i:is(?:[ ]+the)?|serves[ ]+as(?:[ ]+the)?|is[ ]+a))[ ]*(?i:((?:' + ROLE_STR + r')(?:[ ]+(?:and|&)[ ]+(?:' + ROLE_STR + r'))?))'
)
PATTERN_ROLE_THEN_NAME = re.compile(
    r'(?i:\b(?:' + ROLE_STR + r')\b)[ ]+([A-Z][a-z]+(?:[ ]+[A-Z][a-z]+){1,3})\b'
)


def extract_executive_details(soup: BeautifulSoup, text: str) -> list:
    """
    Extracts person-related leadership, executive roles, and biographies from parsed HTML.
    Looks for team cards, bio sections, schema.org Person data, and role regex patterns.
    """
    executives = []
    seen_names = set()

    # 1. Look for Schema.org Person markup or microdata
    for person_tag in soup.find_all(attrs={"itemtype": re.compile(r"schema\.org/Person", re.IGNORECASE)}):
        name_tag = person_tag.find(attrs={"itemprop": "name"})
        job_tag = person_tag.find(attrs={"itemprop": "jobTitle"})
        bio_tag = person_tag.find(attrs={"itemprop": "description"})
        
        name = name_tag.get_text(strip=True) if name_tag else ""
        role = job_tag.get_text(strip=True) if job_tag else "Leadership"
        bio = bio_tag.get_text(strip=True) if bio_tag else ""

        if name and name not in seen_names and len(name.split()) <= 4:
            seen_names.add(name)
            executives.append({
                "name": name,
                "role": role,
                "bio": bio[:500],
                "source": "microdata"
            })

    # 2. Look for semantic classes (team, executive, leadership, bio, member)
    team_containers = soup.find_all(class_=re.compile(r'(team|leadership|executive|board|member|profile|bio-card|person)', re.IGNORECASE))
    for container in team_containers:
        if len(container.get_text()) > 2000:
            continue
        
        name_el = container.find(['h2', 'h3', 'h4', 'h5', 'strong', 'b'])
        if not name_el:
            continue
        name_text = name_el.get_text(strip=True)
        if not name_text or len(name_text.split()) > 5 or len(name_text) > 40:
            continue
        if re.search(r'(team|leadership|about|board|executive|overview|our)', name_text, re.IGNORECASE):
            continue

        container_text = container.get_text(separator=" ", strip=True)
        role_match = ROLE_REGEX.search(container_text)
        role_text = role_match.group(0) if role_match else "Executive / Team Member"
        
        if name_text not in seen_names:
            seen_names.add(name_text)
            executives.append({
                "name": name_text,
                "role": role_text,
                "bio": container_text[:400],
                "source": "team_card"
            })

    # 3. Pattern matching in text for Name + Role combinations
    for match in PATTERN_NAME_THEN_ROLE.finditer(text):
        name = match.group(1).strip()
        role = match.group(2).strip()
        if name not in seen_names and len(name.split()) <= 4:
            if not re.search(r'(Executive|Leadership|Company|Corporation|Inc|Team|Board|Overview|Report)', name, re.IGNORECASE):
                seen_names.add(name)
                start = max(0, match.start() - 40)
                end = min(len(text), match.end() + 150)
                executives.append({
                    "name": name,
                    "role": role,
                    "bio": text[start:end].replace('\n', ' ').strip()[:350],
                    "source": "text_pattern"
                })

    for match in PATTERN_ROLE_THEN_NAME.finditer(text):
        full_m = match.group(0).strip()
        name = match.group(1).strip()
        role = full_m[:-len(name)].strip()
        if name not in seen_names and len(name.split()) <= 4:
            if not re.search(r'(Executive|Leadership|Company|Corporation|Inc|Team|Board|Overview|Report|Google|Apple|Microsoft|Amazon|FutureAI)', name, re.IGNORECASE):
                seen_names.add(name)
                start = max(0, match.start() - 40)
                end = min(len(text), match.end() + 150)
                executives.append({
                    "name": name,
                    "role": role,
                    "bio": text[start:end].replace('\n', ' ').strip()[:350],
                    "source": "text_pattern"
                })

    return executives[:15]


def scrape_url(url: str, timeout: int = 15) -> dict:
    """
    Scrapes content from a single URL.
    Returns dictionary with raw_content, status_code, cleaned_text, title, metadata, and executive_details.
    """
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/124.0.0.0 Safari/537.36 TechnicalAssignment/2.0'
        ),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    start_time = time.time()
    result = {
        'url': url,
        'http_status_code': 0,
        'raw_content': '',
        'page_title': '',
        'meta_description': '',
        'cleaned_text': '',
        'metadata_json': {},
        'executive_details': [],
        'error': None
    }

    # Ensure schema
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        result['url'] = url

    try:
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        latency = round(time.time() - start_time, 3)
        result['http_status_code'] = response.status_code
        result['raw_content'] = response.text

        # Response metadata
        result['metadata_json'] = {
            'content_type': response.headers.get('Content-Type', ''),
            'content_length': len(response.text),
            'latency_seconds': latency,
            'final_url': response.url,
            'is_redirect': len(response.history) > 0
        }

        # Parse HTML if text/html
        soup = BeautifulSoup(response.text, 'html.parser')

        # Title
        if soup.title and soup.title.string:
            result['page_title'] = soup.title.string.strip()
        elif soup.find('h1'):
            result['page_title'] = soup.find('h1').get_text(strip=True)
        else:
            result['page_title'] = urlparse(url).netloc

        # Meta description
        meta_desc = soup.find('meta', attrs={'name': re.compile(r'description', re.I)}) or \
                    soup.find('meta', attrs={'property': re.compile(r'og:description', re.I)})
        if meta_desc and meta_desc.get('content'):
            result['meta_description'] = meta_desc['content'].strip()

        # Clean text: remove non-content tags
        for element in soup(['script', 'style', 'noscript', 'nav', 'footer', 'svg', 'iframe']):
            element.decompose()

        # Extract structured text paragraphs
        text_blocks = []
        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'li', 'article', 'section']):
            t = tag.get_text(separator=' ', strip=True)
            if t and len(t) > 15:
                text_blocks.append(t)

        cleaned = "\n\n".join(text_blocks)
        if not cleaned:
            cleaned = soup.get_text(separator=' ', strip=True)

        result['cleaned_text'] = cleaned

        # Extract executive / person details
        result['executive_details'] = extract_executive_details(soup, cleaned)

        logger.info(f"Successfully scraped {url} [status={response.status_code}, length={len(cleaned)}]")

    except requests.exceptions.RequestException as exc:
        latency = round(time.time() - start_time, 3)
        result['http_status_code'] = getattr(exc.response, 'status_code', 500) if hasattr(exc, 'response') and exc.response else 500
        result['error'] = str(exc)
        result['raw_content'] = f"<!-- Scraping failed: {exc} -->"
        result['cleaned_text'] = f"Failed to fetch content from {url}. Error: {exc}"
        result['page_title'] = f"Error: {urlparse(url).netloc}"
        result['metadata_json'] = {
            'error': str(exc),
            'latency_seconds': latency
        }
        logger.error(f"Error scraping {url}: {exc}")

    return result


def parse_csv_for_urls(file_content: str) -> list:
    """
    Parses uploaded CSV text or content to extract a list of unique URLs.
    Handles single-column, multi-column headers, or raw URL lines.
    """
    urls = []
    seen = set()

    # Try standard CSV parsing
    try:
        reader = csv.reader(io.StringIO(file_content))
        for row in reader:
            for cell in row:
                cell_clean = cell.strip()
                # Check if cell contains URL pattern
                url_match = re.search(r'https?://[^\s,\"\']+', cell_clean)
                if url_match:
                    found_url = url_match.group(0).rstrip('.,;)')
                    if found_url not in seen:
                        seen.add(found_url)
                        urls.append(found_url)
                elif re.match(r'^(www\.)[a-zA-Z0-9-]+\.[a-zA-Z]{2,}', cell_clean):
                    found_url = f"https://{cell_clean}"
                    if found_url not in seen:
                        seen.add(found_url)
                        urls.append(found_url)
    except Exception as exc:
        logger.warning(f"Standard CSV parsing failed, falling back to regex: {exc}")

    # Fallback to regex across the entire text
    if not urls:
        found = re.findall(r'https?://[^\s,\"\'>]+', file_content)
        for u in found:
            u_clean = u.rstrip('.,;)')
            if u_clean not in seen:
                seen.add(u_clean)
                urls.append(u_clean)

    return urls
