"""Neural Text-to-Speech Engine with frame-accurate subtitle timestamping."""

import asyncio
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import edge_tts


@dataclass
class SynthesizedAudio:
    wav_path: Path
    duration: float
    srt_content: str


def get_audio_duration(file_path: Path) -> float:
    """Uses ffprobe to obtain exact audio duration in seconds."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(file_path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(res.stdout.strip())


async def _synthesize_edge_tts(
    text: str,
    voice: str,
    output_wav: Path,
    rate: str = "+0%",
    max_retries: int = 4,
) -> SynthesizedAudio:
    """Internal coroutine for edge-tts streaming and conversion with exponential backoff retries."""
    temp_mp3 = output_wav.with_suffix(".temp.mp3")
    output_wav.parent.mkdir(parents=True, exist_ok=True)

    last_err = None
    submaker = None

    for attempt in range(max_retries):
        try:
            communicate = edge_tts.Communicate(text, voice, rate=rate)
            submaker = edge_tts.SubMaker()

            with open(temp_mp3, "wb") as f:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])
                    elif chunk["type"] in ["WordBoundary", "SentenceBoundary"]:
                        submaker.feed(chunk)

            # If file was written and non-empty, success
            if temp_mp3.exists() and temp_mp3.stat().st_size > 500:
                break
        except Exception as e:
            last_err = e
            if temp_mp3.exists():
                temp_mp3.unlink()
            await asyncio.sleep(1.0 * (attempt + 1))
    else:
        # If all retries with primary voice fail, try fallback voice en-US-GuyNeural
        try:
            communicate = edge_tts.Communicate(text, "en-US-GuyNeural", rate=rate)
            submaker = edge_tts.SubMaker()
            with open(temp_mp3, "wb") as f:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])
                    elif chunk["type"] in ["WordBoundary", "SentenceBoundary"]:
                        submaker.feed(chunk)
        except Exception as e:
            raise RuntimeError(f"Edge-TTS synthesis failed after retries: {last_err or e}")

    # Transcode to broadcast standard PCM 16-bit 48,000 Hz Stereo WAV
    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(temp_mp3),
        "-ar", "48000",
        "-ac", "2",
        "-c:a", "pcm_s16le",
        str(output_wav),
    ]
    subprocess.run(cmd, capture_output=True, check=True)

    if temp_mp3.exists():
        temp_mp3.unlink()

    duration = get_audio_duration(output_wav)
    srt_content = submaker.get_srt() if submaker else ""

    return SynthesizedAudio(
        wav_path=output_wav,
        duration=duration,
        srt_content=srt_content,
    )


def synthesize_narration(
    text: str,
    output_wav: Path,
    voice: str = "en-US-ChristopherNeural",
    rate: str = "+0%",
) -> SynthesizedAudio:
    """Synchronous interface for neural voiceover synthesis."""
    return asyncio.run(_synthesize_edge_tts(text, voice, output_wav, rate=rate))
