"""Neural Text-to-Speech Engine with frame-accurate subtitle timestamping."""

import asyncio
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, TYPE_CHECKING
import edge_tts

from src.audio.voicestudio import process_human_cadence, get_vocal_studio_filter

if TYPE_CHECKING:
    from src.audio.cloner import VoiceProfile


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
    rate: str = "-3%",
    max_retries: int = 4,
    voice_profile: Optional["VoiceProfile"] = None,
) -> SynthesizedAudio:
    """Internal coroutine for edge-tts streaming with VoiceStudio cadence and optional voice cloning."""
    # If a voice profile is provided, use its matched base neural voice
    effective_voice = voice_profile.base_voice if voice_profile else voice

    # Pre-process text through VoiceStudio pronunciation lexicon and human prosody
    human_text = process_human_cadence(text)

    temp_mp3 = output_wav.with_suffix(".temp.mp3")
    output_wav.parent.mkdir(parents=True, exist_ok=True)

    last_err = None
    submaker = None

    for attempt in range(max_retries):
        try:
            communicate = edge_tts.Communicate(human_text, effective_voice, rate=rate)
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
        # If all retries with primary voice fail, try fallback voice en-US-BrianNeural
        try:
            communicate = edge_tts.Communicate(human_text, "en-US-BrianNeural", rate=rate)
            submaker = edge_tts.SubMaker()
            with open(temp_mp3, "wb") as f:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])
                    elif chunk["type"] in ["WordBoundary", "SentenceBoundary"]:
                        submaker.feed(chunk)
        except Exception as e:
            raise RuntimeError(f"Edge-TTS synthesis failed after retries: {last_err or e}")

    # Voice transformation: Neural Tone Color Conversion (OpenVoice V2) with WORLD fallback
    if voice_profile is not None:
        raw_tts_wav = output_wav.with_suffix(".raw_tts.wav")
        cmd_decode = [
            "ffmpeg",
            "-y",
            "-i", str(temp_mp3),
            "-ar", "22050",
            "-ac", "1",
            "-c:a", "pcm_s16le",
            str(raw_tts_wav),
        ]
        subprocess.run(cmd_decode, capture_output=True, check=True)

        converted_success = False
        # 1. Neural Tone Color Converter (Normalizing Flow + HiFi-GAN)
        target_se_path = getattr(voice_profile, "speaker_embedding_path", None)
        if not target_se_path and getattr(voice_profile, "reference_audio", None):
            target_se_path = voice_profile.reference_audio

        if target_se_path and Path(target_se_path).exists():
            try:
                from src.audio.neural_cloner import get_neural_converter

                converter = get_neural_converter()
                converter.convert_voice(raw_tts_wav, Path(target_se_path), output_wav)
                converted_success = True
            except Exception as e_neural:
                from src.audio.cloner import logger as cloner_logger
                cloner_logger.warning(
                    f"Neural voice conversion encountered error ({e_neural}); falling back to WORLD vocoder"
                )

        # 2. Fallback to WORLD vocoder if neural conversion failed
        if not converted_success:
            try:
                from src.audio.cloner import morph_voice_world

                morph_voice_world(raw_tts_wav, voice_profile, output_wav)
            finally:
                if raw_tts_wav.exists():
                    raw_tts_wav.unlink()
        else:
            if raw_tts_wav.exists():
                raw_tts_wav.unlink()
    else:
        # Standard VoiceStudio mastering (highpass, EQ, compression, EBU R128 loudness)
        audio_filter = get_vocal_studio_filter()
        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(temp_mp3),
            "-af", audio_filter,
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
    voice: str = "en-US-AndrewNeural",
    rate: str = "-3%",
    voice_profile: Optional["VoiceProfile"] = None,
) -> SynthesizedAudio:
    """Synchronous interface for neural voiceover synthesis with optional voice cloning."""
    return asyncio.run(
        _synthesize_edge_tts(text, voice, output_wav, rate=rate, voice_profile=voice_profile)
    )
