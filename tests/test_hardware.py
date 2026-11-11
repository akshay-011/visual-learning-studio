"""Tests for hardware detection and profile assignment."""

from src.discovery.hardware import detect_hardware, HardwareReport


def test_detect_hardware_returns_valid_report():
    report = detect_hardware()
    assert isinstance(report, HardwareReport)
    assert report.cpu_cores >= 1
    assert report.ram_gb > 0.5
    assert report.profile in ["LIGHTWEIGHT", "BALANCED", "HIGH_PERFORMANCE"]
    assert report.recommended_encoder in ["h264_nvenc", "libx264"]
