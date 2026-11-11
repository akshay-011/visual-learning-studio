"""Master Orchestration Pipeline: Executes end-to-end autonomous video production."""

import json
import os
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.audio.sound_mixer import build_mixed_soundtrack
from src.audio.tts_engine import SynthesizedAudio, synthesize_narration
from src.composition.ffmpeg_renderer import compose_final_video
from src.discovery.hardware import detect_hardware
from src.generation.visual_engine import render_scene_video
from src.ingestion.source_reader import KnowledgeBundle, ingest_source
from src.learning.architect import plan_storyboard
from src.quality.inspector import QualityCheckResult, inspect_video
from src.research.engine import ResearchReport, conduct_research
from src.storyboard.models import Storyboard


def format_srt_time(seconds: float) -> str:
    """Formats float seconds into SRT timestamp HH:MM:SS,mmm."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"


def produce_video(
    source_input: str,
    output_dir: Path,
    mode: str = "technical",
    target_duration: float = 60.0,
    assets_dir: Optional[Path] = None,
    burn_subtitles: bool = True,
) -> Tuple[Path, Storyboard, QualityCheckResult]:
    """Autonomous End-to-End Video Production Engine."""
    start_time = time.time()
    output_dir.mkdir(parents=True, exist_ok=True)
    work_dir = output_dir / "work"
    work_dir.mkdir(parents=True, exist_ok=True)

    if assets_dir is None:
        assets_dir = Path("/home/akshay/workspace/make-video/assets")

    # 1. Hardware Detection
    hw = detect_hardware()

    # 2. Ingestion
    bundle = ingest_source(source_input)

    # 3. Research Engine
    report = conduct_research(bundle)

    # 4. Learning Architect & Storyboard
    storyboard = plan_storyboard(report, mode=mode, duration=target_duration)

    # Save storyboard.json early
    storyboard_path = output_dir / "storyboard.json"
    with open(storyboard_path, "w", encoding="utf-8") as f:
        f.write(storyboard.model_dump_json(indent=2))

    # Save narration.txt
    narration_lines = [f"[{s.scene_id}] {s.narration}" for s in storyboard.scenes]
    with open(output_dir / "narration.txt", "w", encoding="utf-8") as f:
        f.write("\n\n".join(narration_lines))

    # 5. Synthesize Voiceover & Extract Word Timings
    scene_audios: List[Tuple[float, Path, Optional[str]]] = []
    srt_cues: List[str] = []
    cue_idx = 1
    current_timeline_sec = 0.0

    actual_scene_durations: List[float] = []

    for idx, scene in enumerate(storyboard.scenes):
        wav_path = work_dir / f"dialogue_{scene.scene_id}.wav"
        voice = scene.audio_spec.narration_voice or "en-US-ChristopherNeural"
        synth = synthesize_narration(scene.narration, wav_path, voice=voice)

        # Pad duration slightly for natural pauses between scenes (+0.4s)
        pad_pause = 0.4
        actual_dur = round(synth.duration + pad_pause, 2)
        actual_scene_durations.append(actual_dur)

        # Record scene audio entry on the global timeline
        scene_audios.append((current_timeline_sec, synth.wav_path, scene.audio_spec.sfx_cue))

        # Build clean sequential global SRT cues
        sub_start = current_timeline_sec + 0.05
        sub_end = current_timeline_sec + synth.duration
        srt_cues.append(
            f"{cue_idx}\n"
            f"{format_srt_time(sub_start)} --> {format_srt_time(sub_end)}\n"
            f"{scene.narration}\n"
        )
        cue_idx += 1

        current_timeline_sec += actual_dur

    total_actual_duration = round(current_timeline_sec, 2)

    # Write master subtitles.srt
    srt_path = output_dir / "subtitles.srt"
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_cues))

    # 6. Mix Master Audio Track with Ducking & SFX
    music_file = assets_dir / "music" / storyboard.scenes[0].audio_spec.music_track
    if not music_file.exists():
        # Fallback to any available track in assets/music
        available_tracks = list((assets_dir / "music").glob("*.mp3"))
        if available_tracks:
            music_file = available_tracks[0]

    master_audio_wav = work_dir / "master_soundtrack.wav"
    build_mixed_soundtrack(
        scene_audios=scene_audios,
        total_duration=total_actual_duration,
        music_track_path=music_file,
        output_wav=master_audio_wav,
        assets_dir=assets_dir,
    )

    # 7. Render Visual Scene Clips
    scene_video_paths = []
    for idx, scene in enumerate(storyboard.scenes):
        scene_dur = actual_scene_durations[idx]
        clip_path = work_dir / f"clip_{scene.scene_id}.mp4"
        render_scene_video(
            scene=scene,
            duration=scene_dur,
            output_path=clip_path,
            encoder=hw.recommended_encoder,
            width=storyboard.width,
            height=storyboard.height,
            fps=storyboard.fps,
        )
        scene_video_paths.append(clip_path)

    # 8. Video Composition & Export
    final_video_mp4 = output_dir / "final-video.mp4"
    compose_final_video(
        scene_video_paths=scene_video_paths,
        master_audio_path=master_audio_wav,
        srt_path=srt_path,
        output_mp4=final_video_mp4,
        encoder=hw.recommended_encoder,
        burn_subtitles=burn_subtitles,
    )

    # 9. Quality Control Inspection
    qc_result = inspect_video(final_video_mp4, expected_duration=total_actual_duration)

    # Clean intermediate work files
    if work_dir.exists():
        shutil.rmtree(work_dir, ignore_errors=True)

    elapsed = time.time() - start_time
    print(f"Production completed in {elapsed:.1f}s. Result: {final_video_mp4}")
    return final_video_mp4, storyboard, qc_result
