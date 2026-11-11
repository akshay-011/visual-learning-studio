# Video Production Guide

Visual Learning Studio enables creators and autonomous agents to produce educational videos across three distinct formats.

## Production Modes

### 1. Beginner Explainer (`--mode beginner`)
- **Pacing:** Moderate (110–125 words per minute).
- **Structure:** 
  1. Hook with real-world analogy.
  2. Simplification of core problem.
  3. Interactive mental model diagram.
  4. Real-world example.
  5. Actionable summary.
- **Visual Style:** Warm, high-contrast, rounded nodes, large readable typography, animated particle metaphors.

### 2. Technical Deep Dive (`--mode technical`)
- **Pacing:** Focused, information-dense (130–145 words per minute).
- **Structure:**
  1. High-level architecture topology.
  2. End-to-end request packet routing.
  3. Core code implementation walkthrough.
  4. Internal data structure & algorithm deep dive (e.g. B-Trees, Raft consensus, Ring buffers).
  5. Performance bottlenecks & trade-offs.
- **Visual Style:** Dark-mode terminal theme, glowing cybernetic connection bus, syntax-highlighted code with animated spotlight, packet flow counters.

### 3. Cinematic Documentary (`--mode documentary`)
- **Pacing:** Measured, dramatic (105–120 words per minute).
- **Structure:**
  1. Dramatic hook ("What happens in the 50 milliseconds after you press Enter?").
  2. The immense invisible engineering challenge.
  3. Component revelation across distributed nodes.
  4. The journey of the packet through undersea cables and cloud gateways.
  5. Poetic, awe-inspiring conclusion.
- **Visual Style:** Cinematic 2.39:1 letterbox overlays, ambient soundscapes, deep atmospheric color gradients, subtle camera pan/zoom dynamics.

## Command-Line Usage

```bash
# Generate video from a technical topic
python scripts/studio.py \
  --topic "How an API request travels through a backend system" \
  --mode technical \
  --duration 60 \
  --output output/api_request_deep_dive.mp4

# Generate video from a local or remote GitHub repository
python scripts/studio.py \
  --repo "https://github.com/fastapi/fastapi" \
  --mode beginner \
  --duration 90 \
  --output output/fastapi_explainer.mp4

# Generate video from a PDF research paper
python scripts/studio.py \
  --pdf "papers/attention_is_all_you_need.pdf" \
  --mode documentary \
  --duration 120 \
  --output output/transformers_documentary.mp4
```
