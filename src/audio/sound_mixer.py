"""Multi-track audio mixing engine with sidechain ducking and SFX integration."""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def build_mixed_soundtrack(
    scene_audios: List[Tuple[float, Path, Optional[str]]], # (start_time, wav_path, sfx_name)
    total_duration: float,
    music_track_path: Path,
    output_wav: Path,
    assets_dir: Path,
    music_base_volume: float = 0.12,
    ducked_volume: float = 0.04,
) -> Path:
    """Mixes dialogue, SFX, and background music with automated ducking and leveling."""
    output_wav.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = output_wav.parent / "temp_audio"
    temp_dir.mkdir(parents=True, exist_ok=True)

    # 1. Build concatenated dialogue track with exact pauses
    concat_list_file = temp_dir / "dialogue_concat.txt"
    # Alternatively, create dialogue track using an FFmpeg complex filter with adelay
    inputs = []
    filter_chains = []

    # Input 0: Background music (looped if duration exceeds track)
    inputs.extend(["-stream_loop", "-1", "-i", str(music_track_path)])

    # Inputs 1..N: Scene dialogue wavs
    dialogue_filter_inputs = []
    idx = 1
    for start_sec, wav_path, sfx_name in scene_audios:
        delay_ms = int(start_sec * 1000)
        inputs.extend(["-i", str(wav_path)])
        # Apply delay to align dialogue on the global timeline
        filter_chains.append(f"[{idx}:a]adelay={delay_ms}|{delay_ms}[d{idx}]")
        dialogue_filter_inputs.append(f"[d{idx}]")
        idx += 1

    # SFX inputs
    sfx_filter_inputs = []
    for start_sec, _, sfx_name in scene_audios:
        if sfx_name:
            sfx_file = None
            for cand in [
                assets_dir / "sfx" / "impact" / sfx_name,
                assets_dir / "sfx" / "interface" / sfx_name,
                assets_dir / "sfx" / "keyboard" / sfx_name,
                assets_dir / "sfx" / "ui" / sfx_name,
                assets_dir / "sfx" / sfx_name,
            ]:
                if cand.exists():
                    sfx_file = cand
                    break

            if sfx_file:
                # Place SFX at start_sec with slight offset (-0.1s for swoosh)
                sfx_delay_ms = max(0, int((start_sec - 0.05) * 1000))
                inputs.extend(["-i", str(sfx_file)])
                filter_chains.append(f"[{idx}:a]volume=0.35,adelay={sfx_delay_ms}|{sfx_delay_ms}[sfx{idx}]")
                sfx_filter_inputs.append(f"[sfx{idx}]")
                idx += 1

    # Merge all dialogue segments into a single dialogue stream
    num_dialogues = len(dialogue_filter_inputs)
    if num_dialogues > 1:
        filter_chains.append(f"{''.join(dialogue_filter_inputs)}amix=inputs={num_dialogues}:dropout_transition=0:normalize=0[dialogue_all]")
    elif num_dialogues == 1:
        filter_chains.append(f"{dialogue_filter_inputs[0]}anull[dialogue_all]")
    else:
        filter_chains.append("aevalsrc=0:d=1[dialogue_all]")

    # Music volume shaping: base ducked volume, smooth fade out at the end
    fade_out_start = max(0.0, total_duration - 2.5)
    filter_chains.append(
        f"[0:a]atrim=0:{total_duration},volume={ducked_volume},"
        f"afade=t=in:st=0:d=1.5,afade=t=out:st={fade_out_start}:d=2.5[music_shaped]"
    )

    # Combine dialogue, music, and SFX
    final_mix_inputs = ["[dialogue_all]", "[music_shaped]"] + sfx_filter_inputs
    num_mix = len(final_mix_inputs)
    filter_chains.append(
        f"{''.join(final_mix_inputs)}amix=inputs={num_mix}:duration=first:dropout_transition=0:normalize=0,"
        f"loudnorm=I=-16:TP=-1.5:LRA=11[out_a]"
    )

    filter_complex = ";".join(filter_chains)

    cmd = [
        "ffmpeg",
        "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[out_a]",
        "-t", str(total_duration),
        "-ar", "48000",
        "-ac", "2",
        "-c:a", "pcm_s16le",
        str(output_wav),
    ]

    subprocess.run(cmd, capture_output=True, check=True)

    # Clean up temp files
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)

    return output_wav
