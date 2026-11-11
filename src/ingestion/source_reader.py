"""Universal Source Reader and Ingestion Orchestrator."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import requests
from bs4 import BeautifulSoup

from src.ingestion.github_ingest import ingest_github_url, scan_directory_tree, extract_key_source_snippets
from src.ingestion.pdf_ingest import ingest_pdf_file


class KnowledgeBundle(BaseModel):
    title: str
    source_type: str  # "topic" | "github" | "web" | "pdf" | "markdown"
    summary: str
    key_sections: List[Dict[str, str]] = Field(default_factory=list)
    code_snippets: List[Dict[str, str]] = Field(default_factory=list)
    raw_context: str = ""


def ingest_web_url(url: str) -> Dict[str, Any]:
    """Fetches and parses documentation or articles from a web URL."""
    headers = {
        "User-Agent": "VisualLearningStudio/1.0 (+https://github.com/omarchy/visual-learning-studio)"
    }
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    # Remove script and style elements
    for element in soup(["script", "style", "nav", "footer", "aside"]):
        element.decompose()

    title = soup.title.string.strip() if soup.title and soup.title.string else url
    
    # Extract headings and paragraphs
    paragraphs = []
    for p in soup.find_all(["p", "h1", "h2", "h3", "pre"]):
        text = p.get_text().strip()
        if text:
            paragraphs.append(text)

    full_text = "\n\n".join(paragraphs)
    return {
        "title": title,
        "source_type": "web",
        "url": url,
        "text": full_text[:8000],
    }


def ingest_source(source_input: str, cache_dir: Optional[Path] = None) -> KnowledgeBundle:
    """Universal entrypoint: automatically classifies and ingests any input source."""
    if cache_dir is None:
        cache_dir = Path("/tmp/vls_ingest_cache")
    cache_dir.mkdir(parents=True, exist_ok=True)

    stripped = source_input.strip()

    # Case 1: GitHub URL
    if stripped.startswith("https://github.com/") or stripped.startswith("http://github.com/"):
        data = ingest_github_url(stripped, cache_dir)
        summary = f"GitHub repository {data['title']}: {data['readme_excerpt'][:300]}"
        return KnowledgeBundle(
            title=data["title"],
            source_type="github",
            summary=summary,
            key_sections=[{"title": "README", "content": data["readme_excerpt"]}],
            code_snippets=data["snippets"],
            raw_context=data["readme_excerpt"],
        )

    # Case 2: Web URL
    if stripped.startswith("http://") or stripped.startswith("https://"):
        data = ingest_web_url(stripped)
        return KnowledgeBundle(
            title=data["title"],
            source_type="web",
            summary=data["text"][:300],
            key_sections=[{"title": "Web Documentation", "content": data["text"][:3000]}],
            raw_context=data["text"],
        )

    # Case 3: Local PDF File
    path = Path(stripped)
    if path.is_file() and path.suffix.lower() == ".pdf":
        data = ingest_pdf_file(path)
        return KnowledgeBundle(
            title=data["title"],
            source_type="pdf",
            summary=data["abstract"][:300],
            key_sections=[{"title": "Abstract", "content": data["abstract"]}],
            raw_context=data["sample_content"],
        )

    # Case 4: Local Directory or Markdown File
    if path.is_dir():
        tree = scan_directory_tree(path)
        snippets = extract_key_source_snippets(path, tree["key_files"])
        return KnowledgeBundle(
            title=path.name.replace("_", " ").title(),
            source_type="directory",
            summary=f"Local project {path.name} with {tree['file_count']} files.",
            key_sections=[{"title": "Key Files", "content": "\n".join(tree["key_files"])}],
            code_snippets=snippets,
            raw_context="\n".join(tree["files"][:50]),
        )

    if path.is_file() and path.suffix.lower() in [".md", ".txt", ".rst"]:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        title = path.stem.replace("_", " ").title()
        # Look for markdown H1 header: # Title
        for line in content.splitlines():
            line_str = line.strip()
            if line_str.startswith("# "):
                title = line_str.lstrip("# ").strip()
                break
        return KnowledgeBundle(
            title=title,
            source_type="markdown",
            summary=content[:300],
            key_sections=[{"title": title, "content": content[:4000]}],
            raw_context=content,
        )

    # Case 5: Conceptual Topic Prompt (e.g. "How an API request travels through a backend system")
    title = stripped.strip(".'\"")
    summary = f"Educational exploration of: {title}"
    return KnowledgeBundle(
        title=title,
        source_type="topic",
        summary=summary,
        key_sections=[{"title": "Core Subject", "content": title}],
        raw_context=title,
    )
