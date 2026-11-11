# Visual Learning Studio (VLS)

[![Zero Cost Policy](https://img.shields.io/badge/Monetary%20Cost-%240.00-brightgreen.svg)](#zero-monetary-cost-policy)
[![Hardware Accelerated](https://img.shields.io/badge/Hardware%20Acceleration-NVIDIA%20NVENC-76B900.svg)](#hardware-profiles)
[![Local Cognition](https://img.shields.io/badge/Local%20AI-Ollama%20Qwen2.5--Coder-blue.svg)](#cognition-layer)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Visual Learning Studio** is an autonomous, 100% zero-cost educational video production engine and coding agent skill. It ingests complex technical topics, GitHub repositories, research papers, or documentation websites and transforms them into broadcast-quality 1080p educational videos with animated architecture diagrams, traveling data packets, code walkthroughs, neural narration, background music, sound effects, and frame-synchronized subtitles.

---

## Key Features

- **100% Zero Monetary Cost:** Operates exclusively using open-weight models, local runtimes, open audio assets, and programmatic graphics. No subscriptions, credits, or paid APIs.
- **Universal Ingestion:** Accepts GitHub repositories (with AST/architecture parsing), research paper PDFs, documentation URLs, or plain-text conceptual topics.
- **Three Educational Formats:**
  - `beginner`: Relatable real-world analogies, simplified mental models, and gentle scaffolding.
  - `technical`: Multi-tier architecture diagrams, packet routing hops, controller code inspection, and latency benchmarks.
  - `documentary`: Cinematic atmospheric titles, high-contrast metric visuals, and evocative philosophical narration.
- **Programmatic 1080p Visual Engine:** Mathematical procedural graphics rendered via Pillow + NumPy, eliminating hallucination risks and delivering sub-pixel rendering.
- **Multi-Track Audio Engineering:** Broadcast dialogue leveling (-16 LUFS), dynamic sidechain music ducking (-24 dB during speech), and sample-accurate transition SFX.
- **Autonomous Hardware Adaptation:** Automatically detects CPU cores, RAM, and NVIDIA GPU VRAM to select between `LIGHTWEIGHT`, `BALANCED`, and `HIGH_PERFORMANCE` profiles.
- **Automated Quality Control:** Deep container and stream inspection via `ffprobe` verifying codecs, frame rates, duration tolerances, and audio levels.

---

## Repository Architecture

```
visual-learning-studio/
├── SKILL.md                 # Agent skill definition for Antigravity CLI
├── README.md                # System overview and quickstart
├── LICENSE                  # MIT License
├── pyproject.toml           # Package specification & entrypoints
├── requirements.txt         # Core production dependencies
├── docs/
│   ├── architecture.md      # Pipeline topology & subsystem design
│   ├── hardware-detection.md# Hardware detection & profile matrix
│   ├── installation.md      # Setup instructions
│   ├── models.md            # Model licenses & system requirements
│   ├── open-generative-ai-evaluation.md # Deep evaluation of candidate repo
│   ├── production-guide.md  # Creative directing and format guidelines
│   ├── providers.md         # Adapter abstraction specifications
│   └── troubleshooting.md   # Diagnostic runbooks
├── agents/
│   ├── researcher.md        # Technical research directives
│   ├── teacher.md           # Instructional design & scaffolding
│   ├── scriptwriter.md      # Spoken dialogue & timing constraints
│   ├── storyboard-director.md# Scene schema & visual orchestration
│   ├── visual-director.md   # Color theory & motion principles
│   ├── audio-director.md    # Broadcast audio & sidechain standards
│   └── quality-checker.md   # Automated inspection criteria
├── src/
│   ├── discovery/           # Hardware probing & profile selection
│   ├── ingestion/           # GitHub, PDF, Web, and Topic parsers
│   ├── research/            # Local LLM analysis & heuristic fallbacks
│   ├── learning/            # Pedagogical planning & scene structuring
│   ├── storyboard/          # Pydantic schema models & JSON serialization
│   ├── generation/          # 1080p programmatic animation & video adapters
│   ├── audio/               # Neural TTS & multi-track ducking mixer
│   ├── composition/         # FFmpeg concatenation & subtitle burning
│   ├── quality/             # Automated ffprobe inspection gate
│   └── orchestration/       # Master end-to-end production pipeline
├── templates/
│   ├── beginner/            # Beginner explainer layout & pacing
│   ├── technical/           # Technical deep dive layout & pacing
│   └── documentary/         # Cinematic documentary layout & pacing
├── scripts/
│   ├── studio.py            # Main CLI interface
│   └── run_production.sh    # Bash launcher wrapper
├── tests/                   # Deterministic test suite (100% passing)
├── assets/
│   ├── music/               # CC BY 4.0 royalty-free music beds
│   └── sfx/                 # CC0 public domain sound effects
└── output/
    └── final-demo/
        ├── 30-second/       # Complete 30s challenge video & assets
        ├── 60-second/       # Complete 60s challenge video & assets
        └── production-report.md # Production & verification report
```

---

## Quickstart

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/omarchy/visual-learning-studio.git
cd visual-learning-studio

# Setup virtual environment with uv
uv venv .venv --python 3.12
source .venv/bin/activate
uv pip install -e .
```

### 2. Verify Hardware Discovery

```bash
python scripts/studio.py --check-hardware
```

### 3. Generate an Educational Video

```bash
# Generate a 60-second technical deep dive on API requests
./scripts/run_production.sh \
  --topic "How an API request travels through a backend system" \
  --mode technical \
  --duration 60 \
  --output-dir output/api_request_demo
```

### 4. Run Test Suite

```bash
pytest tests/
```

---

## Evaluated Deliverables

The repository includes two independently produced, broadcast-verified sample videos:
1. **30-Second Edition:** `output/final-demo/30-second/final-video.mp4` (Duration: 25.62s, Size: 1.57 MB)
2. **60-Second Edition:** `output/final-demo/60-second/final-video.mp4` (Duration: 47.78s, Size: 3.00 MB)
3. **Comprehensive Audit:** Read `output/final-demo/production-report.md`.

---

## License

- Code: [MIT License](LICENSE)
- Background Music: Sascha Ende ([ende.app](https://ende.app/en)), licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
- Sound Effects: Kenney ([kenney.nl](https://kenney.nl/)), licensed under [CC0 (Public Domain)](https://creativecommons.org/publicdomain/zero/1.0/).
