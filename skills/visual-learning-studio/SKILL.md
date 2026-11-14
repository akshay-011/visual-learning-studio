---
name: visual-learning-studio
description: Zero-cost autonomous educational video production studio. Transforms technical topics, GitHub repositories, research papers, or documentation into broadcast-quality 1080p educational videos with animated diagrams, neural voiceover, background music, SFX, and synchronized subtitles.
---

# Visual Learning Studio (VLS) Skill

Visual Learning Studio teaches agents how to autonomously research, storyboard, animate, narrate, and render 1080p educational videos with zero monetary cost and zero external API credits.

## When to Activate This Skill

Activate whenever the user requests an educational, technical, or documentary video about any concept, repository, paper, or system.
Common triggers:
- "Teach me how RAG works."
- "Create a video explaining how an API request travels through a backend system."
- "Explain this GitHub repository visually: https://github.com/fastapi/fastapi"
- "Turn this research paper into a cinematic documentary."
- "Show me how a database indexes information."
- "Generate a 30-second explainer video on Kubernetes."

## Absolute Zero-Cost Policy

- **No paid API subscriptions:** Never require or call paid APIs (OpenAI, Anthropic, ElevenLabs, Runway, Midjourney, Replicate, MuAPI).
- **Local Inference:** AI cognition uses local Ollama (`qwen2.5-coder:7b` / `gemma4`) or built-in deterministic heuristic fallback.
- **Voiceover & Neural Voice Cloning:** Powered by zero-cost neural TTS with VoiceStudio human conversational prosody, technical acronym pronunciation dictionary, and 5-stage broadcast vocal mastering chain (`en-US-AndrewNeural`). Supports recording user voice (`./scripts/voice_setup.sh my_voice`) or cloning existing audio samples (`--clone-voice`) using OpenVoice V2 deep neural tone color conversion (normalizing flow + HiFi-GAN decoding) running locally on CUDA GPU.
- **Visuals:** 1080p programmatic animations, glowing network diagrams, data packet simulations, syntax-highlighted code editors, and metric dashboards rendered via Pillow + FFmpeg hardware acceleration (`h264_nvenc`).
- **Subtitles & Music:** Subtitles burning and background music are disabled by default for clean presentation; enabled on demand via `--burn-subtitles` and `--include-music`.

## Natural Language Voice Selection in AGY

You can prompt Antigravity / AGY naturally to select voices:

| User Prompt in AGY | Execution Command | Description |
| :--- | :--- | :--- |
| **"Create a video about X using my voice"** | `./scripts/run_production.sh --topic "X" --voice-profile my_voice` | Uses enrolled user voice with OpenVoice V2 neural cloning |
| **"Create a video about X using somebody's voice"** | `./scripts/run_production.sh --topic "X" --voice-profile <name>` | Uses specific enrolled speaker profile |
| **"Create a video about X using voice from sample.wav"** | `./scripts/run_production.sh --topic "X" --clone-voice sample.wav` | Clones voice from an external audio file |
| **"Create a video about X using Brian's voice"** | `./scripts/run_production.sh --topic "X" --voice brian` | Built-in conversational Tenor (`en-US-BrianNeural`) |
| **"Create a video about X using Ava's voice"** | `./scripts/run_production.sh --topic "X" --voice ava` | Built-in expressive Alto (`en-US-AvaNeural`) |
| **"Create a video about X using Jenny's voice"** | `./scripts/run_production.sh --topic "X" --voice jenny` | Built-in bright Soprano (`en-US-JennyNeural`) |
| **"Create a video about X using Andrew's voice"** | `./scripts/run_production.sh --topic "X" --voice andrew` | Built-in authoritative Baritone (default) |

## Specialized Subagent Roster in AGY

Antigravity CLI provides 7 specialized production subagents:

