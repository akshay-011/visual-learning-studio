"""Tests for video quality inspector."""

import subprocess
from pathlib import Path
import pytest
from src.quality.inspector import inspect_video


def test_inspect_video_valid(tmp_path: Path):
    # Render a 1-second test MP4 with audio
    mp4_path = tmp_path / "valid_test.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=black:s=1920x1080:d=1.0",
        "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-t", "1.0",
        str(mp4_path),
    ]
    subprocess.run(cmd, capture_output=True, check=True)

    qc = inspect_video(mp4_path, expected_duration=1.0, tolerance_sec=0.5)
    assert qc.is_valid is True
    assert qc.width == 1920
    assert qc.height == 1080
    assert qc.audio_channels == 2
    assert qc.duration_seconds >= 0.8


def test_inspect_video_nonexistent():
    with pytest.raises(FileNotFoundError):
        inspect_video(Path("/tmp/nonexistent_video_12345.mp4"))
