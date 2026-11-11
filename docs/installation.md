# Installation & Setup Guide

Visual Learning Studio is designed for rapid, dependency-light deployment on modern Linux, macOS, and Windows environments.

## Prerequisites

1. **Python 3.10+** (Tested on Python 3.12 and 3.14)
2. **FFmpeg & FFprobe** with H.264 support (and optional NVENC on NVIDIA systems):
   ```bash
   # Arch Linux / Omarchy
   sudo pacman -S ffmpeg
   
   # Ubuntu / Debian
   sudo apt update && sudo apt install -y ffmpeg
   ```
3. **uv** (recommended for sub-second virtualenv setup):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
4. **Local LLM Engine (Optional but recommended):**
   - Install and launch Ollama:
     ```bash
     curl -fsSL https://ollama.com/install.sh | sh
     ollama serve &
     ollama pull qwen2.5-coder:7b
     ```

## Quick Installation

```bash
# 1. Clone or navigate to the repository
cd /home/akshay/workspace/make-video

# 2. Create virtual environment using uv
uv venv .venv --python 3.12
source .venv/bin/activate

# 3. Install core production dependencies
uv pip install -e .

# 4. Verify system readiness
python scripts/studio.py --check-hardware
```

## Running the Acceptance Tests

```bash
pytest tests/
```
