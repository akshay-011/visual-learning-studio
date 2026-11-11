# Provider Adapters & Integrations

Visual Learning Studio decouples creative logic from underlying inference and generation runtimes using an extensible provider adapter architecture.

## 1. Local LLM Provider (`src/research/engine.py`)

Communicates with local inference servers conforming to the Ollama REST API or OpenAI-compatible local endpoints.

- **Primary Endpoint:** `http://127.0.0.1:11434/api/generate` and `/api/chat`
- **Supported Backends:** Ollama, LocalAI, vLLM, llama.cpp server.
- **Fail-Safe Mechanism:** If the local LLM daemon is offline, times out, or runs out of context memory, the engine falls back to an embedded deterministic heuristic parser that extracts AST structures, markdown sections, or code blocks to guarantee 100% video completion.

## 2. Voice & Narration Provider (`src/audio/tts_engine.py`)

- **Primary Provider (Edge-TTS):** Interacts with Microsoft's public read-aloud service via websockets. Generates 48 kHz high-definition audio and extracts word-level boundary metadata for frame-accurate subtitles.
- **Offline Fallback (Piper TTS):** When network connectivity is absent, passes text directly to the local `piper` neural binary to synthesize clean, natural speech locally.

## 3. Visual Rendering Provider (`src/generation/visual_engine.py`)

- **Built-in Programmatic Engine:** High-performance Python-based procedural rendering engine. Generates 1920x1080 30/60fps frame sequences with sub-pixel anti-aliasing, glowing neon nodes, animated data packet trajectories, syntax-highlighted code panels, and kinetic typography.
- **Wan2GP MCP Adapter (`src/generation/wan2gp_adapter.py`):** Connects to any local or networked Wan2GP instance running the Model Context Protocol (MCP) Streamable HTTP server on port 7866. Facilitates cinematic AI video generation when high-VRAM workstation hardware is detected.
- **Stable Diffusion WebUI Adapter (`src/generation/sd_adapter.py`):** Interfaces with AUTOMATIC1111 or ComfyUI on port 7860/8188 for background keyframe generation.

## 4. Audio Mixing Provider (`src/audio/sound_mixer.py`)

- Uses FFmpeg's `amix`, `sidechaincompress`, and `volume` filters.
- Implements an automated broadcast audio chain:
  - Dialogue normalization (-16 LUFS target).
  - Music sidechain ducking (-24 dB reduction during speech).
  - Contextual sound effect placement with millisecond precision.
