# Supported Models & Licensing Matrix

Visual Learning Studio adheres to an absolute **Zero Monetary Cost Policy**. Every model, runtime, and asset used is either open-weights, open-source, or licensed for unrestricted personal/educational use.

## Cognition & Reasoning Models

| Model | Size | License | Role in Visual Learning Studio | Hardware Requirement |
| :--- | :--- | :--- | :--- | :--- |
| **Qwen2.5-Coder 7B** | 4.7 GB | Apache 2.0 | Primary local researcher, scriptwriter, and storyboard architect | 6 GB VRAM or 8 GB System RAM |
| **Gemma 2 / Gemma 4** | 9.6 GB | Gemma Terms of Use | Secondary deep reasoning and architectural synthesis | 8 GB VRAM or 16 GB System RAM |
| **Deterministic Fallback Engine** | 0 MB | MIT (Built-in) | Instant heuristic lesson structuring when LLMs are offline | < 100 MB RAM |

## Speech Synthesis (TTS) Models

| Engine | Model / Voice | License | Features | Hardware Requirement |
| :--- | :--- | :--- | :--- | :--- |
| **Edge-TTS** | `en-US-ChristopherNeural` | Free Service Tier | High-fidelity documentary baritone, natural cadence | Zero GPU, HTTP stream |
| **Edge-TTS** | `en-US-GuyNeural` | Free Service Tier | Energetic explainer tone, high retention | Zero GPU, HTTP stream |
| **Edge-TTS** | `en-US-JennyNeural` | Free Service Tier | Conversational, approachable teacher persona | Zero GPU, HTTP stream |
| **Piper TTS** | `en_US-lessac-medium` | MIT / Public Domain | Completely offline local neural TTS binary | 1 CPU core |

## Audio Assets

| Asset Type | Source | Creator / License | Usage Policy |
| :--- | :--- | :--- | :--- |
| **Background Music** | `ende.app` "Happy Beats / Business Moves" (Vol 1–12) | Sascha Ende / CC BY 4.0 | Royalty-free with attribution included in outro |
| **Sound Effects (SFX)** | Kenney Sound Pack (Impact, Interface, UI, Keyboard) | Kenney.nl / CC0 (Public Domain) | Unrestricted public domain sound assets |

## Video & Animation Technologies

| Component | Framework | License | Rendering Method |
| :--- | :--- | :--- | :--- |
| **Programmatic 2D/3D Engine** | Pillow + NumPy + Pygments | MIT / BSD | Sub-pixel procedural animation, glowing diagrams |
| **Video Encoding** | FFmpeg (NVENC + libx264) | LGPL / GPL | 1080p60 hardware-accelerated H.264/AAC muxing |
| **Subtitle Engine** | FFmpeg `subtitles` filter / SRT | LGPL | Burned-in glowing subtitle typography |
| **Wan2GP Adapter (Optional)** | Wan 2.1 Video via MCP | Apache 2.0 | Optional external GPU acceleration (Requires >= 16GB VRAM) |
