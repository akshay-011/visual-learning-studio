"""Tests for speech synthesis and audio measurement."""

from pathlib import Path
from src.audio.tts_engine import synthesize_narration, get_audio_duration


def test_synthesize_narration(tmp_path: Path):
    wav_path = tmp_path / "test_dialogue.wav"
    synth = synthesize_narration("Fast API test.", wav_path)

    assert wav_path.exists()
    assert synth.duration > 0.3
    assert len(synth.srt_content) > 0

    measured_duration = get_audio_duration(wav_path)
    assert abs(measured_duration - synth.duration) < 0.1
