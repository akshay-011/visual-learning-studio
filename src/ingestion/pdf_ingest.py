"""PDF and Research Paper ingestion engine."""

from pathlib import Path
from typing import Any, Dict, List
import pypdf


def ingest_pdf_file(pdf_path: Path, max_pages: int = 15) -> Dict[str, Any]:
    """Extracts text, title, abstract, and sections from PDF research papers."""
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found at {pdf_path}")

    reader = pypdf.PdfReader(str(pdf_path))
    total_pages = len(reader.pages)
    extracted_text_chunks: List[str] = []

    pages_to_read = min(total_pages, max_pages)
    for i in range(pages_to_read):
        page = reader.pages[i]
        text = page.extract_text() or ""
        extracted_text_chunks.append(text)

    full_text = "\n\n".join(extracted_text_chunks)
    
    # Simple extraction of title and abstract heuristics
    title = pdf_path.stem.replace("_", " ").title()
    abstract = ""
    lower_text = full_text.lower()
    if "abstract" in lower_text:
        start_idx = lower_text.find("abstract") + len("abstract")
        end_idx = lower_text.find("1. introduction", start_idx)
        if end_idx == -1:
            end_idx = lower_text.find("1 introduction", start_idx)
        if end_idx == -1:
            end_idx = start_idx + 1500
        abstract = full_text[start_idx:end_idx].strip()

    return {
        "title": title,
        "source_type": "pdf",
        "file_name": pdf_path.name,
        "total_pages": total_pages,
        "abstract": abstract[:2000] if abstract else full_text[:1500],
        "sample_content": full_text[:5000],
    }
