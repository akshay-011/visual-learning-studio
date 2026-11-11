"""Tests for storyboard models and planning."""

from src.research.engine import heuristic_research_fallback
from src.ingestion.source_reader import KnowledgeBundle
from src.learning.architect import plan_storyboard
from src.storyboard.models import Storyboard


def test_storyboard_30s_structure():
    bundle = KnowledgeBundle(
        title="How an API request travels",
        source_type="topic",
        summary="API journey",
        raw_context="",
    )
    report = heuristic_research_fallback(bundle)
    storyboard = plan_storyboard(report, mode="technical", duration=30.0)

    assert isinstance(storyboard, Storyboard)
    assert len(storyboard.scenes) == 3
    assert storyboard.target_duration == 30.0
    assert storyboard.scenes[0].visual_type == "cinematic_title"
    assert storyboard.scenes[1].visual_type == "flow_animation"
    assert storyboard.scenes[2].visual_type == "metric_grid"


def test_storyboard_60s_structure():
    bundle = KnowledgeBundle(
        title="How an API request travels",
        source_type="topic",
        summary="API journey",
        raw_context="",
    )
    report = heuristic_research_fallback(bundle)
    storyboard = plan_storyboard(report, mode="technical", duration=60.0)

    assert isinstance(storyboard, Storyboard)
    assert len(storyboard.scenes) == 5
    assert storyboard.target_duration == 60.0
    assert storyboard.scenes[3].visual_type == "code_walkthrough"
