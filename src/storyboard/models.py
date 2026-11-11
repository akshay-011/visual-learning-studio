"""Pydantic Storyboard Data Models for Visual Learning Studio."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class VisualSpec(BaseModel):
    headline: str = ""
    subline: str = ""
    badge: Optional[str] = None
    diagram_nodes: List[Dict[str, Any]] = Field(default_factory=list)
    diagram_edges: List[Dict[str, Any]] = Field(default_factory=list)
    flow_packets: List[Dict[str, Any]] = Field(default_factory=list)
    code_lines: List[str] = Field(default_factory=list)
    highlighted_line: Optional[int] = None
    metric_cards: List[Dict[str, str]] = Field(default_factory=list)
    theme: str = "dark_cyan"


class AudioSpec(BaseModel):
    narration_voice: str = "en-US-ChristopherNeural"
    speech_rate: str = "+0%"
    sfx_cue: Optional[str] = None  # e.g. "impactSoft", "click", "chime"
    music_track: str = "happy-beats-business-moves-vol-10-by-ende-dot-app.mp3"
    music_volume: float = 0.12


class Scene(BaseModel):
    scene_id: str
    duration: float  # In seconds
    narration: str
    educational_objective: str
    visual_type: str  # "cinematic_title" | "architecture_diagram" | "flow_animation" | "code_walkthrough" | "metric_grid" | "concept_card"
    visual_spec: VisualSpec
    audio_spec: AudioSpec
    transition: str = "crossfade"  # "fade", "crossfade", "cut"


class Storyboard(BaseModel):
    title: str
    mode: str  # "beginner" | "technical" | "documentary"
    target_duration: float
    aspect_ratio: str = "16:9"
    width: int = 1920
    height: int = 1080
    fps: int = 30
    scenes: List[Scene]

    @property
    def total_planned_duration(self) -> float:
        return sum(s.duration for s in self.scenes)

    @property
    def total_word_count(self) -> int:
        return sum(len(s.narration.split()) for s in self.scenes)
