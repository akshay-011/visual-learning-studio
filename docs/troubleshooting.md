# Troubleshooting Guide

Common issues, diagnostics, and deterministic resolutions for Visual Learning Studio.

## 1. Hardware & FFmpeg Issues

### Issue: `h264_nvenc` fails or produces `Device creation failed`
- **Cause:** NVIDIA driver mismatch, missing CUDA toolkit, or running inside a headless container without GPU pass-through.
- **Resolution:** Visual Learning Studio automatically falls back to CPU encoding (`libx264`). To force CPU encoding explicitly:
  ```bash
  export VLS_FFMPEG_ENCODER=libx264
  ```

### Issue: FFmpeg command not found
- **Cause:** FFmpeg is not installed or not in system `$PATH`.
- **Resolution:**
  ```bash
  # Arch / Omarchy Linux
  sudo pacman -S ffmpeg
  # Debian / Ubuntu
  sudo apt install ffmpeg
  ```

## 2. Voice & Audio Issues

### Issue: `edge-tts` network timeout or connection refused
- **Cause:** Temporary network disconnection or firewall blocking Microsoft Read-Aloud websocket.
- **Resolution:**
  1. The studio automatically retries with exponential backoff.
  2. If running fully air-gapped, switch to the offline Piper TTS engine:
     ```bash
     export VLS_TTS_ENGINE=piper
     ```

### Issue: Subtitles are out of sync with narration
- **Cause:** Variable bitrate MP3 encoding or mismatched sample rate.
- **Resolution:** VLS strictly generates fixed-frame PCM 48kHz WAV audio during staging, extracting exact millisecond timestamps directly from the TTS phoneme events before burning subtitles into MP4.

## 3. Ollama / Reasoning Issues

### Issue: Ollama server not responding on `127.0.0.1:11434`
- **Cause:** Ollama service is inactive.
- **Resolution:**
  ```bash
  ollama serve &
  ```
  Even if Ollama is absent, Visual Learning Studio will automatically activate its built-in AST / heuristic research engine and proceed with production without crashing.
