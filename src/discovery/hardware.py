"""Autonomous hardware detection and production profile configuration."""

import os
import shutil
import subprocess
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional


@dataclass
class HardwareReport:
    os_name: str
    cpu_model: str
    cpu_cores: int
    ram_gb: float
    disk_available_gb: float
    gpu_name: Optional[str]
    vram_mb: Optional[int]
    has_cuda: bool
    ffmpeg_encoders: List[str]
    ollama_running: bool
    profile: str  # LIGHTWEIGHT | BALANCED | HIGH_PERFORMANCE
    recommended_encoder: str


def detect_hardware() -> HardwareReport:
    """Safely and deterministically probe host hardware capabilities."""
    # 1. OS & CPU
    os_name = os.uname().sysname if hasattr(os, "uname") else "Unknown"
    cpu_model = "Generic x86_64"
    cpu_cores = os.cpu_count() or 4

    try:
        if os.path.exists("/proc/cpuinfo"):
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "model name" in line:
                        cpu_model = line.split(":", 1)[1].strip()
                        break
    except Exception:
        pass

    # 2. RAM
    ram_gb = 8.0
    try:
        if os.path.exists("/proc/meminfo"):
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        kb = int(line.split()[1])
                        ram_gb = round(kb / (1024 * 1024), 2)
                        break
    except Exception:
        pass

    # 3. Disk space on current working directory filesystem
    disk_available_gb = 50.0
    try:
        stat = os.statvfs(".")
        disk_available_gb = round((stat.f_bavail * stat.f_frsize) / (1024**3), 2)
    except Exception:
        pass

    # 4. GPU & VRAM via nvidia-smi
    gpu_name = None
    vram_mb = None
    has_cuda = False

    if shutil.which("nvidia-smi"):
        try:
            cmd = [
                "nvidia-smi",
                "--query-gpu=gpu_name,memory.total",
                "--format=csv,noheader,nounits",
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
            if res.returncode == 0 and res.stdout.strip():
                lines = res.stdout.strip().split("\n")
                if lines:
                    parts = lines[0].split(",")
                    gpu_name = parts[0].strip()
                    vram_mb = int(parts[1].strip())
                    has_cuda = True
        except Exception:
            pass

    # 5. FFmpeg Encoders
    ffmpeg_encoders = []
    recommended_encoder = "libx264"
    if shutil.which("ffmpeg"):
        try:
            res = subprocess.run(
                ["ffmpeg", "-encoders"], capture_output=True, text=True, timeout=3
            )
            out = res.stdout or ""
            if "h264_nvenc" in out and has_cuda:
                ffmpeg_encoders.append("h264_nvenc")
            if "hevc_nvenc" in out and has_cuda:
                ffmpeg_encoders.append("hevc_nvenc")
            if "libx264" in out:
                ffmpeg_encoders.append("libx264")
        except Exception:
            pass

    # Test nvenc execution safely if detected
    if "h264_nvenc" in ffmpeg_encoders:
        recommended_encoder = "h264_nvenc"
    elif "libx264" in ffmpeg_encoders:
        recommended_encoder = "libx264"

    # 6. Ollama Service Status
    ollama_running = False
    try:
        import urllib.request
        req = urllib.request.Request("http://127.0.0.1:11434/api/tags")
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            if resp.status == 200:
                ollama_running = True
    except Exception:
        ollama_running = False

    # 7. Select Profile
    # HIGH_PERFORMANCE: GPU with >= 14 GB VRAM
    # BALANCED: GPU with >= 4 GB VRAM (e.g. RTX 3050 6GB)
    # LIGHTWEIGHT: CPU only or < 4GB VRAM
    if has_cuda and vram_mb and vram_mb >= 14000:
        profile = "HIGH_PERFORMANCE"
    elif has_cuda and vram_mb and vram_mb >= 4000:
        profile = "BALANCED"
    else:
        profile = "LIGHTWEIGHT"

    # Allow environment override
    override = os.environ.get("VLS_HARDWARE_PROFILE")
    if override and override.upper() in ["LIGHTWEIGHT", "BALANCED", "HIGH_PERFORMANCE"]:
        profile = override.upper()

    return HardwareReport(
        os_name=os_name,
        cpu_model=cpu_model,
        cpu_cores=cpu_cores,
        ram_gb=ram_gb,
        disk_available_gb=disk_available_gb,
        gpu_name=gpu_name,
        vram_mb=vram_mb,
        has_cuda=has_cuda,
        ffmpeg_encoders=ffmpeg_encoders,
        ollama_running=ollama_running,
        profile=profile,
        recommended_encoder=recommended_encoder,
    )


if __name__ == "__main__":
    report = detect_hardware()
    print("Detected Hardware Profile:", report.profile)
    print("Encoder:", report.recommended_encoder)
    print("GPU:", report.gpu_name, f"({report.vram_mb} MB VRAM)")
    print("Ollama Active:", report.ollama_running)
