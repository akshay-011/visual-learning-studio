"""Tests for VoiceStudio pronunciation and cadence processing."""

from src.audio.voicestudio import apply_pronunciation_lexicon, process_human_cadence, get_vocal_studio_filter


def test_pronunciation_lexicon():
    raw = "The client sends an API request with JWT authentication to SQL database."
    processed = apply_pronunciation_lexicon(raw)
    assert "A P I" in processed
    assert "JOT" in processed
    assert "sequel" in processed


def test_process_human_cadence():
    raw = "Every request connects to the gateway [pause 300ms] for [emphasis]TLS[/emphasis] inspection."
    processed = process_human_cadence(raw)
    assert "..." in processed
    assert "T L S" in processed
    assert "[pause" not in processed
    assert "[emphasis]" not in processed


def test_vocal_studio_filter():
    f = get_vocal_studio_filter()
    assert "highpass=f=80" in f
    assert "equalizer=f=250" in f
    assert "acompressor" in f
    assert "loudnorm" in f
