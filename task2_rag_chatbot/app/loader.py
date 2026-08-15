"""
Multi-Format Document Loader.
Extracts text and page metadata from PDF, DOCX, TXT, MD, and CSV files.
"""
import io
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def load_pdf_file(file_bytes: bytes, file_name: str) -> List[Dict[str, Any]]:
    """
    Extracts text page by page from PDF file.
    Returns list of page items with 'text' and 'page_number'.
    """
    import pypdf
    pages = []
    try:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        for page_idx, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            if page_text.strip():
                pages.append({
                    "text": page_text.strip(),
                    "page_number": page_idx + 1,
                    "file_name": file_name
                })
    except Exception as exc:
        logger.error(f"Error extracting PDF text from {file_name}: {exc}")
        raise ValueError(f"Failed to parse PDF document '{file_name}': {exc}")
    
    return pages


def load_docx_file(file_bytes: bytes, file_name: str) -> List[Dict[str, Any]]:
    """
    Extracts paragraphs from Microsoft Word .docx files.
    """
    import docx
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        full_text = "\n\n".join(paragraphs)
        return [{
            "text": full_text,
            "page_number": 1,
            "file_name": file_name
        }]
    except Exception as exc:
        logger.error(f"Error extracting DOCX text from {file_name}: {exc}")
        raise ValueError(f"Failed to parse DOCX document '{file_name}': {exc}")


def load_txt_or_md_file(file_bytes: bytes, file_name: str) -> List[Dict[str, Any]]:
    """
    Extracts plain text from .txt and .md files with UTF-8/latin-1 decoding.
    """
    try:
        text = file_bytes.decode('utf-8')
    except UnicodeDecodeError:
        text = file_bytes.decode('latin-1', errors='ignore')

    return [{
        "text": text.strip(),
        "page_number": 1,
        "file_name": file_name
    }]


def load_csv_file(file_bytes: bytes, file_name: str) -> List[Dict[str, Any]]:
    """
    Extracts structured CSV rows into readable context sentences.
    """
    try:
        text = file_bytes.decode('utf-8')
    except UnicodeDecodeError:
        text = file_bytes.decode('latin-1', errors='ignore')

    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        return []

    header = rows[0]
    records = []
    for r in rows[1:]:
        pairs = [f"{header[i] if i < len(header) else f'Col_{i}'}: {val.strip()}" for i, val in enumerate(r) if val.strip()]
        if pairs:
            records.append(", ".join(pairs))

    return [{
        "text": "\n".join(records),
        "page_number": 1,
        "file_name": file_name
    }]


def load_document(file_bytes: bytes, file_name: str) -> List[Dict[str, Any]]:
    """
    Dispatcher function to parse any supported document type.
    """
    suffix = Path(file_name).suffix.lower()

    if suffix == '.pdf':
        return load_pdf_file(file_bytes, file_name)
    elif suffix in ['.docx', '.doc']:
        return load_docx_file(file_bytes, file_name)
    elif suffix in ['.txt', '.md', '.markdown', '.rst']:
        return load_txt_or_md_file(file_bytes, file_name)
    elif suffix == '.csv':
        return load_csv_file(file_bytes, file_name)
    else:
        # Default fallback to plain text loader
        return load_txt_or_md_file(file_bytes, file_name)
