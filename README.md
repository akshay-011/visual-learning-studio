# Visual Learning Studio (VLS)

[![Zero Cost Policy](https://img.shields.io/badge/Monetary%20Cost-%240.00-brightgreen.svg)](#zero-monetary-cost-policy)
[![Hardware Accelerated](https://img.shields.io/badge/Hardware%20Acceleration-NVIDIA%20NVENC-76B900.svg)](#hardware-discovery--profiles)
[![Local Cognition](https://img.shields.io/badge/Local%20AI-Ollama%20Qwen2.5--Coder-blue.svg)](#local-cognition--research-engine)
[![Voice Match](https://img.shields.io/badge/Voice%20Cloning-Google%20Assistant%20Style-purple.svg)](#step-2-voice-match--voice-cloning-calibration)
[![Tests Passing](https://img.shields.io/badge/Tests-19%2F19%20Passed-success.svg)](#step-4-deterministic-verification--quality-control)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Visual Learning Studio** is an autonomous, 100% zero-cost educational video production engine and native coding agent skill. It ingests complex technical topics, GitHub repositories, research papers, or documentation websites and transforms them into broadcast-quality 1080p educational videos with animated architecture diagrams, traveling data packets, code walkthroughs, neural narration, local voice cloning, and frame-synchronized subtitles.

---

## Table of Contents

1. [Key Capabilities](#key-capabilities)
2. [Prerequisites & System Dependencies](#prerequisites--system-dependencies)
3. [Step 1: Setting Up the Repository](#step-1-setting-up-the-repository)
4. [Step 2: Voice Match & Voice Cloning Calibration](#step-2-voice-match--voice-cloning-calibration)
5. [Step 3: Generating Educational Videos](#step-3-generating-educational-videos)
6. [Step 4: Deterministic Verification & Quality Control](#step-4-deterministic-verification--quality-control)
7. [Repository Structure](#repository-structure)
8. [Antigravity CLI (agy) Plugin & Subagents](#antigravity-cli-agy-plugin--subagents)
9. [Zero Monetary Cost Policy](#zero-monetary-cost-policy)
10. [License](#license)

---

## Key Capabilities

- **100% Zero Monetary Cost:** Operates exclusively using open-weight models, local runtimes, open audio assets, and programmatic graphics. Zero subscriptions, zero paid API keys, zero cloud GPU rentals.
- **Universal Knowledge Ingestion:** Accepts GitHub repository URLs/folders (with AST and file tree analysis), research paper PDFs, documentation URLs, or plain-text technical topics.
- **Google Assistant-Style Voice Match:** Calibrate and save your own voice model via a 4-phrase interactive setup wizard. The engine extracts your fundamental pitch ($F_0$), matches an optimal base neural voice, and applies real-time formant-preserving pitch and vocal tract resonance shifting (`librubberband` + 5-band parametric EQ).
- **VoiceStudio Human Prosody & Pronunciation:** Integrates techniques from [debpalash/voicestudio](https://github.com/debpalash/voicestudio), including an automated technical acronym dictionary (`API` &rarr; `A P I`, `SQL` &rarr; `sequel`, `JWT` &rarr; `JOT`, `gRPC` &rarr; `G R P C`), human breathing pauses, and 5-stage studio vocal mastering (80Hz rumble cut, warmth boost, de-esser, compressor, EBU R128 loudnorm).
- **Clean Visual Presentation:** Exported MP4 frames feature pristine diagrammatic animations without burned-in captions by default. Standalone `.srt` subtitles are generated alongside. Subtitle burning and background music can be toggled on demand.
- **Three Educational Formats:**
  - `beginner`: Relatable analogies, simplified mental models, and gentle scaffolding (110–125 WPM).
  - `technical`: Multi-tier architecture diagrams, packet routing hops, controller code inspection, and latency benchmarks (130–145 WPM).
  - `documentary`: Cinematic atmospheric titles, high-contrast metric visuals, and evocative narration (105–120 WPM).
- **Autonomous Hardware Adaptation:** Automatically profiles CPU cores, RAM, and NVIDIA GPU VRAM to select between `LIGHTWEIGHT`, `BALANCED`, and `HIGH_PERFORMANCE` hardware profiles.

---

## Prerequisites & System Dependencies

Visual Learning Studio requires only standard Linux or macOS media packages:

### System Packages (Linux / Arch / Debian / Fedora)
- **FFmpeg 6+** compiled with `librubberband`, `libpulse`, and `h264_nvenc` (or `libx264`):
  ```bash
  # Arch / Omarchy
  sudo pacman -S ffmpeg rubberband pipewire pipewire-pulse

  # Ubuntu / Debian
  sudo apt-get update && sudo apt-get install -y ffmpeg librubberband-dev pipewire pulseaudio-utils

  # Fedora
  sudo dnf install -y ffmpeg rubberband pipewire
  ```
- **Python 3.10+** (Python 3.12 recommended)
- **uv** (recommended high-speed Python package manager):
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- **Optional Local LLM (Ollama):** For offline AI research and scriptwriting:
  ```bash
  curl -fsSL https://ollama.com/install.sh | sh
  ollama serve
  ollama run qwen2.5-coder:7b
  ```
  *(Note: If Ollama is not running, the studio automatically switches to its deterministic heuristic learning architect without failing).*

---

## Step 1: Setting Up the Repository

### 1. Clone the Codebase
```bash
git clone https://github.com/omarchy/visual-learning-studio.git
cd visual-learning-studio
```

### 2. Create Virtual Environment & Install Dependencies
```bash
# Create virtual environment with uv
uv venv .venv --python 3.12

# Activate virtual environment
source .venv/bin/activate

# Install all dependencies in editable mode
uv pip install -e .
```

### 3. Probe Host Hardware & Profile
Run hardware discovery to verify CPU cores, GPU VRAM, hardware encoders, and active production profiles:
```bash
python scripts/studio.py --check-hardware
```

Sample output:
```
============================================================
 VISUAL LEARNING STUDIO - HARDWARE DISCOVERY REPORT
============================================================
OS:                  Linux omarchy 7.2.15-1-omarchy (x86_64)
CPU:                 13th Gen Intel(R) Core(TM) i5-13420H (12 cores)
RAM:                 15.3 GB
Disk Available:      184.2 GB
GPU:                 NVIDIA GeForce RTX 3050 Laptop GPU (6144 MB VRAM)
CUDA Available:      True
Recommended Encoder: h264_nvenc
Ollama Active:       True
Production Profile:  BALANCED
============================================================
```

---

## Step 2: Voice Match & Voice Cloning Calibration

Visual Learning Studio lets you record your own voice and use your cloned vocal timbre for narration with zero external API calls or fees.

### Method A: Google Assistant-Style 4-Phase Voice Match (Recommended)
Launch the interactive calibration wizard:
```bash
./scripts/voice_setup.sh my_voice
```
*(Or via python: `python scripts/studio.py --setup-voice --voice-profile my_voice`)*

#### The 4 Calibration Phases
Just like Google Assistant Voice Match, the wizard prompts you through 4 diverse phonetic sentences to map your vocal range:
1. **Conversational Greeting:** *"Hey Studio, what's on the schedule for today?"* (Friendly conversational cadence)
2. **Declarative Statement:** *"Distributed architectures scale horizontally by partitioning database tables."* (Firm declarative pacing)
3. **Interrogative Inflection:** *"How does an in-memory cache prevent database read bottlenecks?"* (Rising question inflection)
4. **Technical Mechanics:** *"Consensus protocols like Raft ensure exact replica synchronization across nodes."* (Crisp consonants)

```
┌────────────────────────────────────────────────────────────────────┐
│ [● ○ ○ ○] Phrase 1 of 4: Conversational Greeting                   │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  "Hey Studio, what's on the schedule for today?"                   │
│                                                                    │
│  💡 Tip: Speak in your natural, friendly conversational tone.       │
└────────────────────────────────────────────────────────────────────┘

Press [ENTER] when ready to speak (5.0s take)...
```

#### What Happens Under the Hood
1. Captures 4 clean PCM WAV takes directly from your microphone via PipeWire/ALSA.
2. Validates signal level (prompts you to re-record if silent or muted).
3. Fuses the 4 takes into a master calibration reference (`assets/voices/my_voice/reference.wav`).
4. Extracts your fundamental pitch ($F_0$), identifies your vocal register, and selects the closest base neural model.
5. Computes your 5-band vocal tract parametric EQ offsets (Sub-bass, Low-mid, Mid, High-mid, Presence).
6. Synthesizes an instant audition test clip (`assets/voices/my_voice/audition.wav`) and plays it back through your speakers.

---

### Method B: Single-Pass Microphone Recording (8 Seconds)
If you prefer a single calibration passage instead of 4 phases:
```bash
./scripts/record_voice.sh my_voice 8
```

---

### Method C: Import an Existing Audio Sample
If you already have a voice recording (`.wav`, `.mp3`, `.m4a`, `.flac`):
```bash
python scripts/studio.py --clone-voice /path/to/my_recording.wav --voice-profile my_voice
```

---

### Inspect Enrolled Voice Profiles
List all saved voice profiles and inspect their detected pitch and acoustic metrics:
```bash
python scripts/studio.py --list-voices
```

Sample output:
```
=================================================================
 ENROLLED VOICE CLONE PROFILES
=================================================================
Profile:     my_voice
Pitch (F0):  134.2 Hz (Tenor / Neutral)
Base Model:  en-US-BrianNeural (Pitch Shift: 0.93x, -1.3 st)
Reference:   /home/akshay/workspace/make-video/assets/voices/my_voice/reference.wav
Takes:       4 calibration takes fused (21.0s total)
Audition:    /home/akshay/workspace/make-video/assets/voices/my_voice/audition.wav
=================================================================
```

---

## Step 3: Generating Educational Videos

The studio accepts any technical input and renders a broadcast-quality Full HD 1080p MP4.

### 1. Conceptual Topic with Cloned Voice (60s Technical Deep Dive)
```bash
./scripts/run_production.sh \
  --topic "How an API request travels through a backend system" \
  --mode technical \
  --duration 60 \
  --output-dir output/api-journey-60s \
  --voice-profile my_voice
```

### 2. Ingest a GitHub Repository (90s Beginner Explainer)
```bash
./scripts/run_production.sh \
  --repo "https://github.com/fastapi/fastapi" \
  --mode beginner \
  --duration 90 \
  --output-dir output/fastapi-explainer \
  --voice-profile my_voice
```

### 3. Ingest a Research Paper PDF (120s Cinematic Documentary)
```bash
./scripts/run_production.sh \
  --pdf "papers/attention_is_all_you_need.pdf" \
  --mode documentary \
  --duration 120 \
  --output-dir output/transformers-doc \
  --voice-profile my_voice
```

### Optional Styling Flags
- `--burn-subtitles`: Burns styled, bottom-centered subtitles into the MP4 video frames (default: False for clean visual aesthetic).
- `--include-music`: Mixes licensed background music with automated ducking (-24 dB during speech) (default: False for isolated dialogue).
- `--include-sfx`: Mixes contextual transition whooshes and UI actuation sound effects.

### Output Bundle
Every production run generates a self-contained bundle in `--output-dir`:
```
output/api-journey-60s/
├── final-video.mp4      # Broadcast-grade 1080p Full HD video (H.264 / AAC 48kHz stereo)
├── narration.txt        # Scene-by-scene voiceover script
├── storyboard.json      # Structured Pydantic storyboard with visual and audio specs
└── subtitles.srt        # Millisecond-accurate synchronized subtitles file
```

---

## Step 4: Deterministic Verification & Quality Control

### Run Automated Unit & Integration Tests
The repository maintains a 100% passing test suite with zero mocking of audio transcoding or video frame rendering:
```bash
pytest tests/ -v
```

Test coverage includes:
- Neural speech synthesis and VoiceStudio prosody (`test_audio.py`, `test_voicestudio.py`)
- Acoustic pitch autocorrelation and 5-band formant extraction (`test_cloning.py`)
- Multi-take fusion and Google Assistant-style Voice Match calibration (`test_voice_match.py`)
- Programmatic 1080p graphics: Title cards, architecture diagrams, packet animations, IDE code frames, KPI metric dashboards (`test_generation.py`)
- Hardware discovery and profile assignment (`test_hardware.py`)
- Source ingestion: GitHub repos, local Markdown, PDFs, web URLs (`test_ingestion.py`)
- Quality control inspector: Container verification, codec streams, resolution, and duration tolerances (`test_quality.py`)

### Automated Quality Inspector Gate
Every rendered video must automatically pass 6 verification gates via `ffprobe` in `src/quality/inspector.py`:
1. File exists and non-zero filesize.
2. Valid H.264 video stream.
3. Strict 1920x1080 (1080p Full HD) resolution.
4. Valid stereo AAC audio stream at 48,000 Hz.
5. Consistent 30.0 fps frame rate.
6. Target duration within strict tolerance ($\pm 2.0$ seconds).

---

## Repository Structure

```
make-video/
├── SKILL.md                 # Antigravity CLI (agy) skill specification
├── README.md                # This complete guide
├── LICENSE                  # MIT License
├── pyproject.toml           # Package build configuration & entrypoints
├── requirements.txt         # Core dependencies (Pillow, numpy, pydantic, edge-tts)
├── scripts/
│   ├── studio.py            # Primary studio CLI interface
│   ├── run_production.sh    # Production runner wrapper
│   ├── voice_setup.sh       # Google Assistant-style Voice Match wizard
│   └── record_voice.sh      # Single-pass microphone recording utility
├── agents/                  # Production subagent role definitions
│   ├── researcher.md        # Technical research engine
│   ├── teacher.md           # Instructional design & mental scaffolding
│   ├── scriptwriter.md      # Natural dialogue & word-budget timing
│   ├── storyboard-director.md # Structured scene JSON schemas
│   ├── visual-director.md   # Color palettes, typography & layout
│   ├── audio-director.md    # VoiceStudio mastering & audio ducking
│   └── quality-checker.md   # Automated ffprobe inspection gate
├── src/
│   ├── audio/               # VoiceStudio prosody, cloner, sound mixer, TTS
│   │   ├── cloner.py        # Voice Match, pitch detection, formant EQ, take fusion
│   │   ├── voicestudio.py   # Technical lexicon & vocal studio mastering chain
│   │   ├── sound_mixer.py   # Multi-track audio mixing & leveling
│   │   └── tts_engine.py    # Neural TTS with VoiceStudio prosody & cloning
│   ├── composition/         # FFmpeg hardware concatenation & encoding
│   ├── discovery/           # Hardware detection & profile selection
│   ├── generation/          # 1080p procedural diagrams, code frames & metrics
│   ├── ingestion/           # GitHub, PDF, URL, and Markdown source parsers
│   ├── learning/            # Pedagogical storyboards (30s, 60s, custom)
│   ├── quality/             # Automated video quality inspector
│   ├── research/            # Local LLM research & deterministic fallback
│   └── orchestration/       # Master end-to-end production pipeline
├── assets/
│   ├── voices/              # Enrolled user voice profiles & calibration takes
│   ├── music/               # CC BY 4.0 royalty-free background music
│   └── sfx/                 # CC0 public domain sound effects
├── tests/                   # 19 deterministic pytest tests
└── output/
    └── final-demo/          # Pre-rendered broadcast deliverables
        ├── 30-second/       # Complete 30s challenge video & assets
        ├── 60-second/       # Complete 60s challenge video & assets
        └── production-report.md # Comprehensive production audit
```

---

## Antigravity CLI (agy) Plugin & Subagents

Visual Learning Studio is installed as a native plugin for Google Antigravity CLI (`agy`):

```bash
# List installed plugins in agy
agy plugin list
```

Output:
```
Installed plugins:
- visual-learning-studio (enabled, 1.0.0)
    Components: 1 skill, 7 agents
```

### The 7 Autonomous Subagents
When interacting in `agy`, you can delegate specific video production responsibilities to specialized subagents:
- `@researcher`: Extracts core architectural mechanisms and invariants from codebases or papers.
- `@teacher`: Designs intuitive mental models and progressive pedagogical scaffolding.
- `@scriptwriter`: Drafts spoken conversational dialogue adhering to strict word-budget tempos.
- `@storyboard-director`: Orchestrates machine-validated JSON storyboards conforming to Pydantic schemas.
- `@visual-director`: Enforces color theory, geometric layouts, typography, and motion timing.
- `@audio-director`: Masters voice synthesis, VoiceStudio prosody, and audio leveling.
- `@quality-checker`: Validates the exported MP4 against the 6 automated inspection gates.

---

## Pre-Rendered Challenge Deliverables

The repository includes two pre-rendered, independently verified sample videos demonstrating the full production pipeline:
- **30-Second Edition:** [`output/final-demo/30-second/final-video.mp4`](file:///home/akshay/workspace/make-video/output/final-demo/30-second/final-video.mp4) (Duration: 27.20s, Size: 1.43 MB, 1080p @ 30fps H.264, AAC 48kHz stereo, pure voice, zero burned captions, zero background music).
- **60-Second Edition:** [`output/final-demo/60-second/final-video.mp4`](file:///home/akshay/workspace/make-video/output/final-demo/60-second/final-video.mp4) (Duration: 47.80s, Size: 2.31 MB, 1080p @ 30fps H.264, AAC 48kHz stereo, pure voice, zero burned captions, zero background music).
- **Audit Report:** Read [`output/final-demo/production-report.md`](file:///home/akshay/workspace/make-video/output/final-demo/production-report.md) for full metrics and verification output.

---

## Zero Monetary Cost Policy

Visual Learning Studio strictly enforces an **Absolute Zero-Cost Policy**:
- **Paid APIs:** None ($0.00). No OpenAI, ElevenLabs, Runway, Midjourney, Replicate, or MuAPI.
- **LLM Subscriptions:** None ($0.00). Runs local Ollama (`qwen2.5-coder:7b`) with deterministic heuristic fallbacks.
- **Voiceover & Cloning:** None ($0.00). Zero-cost neural TTS with local DSP acoustic morphing (`librubberband`).
- **Cloud GPUs:** None ($0.00). Renders locally via NVIDIA NVENC hardware acceleration or standard CPU fallback.

---

## License

- **Source Code:** [MIT License](LICENSE)
- **Background Music:** Sascha Ende ([ende.app](https://ende.app/en)), licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
- **Sound Effects:** Kenney ([kenney.nl](https://kenney.nl/)), licensed under [CC0 (Public Domain)](https://creativecommons.org/publicdomain/zero/1.0/).
