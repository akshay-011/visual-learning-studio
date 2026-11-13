"""Unit tests for Google Assistant-style Voice Match Calibration Engine."""

import wave
from pathlib import Path
import numpy as np
import pytest

from src.audio.cloner import (
    VOICE_MATCH_PROMPTS,
    VoiceProfile,
    fuse_voice_takes,
    load_voice_profile,
    run_voice_match_setup,
)


def _create_tone_take(file_path: Path, f0: float, duration_sec: float = 1.0) -> Path:
    """Creates a synthetic speech-like tone file for deterministic testing."""
    sr = 48000
    t = np.linspace(0, duration_sec, int(sr * duration_sec), endpoint=False)
    sig = 0.5 * np.sin(2 * np.pi * f0 * t) + 0.25 * np.sin(2 * np.pi * 2 * f0 * t)
    pcm = (sig * 32767.0).astype(np.int16)

    with wave.open(str(file_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())
    return file_path


def test_voice_match_prompts_structure():
    """Verifies that all 4 Google Assistant calibration prompts are configured."""
    assert len(VOICE_MATCH_PROMPTS) == 4
    for idx, prompt in enumerate(VOICE_MATCH_PROMPTS, start=1):
        assert prompt["id"] == idx
        assert "title" in prompt
        assert len(prompt["text"]) > 10
        assert "tip" in prompt
        assert prompt["duration"] >= 4.0


def test_fuse_voice_takes(tmp_path: Path):
    """Verifies that multi-phrase calibration takes are concatenated properly."""
    take1 = _create_tone_take(tmp_path / "take1.wav", 130.0, 1.0)
    take2 = _create_tone_take(tmp_path / "take2.wav", 140.0, 1.2)
    take3 = _create_tone_take(tmp_path / "take3.wav", 150.0, 0.8)

    fused_out = tmp_path / "fused_master.wav"
    result = fuse_voice_takes([take1, take2, take3], fused_out)

    assert result.exists()
    assert result.stat().st_size > 1000

    with wave.open(str(result), "rb") as wf:
        duration = wf.getnframes() / wf.getframerate()
        assert 2.9 <= duration <= 3.2


def test_run_voice_match_setup_with_custom_takes(tmp_path: Path):
    """Verifies the complete Voice Match enrollment flow using simulated takes."""
    takes_dir = tmp_path / "raw_takes"
    takes_dir.mkdir(parents=True, exist_ok=True)

    take_paths = [
        _create_tone_take(takes_dir / "t1.wav", 135.0, 1.5),
        _create_tone_take(takes_dir / "t2.wav", 140.0, 1.5),
        _create_tone_take(takes_dir / "t3.wav", 130.0, 1.5),
        _create_tone_take(takes_dir / "t4.wav", 138.0, 1.5),
    ]

    voices_dir = tmp_path / "voices"
    profile = run_voice_match_setup(
        profile_name="assistant_match_test",
        voices_dir=voices_dir,
        interactive=False,
        custom_takes=take_paths,
        synthesize_audition=True,
    )

    assert profile.profile_name == "assistant_match_test"
    assert profile.is_valid is True
    assert len(profile.takes) == 4
    assert (voices_dir / "assistant_match_test" / "reference.wav").exists()
    assert (voices_dir / "assistant_match_test" / "profile.json").exists()
    assert (voices_dir / "assistant_match_test" / "audition.wav").exists()
    assert (voices_dir / "assistant_match_test" / "spectral_signature.npz").exists()
    assert profile.spectral_signature_path is not None
    assert profile.audition_audio is not None

    # Load and verify
    loaded = load_voice_profile("assistant_match_test", voices_dir=voices_dir)
    assert loaded.profile_name == "assistant_match_test"
    assert loaded.f0_median_hz == profile.f0_median_hz
    assert loaded.spectral_signature_path is not None
    assert len(loaded.takes) == 4
