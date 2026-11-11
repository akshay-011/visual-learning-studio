"""FFmpeg Video Composition and Final Multiplexing Engine."""

import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

from src.discovery.hardware import detect_hardware


def compose_final_video(
    scene_video_paths: List[Path],
    master_audio_path: Path,
    srt_path: Optional[Path],
    output_mp4: Path,
    encoder: str = "auto",
    burn_subtitles: bool = True,
) -> Path:
    """Concatenates scene clips, multiplexes master audio, burns subtitles, and exports final MP4."""
    output_mp4.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = output_mp4.parent / "temp_compose"
    temp_dir.mkdir(parents=True, exist_ok=True)

    if encoder == "auto":
        hw = detect_hardware()
        encoder = hw.recommended_encoder

    # 1. Write concat demuxer list
    concat_list_file = temp_dir / "concat_scenes.txt"
    with open(concat_list_file, "w", encoding="utf-8") as f:
        for p in scene_video_paths:
            f.write(f"file '{p.resolve()}'\n")

    # 2. Build filter graph
    vf_filters = []
    if burn_subtitles and srt_path and srt_path.exists():
        # Escape path for FFmpeg subtitles filter
        escaped_srt = str(srt_path.resolve()).replace(":", "\\:").replace("'", "\\'")
        style = (
            "Fontname=Liberation Sans,Fontsize=24,PrimaryColour=&H00FFFFFF,"
            "OutlineColour=&H00090D16,BorderStyle=3,Outline=2,Shadow=0,MarginV=55"
        )
        vf_filters.append(f"subtitles={escaped_srt}:force_style='{style}'")

    vf_arg = ["-vf", ",".join(vf_filters)] if vf_filters else []

    # 3. Encoder settings
    if encoder == "h264_nvenc":
        enc_args = ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "19"]
    else:
        enc_args = ["-c:v", "libx264", "-preset", "medium", "-crf", "19"]

    cmd = [
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list_file),
        "-i", str(master_audio_path),
        *vf_arg,
        *enc_args,
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "48000",
        "-shortest",
        str(output_mp4),
    ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        # Fallback to libx264 if nvenc failed
        if encoder == "h264_nvenc":
            return compose_final_video(
                scene_video_paths,
                master_audio_path,
                srt_path,
                output_mp4,
                encoder="libx264",
                burn_subtitles=burn_subtitles,
            )
        raise RuntimeError(f"FFmpeg final composition failed: {res.stderr[-600:]}")

    # Clean up temporary concat list
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)

    return output_mp4