1. **`audio-director`**: Directs neural voiceover synthesis, voice cloning selection, sound effect sync, and EBU R128 mastering.
2. **`teacher`**: Instructional designer structuring progressive scaffolding, mental models, and the 5-second pedagogical hook.
3. **`researcher`**: Ingests codebases, GitHub repositories, and research papers; extracts core mechanisms and architectures.
4. **`scriptwriter`**: Drafts spoken dialogue scripts tailored to human speech cadence with strict word-budget timing.
5. **`storyboard-director`**: Unifies script, visual layout, packet pathways, and timing into machine-validated JSON.
6. **`visual-director`**: Governs color theory, typography, geometric hierarchy, and easing animations.
7. **`quality-checker`**: Automated video inspection gate verifying MP4 container validity, codecs, resolutions, and stream sync.

## Voice Recording & Google Assistant-Style Voice Match

You can calibrate and save your voice model just like setting up Google Assistant:

```bash
# 1. Launch the 4-phase Voice Match Calibration Wizard (Google Assistant Style)
./scripts/voice_setup.sh my_voice

# Or single-pass recording (8 seconds)
./scripts/record_voice.sh my_voice 8

# 2. List enrolled voice profiles, neural engine status, and built-in voices
python scripts/studio.py --list-voices

# 3. Produce video using your cloned voice
./scripts/run_production.sh \
  --topic "Distributed Consensus with Raft" \
  --mode technical \
  --duration 60 \
  --output-dir output/raft-video \
  --voice-profile my_voice
```

## Production Execution Workflow

When invoked, the agent executes the production pipeline directly through the command line:

```bash
# General syntax
./scripts/run_production.sh \
  --topic "<TOPIC_NAME>" \
  --mode <beginner|technical|documentary> \
  --duration <SECONDS> \
  --output-dir <OUTPUT_PATH>

# Example 1: Technical Deep Dive on API Requests (60s)
./scripts/run_production.sh \
  --topic "How an API request travels through a backend system" \
  --mode technical \
  --duration 60 \
  --output-dir output/api-journey-60s

# Example 2: Ingest a GitHub Repository (90s)
./scripts/run_production.sh \
  --repo "https://github.com/fastapi/fastapi" \
  --mode beginner \
  --duration 90 \
  --output-dir output/fastapi-explainer

# Example 3: Ingest a Research Paper PDF (120s)
./scripts/run_production.sh \
  --pdf "papers/attention.pdf" \
  --mode documentary \
  --duration 120 \
  --output-dir output/transformers-doc
```

## Production Modes

1. **`beginner` (Explainer):**
   - High-contrast visual analogies.
   - Pacing: 110–125 WPM.
   - Ideal for non-technical or introductory audiences.
2. **`technical` (Deep Dive):**
   - Architecture diagrams, packet hops, code syntax inspection, latency benchmarks.
   - Pacing: 130–145 WPM.
   - Ideal for software engineers, devops practitioners, and system architects.
3. **`documentary` (Cinematic):**
   - Atmospheric cinematic title cards, high-contrast metric visuals, reflective narration.
   - Pacing: 105–120 WPM.
   - Ideal for narrative storytelling and high-level architectural history.

## Expected Deliverables Structure

Every execution produces a clean, self-contained bundle in the target output directory:

```
<output-dir>/
├── final-video.mp4      # Broadcast-ready 1080p MP4 (H.264 / AAC 48kHz stereo)
├── narration.txt        # Scene-by-scene spoken voiceover script
├── storyboard.json      # Structured Pydantic storyboard with visual and audio specs
└── subtitles.srt        # Millisecond-accurate synchronized subtitles
```

## Quality Verification Gate

After rendering, the pipeline automatically runs `inspect_video()` using `ffprobe` to verify:
- Container validity and non-zero filesize.
- Valid H.264 video stream at 1920x1080 resolution.
- Valid stereo AAC audio stream at 48,000 Hz.
- Duration within tolerance (±1.5 seconds of target).
- Clean subtitle burn-in.

If any check fails, the pipeline logs the diagnostic error and applies deterministic fallbacks (e.g. falling back from `h264_nvenc` to `libx264`).
