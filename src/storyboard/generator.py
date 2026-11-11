"""Storyboard Generator: Serialization and validation engine."""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from src.ingestion.source_reader import KnowledgeBundle, ingest_source
from src.research.engine import ResearchReport, conduct_research
from src.learning.architect import plan_storyboard
from src.storyboard.models import Storyboard


def generate_storyboard(
    source_input: str,
    mode: str = "technical",
    duration: float = 60.0,
    output_path: Optional[Path] = None,
) -> Storyboard:
    """End-to-end storyboard generation from input source to validated Pydantic model."""
    bundle: KnowledgeBundle = ingest_source(source_input)
    report: ResearchReport = conduct_research(bundle)
    storyboard: Storyboard = plan_storyboard(report, mode=mode, duration=duration)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(storyboard.model_dump_json(indent=2))

    return storyboard
