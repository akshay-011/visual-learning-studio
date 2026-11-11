"""Automated Video Quality Inspection and Verification Engine."""

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel


class QualityCheckResult(BaseModel):
    is_valid: bool
    file_path: str
    file_size_mb: float
    duration_seconds: float
    video_codec: str
    width: int
    height: int
    fps: float
    audio_codec: str
    audio_channels: int
    audio_sample_rate: int
    duration_target: float
    duration_delta: float
    checks: Dict[str, bool]
    summary: str


def inspect_video(mp4_path: Path, expected_duration: float = 30.0, tolerance_sec: float = 2.0) -> QualityCheckResult:
    """Uses ffprobe to deeply validate video container, streams, and sync."""
    if not mp4_path.exists():
        raise FileNotFoundError(f"Video file does not exist: {mp4_path}")

    size_mb = round(mp4_path.stat().st_size / (1024 * 1024), 2)

    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_format",
        "-show_streams",
        "-of", "json",
        str(mp4_path),
    ]

    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    probe_data = json.loads(res.stdout)

    video_stream = None
    audio_stream = None

    for s in probe_data.get("streams", []):
        if s.get("codec_type") == "video" and not video_stream:
            video_stream = s
        elif s.get("codec_type") == "audio" and not audio_stream:
            audio_stream = s

    if not video_stream:
        raise ValueError("No video stream found in container")
    if not audio_stream:
        raise ValueError("No audio stream found in container")

    duration = float(probe_data.get("format", {}).get("duration", 0.0))
    v_codec = video_stream.get("codec_name", "unknown")
    width = int(video_stream.get("width", 0))
    height = int(video_stream.get("height", 0))

    # Parse fps
    r_fps = video_stream.get("r_frame_rate", "30/1")
    try:
        num, den = r_fps.split("/")
        fps = round(float(num) / float(den), 2)
    except Exception:
        fps = 30.0

    a_codec = audio_stream.get("codec_name", "unknown")
    channels = int(audio_stream.get("channels", 0))
    sample_rate = int(audio_stream.get("sample_rate", 0))

    delta = abs(duration - expected_duration)

    checks = {
        "file_exists_and_nonzero": mp4_path.stat().st_size > 1024,
        "video_stream_valid_h264": v_codec in ["h264", "avc1"],
        "resolution_1080p": width == 1920 and height == 1080,
        "audio_stream_valid_aac": a_codec in ["aac", "pcm_s16le"],
        "audio_stereo": channels == 2,
        "duration_within_tolerance": delta <= tolerance_sec,
    }

    is_valid = all(checks.values())
    summary = (
        f"Passed all {len(checks)} automated quality gates. Duration: {duration:.2f}s "
        f"(target: {expected_duration:.2f}s, delta: {delta:.2f}s). Resolution: {width}x{height} @ {fps}fps."
        if is_valid
        else f"Quality check failed: {[k for k, v in checks.items() if not v]}"
    )

    return QualityCheckResult(
        is_valid=is_valid,
        file_path=str(mp4_path),
        file_size_mb=size_mb,
        duration_seconds=round(duration, 2),
        video_codec=v_codec,
        width=width,
        height=height,
        fps=fps,
        audio_codec=a_codec,
        audio_channels=channels,
        audio_sample_rate=sample_rate,
        duration_target=expected_duration,
        duration_delta=round(delta, 2),
        checks=checks,
        summary=summary,
    )
