"""Tests for universal source ingestion."""

from pathlib import Path
from src.ingestion.source_reader import ingest_source, KnowledgeBundle


def test_ingest_topic():
    bundle = ingest_source("How an API request travels through a backend system")
    assert isinstance(bundle, KnowledgeBundle)
    assert "API request" in bundle.title
    assert bundle.source_type == "topic"
    assert len(bundle.key_sections) > 0


def test_ingest_local_markdown(tmp_path: Path):
    md_file = tmp_path / "sample.md"
    md_file.write_text("# Test Architecture\n\nDistributed raft consensus mechanism.")
    bundle = ingest_source(str(md_file))
    assert bundle.source_type == "markdown"
    assert "Test Architecture" in bundle.title
