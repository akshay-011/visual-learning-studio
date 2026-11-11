# Hardware Detection & Profile Architecture

Visual Learning Studio autonomously probes host system topology at startup to select the optimal production profile without requiring user intervention.

## Discovered Hardware Specification

The following hardware configuration was probed directly from the execution environment:

| Component | Detected Specification | Studio Operational Impact |
| :--- | :--- | :--- |
| **Operating System** | Linux omarchy 7.2.15-1-omarchy (x86_64) | Full POSIX shell, native FFmpeg, low-overhead scheduling |
| **CPU** | 13th Gen Intel(R) Core(TM) i5-13420H | 12 vCPUs (4 P-cores + 4 E-cores), boost clock up to 4.60 GHz |
| **System Memory** | 15.3 GiB RAM + 30 GiB swap | Sufficient for 1080p frame composition and Ollama 7B context |
| **GPU** | NVIDIA GeForce RTX 3050 Laptop GPU | 6144 MiB (6 GB) VRAM, Driver 615.78.08, CUDA 13.4 |
| **Hardware Encoders** | NVENC (`h264_nvenc`, `hevc_nvenc`) | High-speed 1080p60 hardware video encoding enabled |
| **Disk Storage** | 174 GiB available on `/home` | Ample capacity for high-bitrate video caching and rendering |
| **Local Runtimes** | Python 3.12 (uv), Node.js v26.13, Ollama 0.40.7 | Fully zero-cost local execution stack |

## Production Profiles

Visual Learning Studio implements three tiered operational profiles designed to maximize quality while preventing out-of-memory (OOM) failures:

### 1. LIGHTWEIGHT Profile
- **Target Hardware:** Systems with integrated graphics or no dedicated GPU (Intel UHD, Iris Xe, AMD APUs, CPU-only servers), < 8 GB RAM.
- **Inference:** Fast local heuristic templates or quantized 3B LLMs (Ollama `qwen2.5:3b` or `phi3`).
- **Rendering:** CPU-based FFmpeg software rendering (`libx264 -preset fast`).
- **Visuals:** 1080p programmatic 2D architecture diagrams, kinetic typography, syntax cards.
- **Voice:** `edge-tts` streaming or local Piper TTS CPU binary.

### 2. BALANCED Profile (Selected on Current System)
- **Target Hardware:** Dedicated consumer GPUs with 4 GB – 8 GB VRAM (RTX 3050, GTX 1660, RTX 2060, Apple Silicon 16GB).
- **Inference:** Local 7B reasoning models (`qwen2.5-coder:7b`, `gemma4`) via Ollama.
- **Rendering:** Hardware-accelerated FFmpeg NVENC (`h264_nvenc -preset p4 -cq 20`) for sub-minute 1080p export.
- **Visuals:** 1080p 60fps programmatic animations, procedural particle dynamics, dynamic glowing network packet routing, animated code walkthroughs, high-contrast technical schematics.
- **Voice:** Neural TTS with precise word-level synchronization and multi-track audio ducking.

### 3. HIGH PERFORMANCE Profile
- **Target Hardware:** Workstation GPUs with >= 16 GB VRAM (RTX 3090, RTX 4090, A100).
- **Inference:** Local 14B/32B models (`qwen2.5:14b`, `deepseek-r1:14b`).
- **Rendering:** Full GPU composition pipeline with optional local diffusion visual generation (Stable Diffusion WebUI / ComfyUI / Wan2GP adapter).
- **Visuals:** Hybrid cinematic shots combining 3D Blender models, photorealistic AI keyframes, and motion graphic overlays.

## Automated Selection Logic

The hardware detector (`src/discovery/hardware.py`) computes an optimal profile using the following deterministic state machine:

```
[System Probe] 
     │
     ├── Has NVIDIA GPU with CUDA & >= 14GB VRAM? ──> HIGH PERFORMANCE
     │
     ├── Has NVIDIA GPU with CUDA & >= 4GB VRAM?  ──> BALANCED (Active)
     │
     └── Integrated GPU or CPU-only?              ──> LIGHTWEIGHT
```
