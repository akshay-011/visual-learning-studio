"""Visual Engine: Renders animated scene segments using hardware-accelerated FFmpeg streaming."""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from src.discovery.hardware import detect_hardware
from src.generation.programmatic_animator import render_scene_frame
from src.storyboard.models import Scene


def render_scene_video(
    scene: Scene,
    duration: float,
    output_path: Path,
    encoder: str = "auto",
    width: int = 1920,
    height: int = 1080,
    fps: int = 30,
) -> Path:
    """Renders a complete, animated MP4 video clip for a single scene."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Resolve encoder
    if encoder == "auto":
        hw = detect_hardware()
        encoder = hw.recommended_encoder

    total_frames = max(1, int(duration * fps))

    # Encoder specific parameters
    encoder_args = []
    if encoder == "h264_nvenc":
        encoder_args = ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "20"]
    else:
        encoder_args = ["-c:v", "libx264", "-preset", "fast", "-crf", "20"]

    cmd = [
        "ffmpeg",
        "-y",
        "-f", "rawvideo",
        "-pix_fmt", "rgb24",
        "-s", f"{width}x{height}",
        "-r", str(fps),
        "-i", "-",
        *encoder_args,
        "-pix_fmt", "yuv420p",
        "-t", f"{duration:.3f}",
        str(output_path),
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    try:
        for f_idx in range(total_frames):
            t = f_idx / float(total_frames)
            frame_img = render_scene_frame(scene, t, width=width, height=height)
            raw_bytes = frame_img.tobytes()
            proc.stdin.write(raw_bytes)
    except Exception as e:
        proc.kill()
        raise RuntimeError(f"Visual rendering pipeline failed on frame {f_idx}: {e}")
    finally:
        if proc.stdin:
            proc.stdin.close()
        proc.wait()

    if proc.returncode != 0:
        err = proc.stderr.read().decode("utf-8", errors="ignore")
        # Attempt fallback to libx264 if nvenc failed
        if encoder == "h264_nvenc":
            return render_scene_video(
                scene, duration, output_path, encoder="libx264", width=width, height=height, fps=fps
            )
        raise RuntimeError(f"FFmpeg render error (code {proc.returncode}): {err[-500:]}")

    return output_path
