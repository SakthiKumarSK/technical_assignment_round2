"""
Smart Recursive Text Chunker with metadata tracking for Task 2.
"""
from typing import List, Dict, Any


def split_text_recursive(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 100,
    separators: List[str] = None
) -> List[str]:
    """
    Splits text recursively using natural boundary separators.
    """
    if not text:
        return []
    if separators is None:
        separators = ["\n\n", "\n", ". ", "? ", "! ", "; ", " ", ""]

    if len(text) <= chunk_size:
        return [text.strip()] if text.strip() else []

    # Find the highest priority separator present in the text
    chosen_sep = ""
    for sep in separators:
        if sep == "":
            chosen_sep = ""
            break
        if sep in text:
            chosen_sep = sep
            break

    splits = text.split(chosen_sep) if chosen_sep != "" else list(text)

    chunks = []
    current_chunk = ""

    for s in splits:
        piece = (s + chosen_sep) if chosen_sep != "" else s
        if len(current_chunk) + len(piece) <= chunk_size:
            current_chunk += piece
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
                # Apply overlap from the tail of current_chunk
                overlap_text = current_chunk[-chunk_overlap:] if len(current_chunk) > chunk_overlap else current_chunk
                current_chunk = overlap_text + piece
            else:
                # If a single piece exceeds chunk_size, split further with remaining separators
                remaining_seps = separators[separators.index(chosen_sep) + 1:] if chosen_sep in separators else []
                sub_chunks = split_text_recursive(piece, chunk_size, chunk_overlap, remaining_seps)
                chunks.extend(sub_chunks)
                current_chunk = ""

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def create_document_chunks(
    pages: List[Dict[str, Any]],
    doc_id: str,
    doc_name: str,
    chunk_size: int = 500,
    chunk_overlap: int = 100
) -> List[Dict[str, Any]]:
    """
    Converts extracted document pages into a list of chunk items enriched with metadata.
    """
    all_chunks = []
    chunk_idx = 0

    for page in pages:
        page_text = page.get("text", "")
        page_num = page.get("page_number", 1)

        raw_splits = split_text_recursive(
            page_text,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        for chunk_text in raw_splits:
            if len(chunk_text.strip()) < 15:
                continue

            all_chunks.append({
                "doc_id": doc_id,
                "doc_name": doc_name,
                "chunk_index": chunk_idx,
                "page_number": page_num,
                "text": chunk_text.strip(),
                "char_count": len(chunk_text),
                "word_count": len(chunk_text.split())
            })
            chunk_idx += 1

    return all_chunks
