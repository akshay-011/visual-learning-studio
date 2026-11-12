"""Voice Recording, Enrollment, and Voice Cloning Engine.

Enables local users to record their voice via system microphone or import an existing
audio reference, extract acoustic signatures (fundamental pitch F0, vocal tract
formant distribution, and dynamic profile), and synthesize narration matching their
cloned vocal timbre at zero monetary cost.
"""

from __future__ import annotations

import json
import logging
import math
import shutil
import subprocess
import time
import wave
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from pydantic import BaseModel, Field

from src.audio.voicestudio import get_vocal_studio_filter

logger = logging.getLogger("visual_studio.cloner")

DEFAULT_PROMPT_SENTENCE = (
    "Distributed architectures achieve resilient state consistency through "
    "asynchronous replication, cryptographic handshakes, and in-memory caching."
)

# Reference baseline frequencies and matching base neural models
BASE_VOICE_REGISTERS = [
    # (max_f0, voice_name, typical_f0, register_label)
    (135.0, "en-US-AndrewNeural", 118.0, "Baritone / Bass"),
    (175.0, "en-US-BrianNeural", 145.0, "Tenor / Neutral"),
    (225.0, "en-US-AvaNeural", 195.0, "Alto / Contralto"),
    (9999.0, "en-US-JennyNeural", 235.0, "Soprano / Mezzo"),
]

# Standard reference spectral energy percentages for neutral vocal
TARGET_BAND_PERCENTAGES = {
    "sub_bass": 48.0,   # 80 - 250 Hz
    "low_mid": 30.0,    # 250 - 800 Hz
    "mid": 12.0,        # 800 - 2500 Hz
    "high_mid": 7.0,    # 2500 - 5000 Hz
    "presence": 3.0,    # 5000 - 12000 Hz
}


class VoiceProfile(BaseModel):
    """Enrolled acoustic profile of a user or cloned speaker."""

    profile_name: str
    reference_audio: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    duration_seconds: float
    f0_mean_hz: float
    f0_median_hz: float
    f0_std_hz: float
    vocal_register: str
    base_voice: str
    base_f0_hz: float
    pitch_ratio: float
    pitch_semitones: float
    eq_gains: Dict[str, float]
    speech_rms: float
    is_valid: bool = True


def record_voice_clip(
    output_wav: Path,
    duration_seconds: float = 8.0,
    device: str = "default",
) -> Path:
    """Records audio from system microphone using PulseAudio/PipeWire or ALSA."""
    output_wav.parent.mkdir(parents=True, exist_ok=True)
    temp_raw = output_wav.with_suffix(".raw.wav")

    # Attempt 1: FFmpeg with PulseAudio/PipeWire default source
    cmd_pulse = [
        "ffmpeg",
        "-y",
        "-f", "pulse",
        "-i", device,
        "-t", str(duration_seconds),
        "-ar", "48000",
        "-ac", "2",
        "-c:a", "pcm_s16le",
        str(temp_raw),
    ]

    try:
        subprocess.run(cmd_pulse, capture_output=True, check=True)
    except Exception as e1:
        logger.warning(f"Pulse capture failed ({e1}), falling back to ALSA...")
        # Attempt 2: FFmpeg with ALSA
        cmd_alsa = [
            "ffmpeg",
            "-y",
            "-f", "alsa",
            "-i", "default",
            "-t", str(duration_seconds),
            "-ar", "48000",
            "-ac", "2",
            "-c:a", "pcm_s16le",
            str(temp_raw),
        ]
        try:
            subprocess.run(cmd_alsa, capture_output=True, check=True)
        except Exception as e2:
            # Attempt 3: pw-record
            cmd_pw = [
                "pw-record",
                "--rate", "48000",
                "--channels", "2",
                str(temp_raw),
            ]
            try:
                proc = subprocess.Popen(cmd_pw)
                time.sleep(duration_seconds)
                proc.terminate()
                proc.wait(timeout=2.0)
            except Exception as e3:
                raise RuntimeError(
                    f"Microphone recording failed across all interfaces (Pulse, ALSA, PipeWire): {e1} | {e2} | {e3}"
                )

    if not temp_raw.exists() or temp_raw.stat().st_size < 1000:
        raise RuntimeError("Recorded audio file is empty or capture failed.")

    # Clean and calibrate the recorded raw audio
    clean_voice_sample(temp_raw, output_wav)
    if temp_raw.exists():
        temp_raw.unlink()

    return output_wav


