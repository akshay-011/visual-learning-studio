"""Unit tests for Voice Cloning and Acoustic Enrollment Engine."""

import math
import struct
import wave
from pathlib import Path
import pytest
import numpy as np

from src.audio.cloner import (
    VoiceProfile,
    analyze_voice_acoustics,
    enroll_voice,
    extract_world_acoustic_profile,
    get_voice_clone_filter,
    list_voice_profiles,
    load_voice_profile,
    morph_voice_world,
)
from src.audio.tts_engine import synthesize_narration


def _generate_synthetic_voice(
    file_path: Path,
    f0_hz: float = 140.0,
    duration_sec: float = 2.0,
    sample_rate: int = 48000,
) -> Path:
    """Generates a synthetic speech-like tone with pitch F0 and multiple vocal harmonics."""
    t = np.linspace(0, duration_sec, int(sample_rate * duration_sec), endpoint=False)
    # Fundamental + 3 harmonics + slight vibrato modulation to simulate human vocal folds
    vibrato = 1.0 + 0.015 * np.sin(2 * np.pi * 5.0 * t)
    sig = (
        0.55 * np.sin(2 * np.pi * f0_hz * vibrato * t)
        + 0.25 * np.sin(2 * np.pi * 2 * f0_hz * vibrato * t)
        + 0.15 * np.sin(2 * np.pi * 3 * f0_hz * vibrato * t)
        + 0.05 * np.sin(2 * np.pi * 4 * f0_hz * vibrato * t)
    )
    # Apply soft attack and decay envelope
    envelope = np.ones_like(sig)
    fade_len = int(sample_rate * 0.05)
    envelope[:fade_len] = np.linspace(0, 1, fade_len)
    envelope[-fade_len:] = np.linspace(1, 0, fade_len)
    sig = sig * envelope

    pcm_data = (sig * 32767.0).astype(np.int16)
    with wave.open(str(file_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data.tobytes())

    return file_path


def test_analyze_voice_acoustics(tmp_path: Path):
    """Verifies that acoustic feature extraction captures pitch and formant bands accurately."""
    wav_path = tmp_path / "synth_voice.wav"
    _generate_synthetic_voice(wav_path, f0_hz=145.0, duration_sec=2.0)

    acoustics = analyze_voice_acoustics(wav_path)

    assert acoustics["duration_seconds"] >= 1.9
    assert 130.0 <= acoustics["f0_median_hz"] <= 160.0
    assert acoustics["vocal_register"] in ["Baritone / Bass", "Tenor / Neutral"]
    assert "sub_bass" in acoustics["eq_gains"]
    assert "presence" in acoustics["eq_gains"]
    assert 0.70 <= acoustics["pitch_ratio"] <= 1.40


def test_enroll_and_load_voice_profile(tmp_path: Path):
    """Verifies voice enrollment, file persistence, and profile retrieval."""
    wav_path = tmp_path / "raw_recording.wav"
    _generate_synthetic_voice(wav_path, f0_hz=120.0, duration_sec=2.5)

    voices_dir = tmp_path / "voices"
    profile = enroll_voice(wav_path, profile_name="test_speaker", voices_dir=voices_dir)

    assert profile.profile_name == "test_speaker"
    assert profile.is_valid is True
    assert (voices_dir / "test_speaker" / "profile.json").exists()
    assert (voices_dir / "test_speaker" / "reference.wav").exists()

    # Verify loading by name
    loaded = load_voice_profile("test_speaker", voices_dir=voices_dir)
    assert loaded.profile_name == "test_speaker"
    assert loaded.f0_median_hz == profile.f0_median_hz
    assert (voices_dir / "test_speaker" / "spectral_signature.npz").exists()
    assert loaded.spectral_signature_path is not None

    # Verify listing
    profiles = list_voice_profiles(voices_dir=voices_dir)
    assert len(profiles) == 1
    assert profiles[0].profile_name == "test_speaker"


def test_get_voice_clone_filter(tmp_path: Path):
    """Verifies that the generated FFmpeg DSP filter contains all required cloning stages."""
    profile = VoiceProfile(
        profile_name="dsp_test",
        reference_audio=str(tmp_path / "ref.wav"),
        duration_seconds=5.0,
        f0_mean_hz=135.0,
        f0_median_hz=135.0,
        f0_std_hz=15.0,
        vocal_register="Tenor / Neutral",
        base_voice="en-US-BrianNeural",
        base_f0_hz=145.0,
        pitch_ratio=0.9310,
        pitch_semitones=-1.2,
        eq_gains={
            "sub_bass": 1.2,
            "low_mid": -0.5,
            "mid": 0.8,
            "high_mid": -0.2,
            "presence": 1.5,
        },
        speech_rms=0.15,
        is_valid=True,
    )

    filter_str = get_voice_clone_filter(profile)
    assert "rubberband=pitch=0.9310" in filter_str
    assert "equalizer=f=120:t=q:w=1.2:g=1.20" in filter_str
    assert "equalizer=f=8000:t=q:w=1.5:g=1.50" in filter_str
    assert "loudnorm=" in filter_str


def test_synthesize_with_cloned_voice(tmp_path: Path):
    """End-to-end verification of dialogue synthesis with active voice cloning."""
    ref_wav = tmp_path / "user_sample.wav"
    _generate_synthetic_voice(ref_wav, f0_hz=125.0, duration_sec=2.0)

    profile = enroll_voice(ref_wav, profile_name="unit_user", voices_dir=tmp_path / "voices")

    out_wav = tmp_path / "cloned_dialogue.wav"
    synth = synthesize_narration(
        "Verifying voice cloning acoustic transformation.",
        out_wav,
        voice_profile=profile,
    )

    assert out_wav.exists()
    assert synth.duration > 0.5
    assert synth.wav_path == out_wav


def test_extract_world_acoustic_profile(tmp_path: Path):
    """Verifies that WORLD vocoder extracts continuous Log-F0 and 1025-bin spectral envelope."""
    wav_path = tmp_path / "voice_sample.wav"
    _generate_synthetic_voice(wav_path, f0_hz=135.0, duration_sec=1.5)

    profile_data = extract_world_acoustic_profile(wav_path)

    assert 120.0 <= profile_data["f0_median_hz"] <= 150.0
    assert 4.5 <= profile_data["f0_log_mean"] <= 5.2
    assert profile_data["f0_log_std"] >= 0.0
    assert len(profile_data["mean_sp"]) == 1025
    assert len(profile_data["mean_ap"]) == 1025
    assert len(profile_data["formants"]) > 0


def test_morph_voice_world(tmp_path: Path):
    """Verifies WORLD vocoder resynthesis, Log-F0 mapping, and vocal tract transfer."""
    ref_wav = tmp_path / "ref_voice.wav"
    _generate_synthetic_voice(ref_wav, f0_hz=110.0, duration_sec=2.0)
    profile = enroll_voice(ref_wav, profile_name="morph_test", voices_dir=tmp_path / "voices")

    base_wav = tmp_path / "base_tts.wav"
    _generate_synthetic_voice(base_wav, f0_hz=155.0, duration_sec=2.0)

    morphed_wav = tmp_path / "morphed_out.wav"
    res = morph_voice_world(base_wav, profile, morphed_wav)

    assert res.exists()
    assert res.stat().st_size > 10000

    # Verify morphed audio has shifted pitch towards target
    from src.audio.cloner import analyze_voice_acoustics
    morphed_acoustics = analyze_voice_acoustics(res)
    # Target was 110 Hz, base was 155 Hz; morphed should be significantly lower than base
    assert morphed_acoustics["f0_median_hz"] < 140.0