def clean_voice_sample(raw_wav: Path, clean_wav: Path) -> Path:
    """Cleans recorded voice sample: cuts rumble, gates silence, and normalizes."""
    clean_wav.parent.mkdir(parents=True, exist_ok=True)
    filter_chain = (
        "highpass=f=80,"
        "silenceremove=start_periods=1:start_duration=0.08:start_threshold=-45dB:"
        "stop_periods=1:stop_duration=0.3:stop_threshold=-45dB,"
        "loudnorm=I=-16:TP=-1.5:LRA=9"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(raw_wav),
        "-af", filter_chain,
        "-ar", "48000",
        "-ac", "2",
        "-c:a", "pcm_s16le",
        str(clean_wav),
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return clean_wav


def analyze_voice_acoustics(wav_path: Path) -> Dict[str, Any]:
    """Extracts fundamental pitch F0 and 5-band spectral formant distribution."""
    if not wav_path.exists():
        raise FileNotFoundError(f"Audio file not found: {wav_path}")

    with wave.open(str(wav_path), "rb") as wf:
        sample_rate = wf.getframerate()
        n_channels = wf.getnchannels()
        n_frames = wf.getnframes()
        raw_bytes = wf.readframes(n_frames)

    audio = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    if n_channels > 1:
        audio = audio.reshape(-1, n_channels).mean(axis=1)

    duration = float(len(audio) / sample_rate)
    speech_rms = float(np.sqrt(np.mean(audio**2)))

    # 1. Pitch Extraction via Short-Time Autocorrelation
    frame_len = int(sample_rate * 0.035)  # 35ms window
    hop_len = int(sample_rate * 0.010)    # 10ms hop
    min_lag = int(sample_rate / 400.0)    # 400 Hz upper pitch limit
    max_lag = int(sample_rate / 65.0)     # 65 Hz lower pitch limit

    pitches = []
    for start in range(0, len(audio) - frame_len, hop_len):
        frame = audio[start : start + frame_len]
        frame_rms = np.sqrt(np.mean(frame**2))
        if frame_rms < 0.015:  # Ignore background silence/breaths
            continue

        w_frame = frame * np.hamming(len(frame))
        corr = np.correlate(w_frame, w_frame, mode="full")
        corr = corr[len(corr) // 2 :]

        if len(corr) < max_lag:
            continue

        peak_lag = min_lag + int(np.argmax(corr[min_lag:max_lag]))
        # Harmonic quality threshold
        if corr[0] > 0 and (corr[peak_lag] / corr[0]) > 0.28:
            pitch = sample_rate / float(peak_lag)
            if 65.0 <= pitch <= 400.0:
                pitches.append(pitch)

    if pitches:
        f0_mean = float(np.mean(pitches))
        f0_median = float(np.median(pitches))
        f0_std = float(np.std(pitches))
    else:
        # Fallback to neutral default pitch if audio was unvoiced/whispered
        f0_mean = 135.0
        f0_median = 135.0
        f0_std = 25.0

    # 2. Spectral Band Energy & Formant Analysis
    fft_vals = np.abs(np.fft.rfft(audio))
    freqs = np.fft.rfftfreq(len(audio), 1.0 / sample_rate)

    bands = {
        "sub_bass": (80.0, 250.0),
        "low_mid": (250.0, 800.0),
        "mid": (800.0, 2500.0),
        "high_mid": (2500.0, 5000.0),
        "presence": (5000.0, 12000.0),
    }

    raw_energies = {}
    for name, (low, high) in bands.items():
        idx = (freqs >= low) & (freqs < high)
        raw_energies[name] = float(np.mean(fft_vals[idx])) if np.any(idx) else 0.0

    total_energy = sum(raw_energies.values()) or 1.0
    measured_pct = {k: (v / total_energy) * 100.0 for k, v in raw_energies.items()}

    # Compute 5-band EQ offsets relative to standard target vocal curve
    eq_gains = {}
    for band_name, target_pct in TARGET_BAND_PERCENTAGES.items():
        diff_pct = measured_pct.get(band_name, target_pct) - target_pct
        # 10% deviation roughly corresponds to ~1.5 dB EQ offset, clamped to [-4.5, +4.5] dB
        gain_db = round(float(np.clip(diff_pct * 0.15, -4.5, 4.5)), 2)
        eq_gains[band_name] = gain_db

    # 3. Base Neural Voice Matching
    selected_voice = "en-US-AndrewNeural"
    base_f0 = 118.0
    vocal_register = "Baritone / Bass"

    for max_f0, voice_name, ref_f0, reg_label in BASE_VOICE_REGISTERS:
        if f0_median < max_f0:
            selected_voice = voice_name
            base_f0 = ref_f0
            vocal_register = reg_label
            break

    # Calculate required pitch shifting factor
    pitch_ratio = round(float(f0_median / base_f0), 4)
    # Clamp pitch ratio to prevent synthetic distortion
    pitch_ratio = float(np.clip(pitch_ratio, 0.72, 1.38))
    pitch_semitones = round(12.0 * math.log2(pitch_ratio), 2)

    return {
        "duration_seconds": round(duration, 2),
        "speech_rms": round(speech_rms, 4),
        "f0_mean_hz": round(f0_mean, 1),
        "f0_median_hz": round(f0_median, 1),
        "f0_std_hz": round(f0_std, 1),
        "vocal_register": vocal_register,
        "base_voice": selected_voice,
        "base_f0_hz": base_f0,
        "pitch_ratio": pitch_ratio,
        "pitch_semitones": pitch_semitones,
        "eq_gains": eq_gains,
    }


def enroll_voice(
    reference_path: Path,
    profile_name: str = "my_voice",
    voices_dir: Optional[Path] = None,
) -> VoiceProfile:
    """Enrolls an audio reference into a persistent VoiceProfile."""
    if not reference_path.exists():
        raise FileNotFoundError(f"Reference voice audio not found: {reference_path}")

    if voices_dir is None:
        voices_dir = Path(__file__).resolve().parent.parent.parent / "assets" / "voices"

    profile_dir = voices_dir / profile_name
    profile_dir.mkdir(parents=True, exist_ok=True)

    dest_ref = profile_dir / "reference.wav"
    clean_voice_sample(reference_path, dest_ref)

    acoustics = analyze_voice_acoustics(dest_ref)

    profile = VoiceProfile(
        profile_name=profile_name,
        reference_audio=str(dest_ref.resolve()),
        duration_seconds=acoustics["duration_seconds"],
        f0_mean_hz=acoustics["f0_mean_hz"],
        f0_median_hz=acoustics["f0_median_hz"],
        f0_std_hz=acoustics["f0_std_hz"],
        vocal_register=acoustics["vocal_register"],
        base_voice=acoustics["base_voice"],
        base_f0_hz=acoustics["base_f0_hz"],
        pitch_ratio=acoustics["pitch_ratio"],
        pitch_semitones=acoustics["pitch_semitones"],
        eq_gains=acoustics["eq_gains"],
        speech_rms=acoustics["speech_rms"],
        is_valid=True,
    )

    profile_json = profile_dir / "profile.json"
    with open(profile_json, "w", encoding="utf-8") as f:
        f.write(profile.model_dump_json(indent=2))

    logger.info(
        f"Enrolled voice profile '{profile_name}': F0={profile.f0_median_hz}Hz, "
        f"Base={profile.base_voice}, PitchRatio={profile.pitch_ratio}"
    )
    return profile


def load_voice_profile(
    name_or_path: str,
    voices_dir: Optional[Path] = None,
) -> VoiceProfile:
    """Loads an enrolled VoiceProfile by name, directory path, or audio file."""
    if voices_dir is None:
        voices_dir = Path(__file__).resolve().parent.parent.parent / "assets" / "voices"

    target_path = Path(name_or_path)

    # 1. Direct path to profile.json
    if target_path.is_file() and target_path.suffix == ".json":
        with open(target_path, "r", encoding="utf-8") as f:
            return VoiceProfile.model_validate_json(f.read())

    # 2. Named profile directory
    named_json = voices_dir / name_or_path / "profile.json"
    if named_json.exists():
        with open(named_json, "r", encoding="utf-8") as f:
            return VoiceProfile.model_validate_json(f.read())

    # 3. Direct audio file passed (e.g. sample.wav) -> Enroll on the fly
    if target_path.is_file() and target_path.suffix.lower() in [".wav", ".mp3", ".m4a", ".ogg", ".flac"]:
        stem_name = target_path.stem.replace(" ", "_").lower()
        return enroll_voice(target_path, profile_name=stem_name, voices_dir=voices_dir)

    raise FileNotFoundError(
        f"Voice profile '{name_or_path}' not found. Searched: {named_json} and {target_path}"
    )


def list_voice_profiles(voices_dir: Optional[Path] = None) -> List[VoiceProfile]:
    """Lists all enrolled voice profiles found in assets/voices."""
    if voices_dir is None:
        voices_dir = Path(__file__).resolve().parent.parent.parent / "assets" / "voices"

    if not voices_dir.exists():
        return []

    profiles = []
    for json_file in sorted(voices_dir.glob("*/profile.json")):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                profiles.append(VoiceProfile.model_validate_json(f.read()))
        except Exception as e:
            logger.warning(f"Failed to read profile at {json_file}: {e}")
    return profiles


def get_voice_clone_filter(profile: VoiceProfile) -> str:
    """Constructs the real-time DSP filter chain transforming base TTS to the cloned voice."""
    eq = profile.eq_gains
    filters = [
        # Formant-preserving pitch shifting via librubberband
        f"rubberband=pitch={profile.pitch_ratio:.4f}:pitchq=quality:formant=preserved",
        # 5-band vocal tract parametric resonance EQ
        f"equalizer=f=120:t=q:w=1.2:g={eq.get('sub_bass', 0.0):.2f}",
        f"equalizer=f=350:t=q:w=1.2:g={eq.get('low_mid', 0.0):.2f}",
        f"equalizer=f=1500:t=q:w=1.5:g={eq.get('mid', 0.0):.2f}",
        f"equalizer=f=3800:t=q:w=1.5:g={eq.get('high_mid', 0.0):.2f}",
        f"equalizer=f=8000:t=q:w=1.5:g={eq.get('presence', 0.0):.2f}",
        # Broadcast vocal studio mastering (highpass, de-esser, compressor, loudnorm)
        get_vocal_studio_filter(),
    ]
    return ",".join(filters)
