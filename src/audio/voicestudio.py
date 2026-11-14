"""VoiceStudio Integration: Human-like speech processing, lexicon respelling, and vocal studio mastering.

Inspired by VoiceStudio (https://github.com/debpalash/voicestudio):
- Expressive SSML-Lite prosody parser
- Technical pronunciation lexicon for natural human cadence
- Studio mastering chain (warmth EQ, de-essing, dynamic leveling)
"""

import re
from typing import Dict, List, Optional, Tuple

# Technical pronunciation dictionary to eliminate robotic mispronunciations
DEFAULT_TECHNICAL_LEXICON: Dict[str, str] = {
    "API": "A P I",
    "APIs": "A P I's",
    "TLS": "T L S",
    "TLS 1.3": "T L S 1.3",
    "JWT": "JOT",
    "JWTs": "JOTs",
    "SQL": "sequel",
    "NoSQL": "no sequel",
    "PostgreSQL": "Postgres Q L",
    "Redis": "Red-iss",
    "HTTP": "H T T P",
    "HTTPS": "H T T P S",
    "DNS": "D N S",
    "gRPC": "G R P C",
    "RPC": "R P C",
    "OAuth": "Oh-auth",
    "OAuth2": "Oh-auth 2",
    "JSON": "JAY-son",
    "REST": "rest",
    "RESTful": "rest-ful",
    "UUID": "U U I D",
    "URI": "U R I",
    "URL": "U R L",
    "IP": "I P",
    "TCP": "T C P",
    "UDP": "U D P",
    "CLI": "C L I",
    "SSH": "S S H",
    "SSL": "S S L",
    "RAM": "ram",
    "CPU": "C P U",
    "GPU": "G P U",
    "NVMe": "N V M E",
    "SSD": "S S D",
    "SDK": "S D K",
    "SDKs": "S D K's",
    "CI/CD": "C I C D",
    "POSIX": "paw-zix",
    "SaaS": "sass",
    "microsecond": "micro-second",
    "microseconds": "micro-seconds",
    "sub-millisecond": "sub millisecond",
    "sub-second": "sub second",
    "RTT": "round trip time",
    "ms": "milliseconds",
    "12ms": "12 milliseconds",
    "18ms": "18 milliseconds",
    "3ms": "3 milliseconds",
    "4ms": "4 milliseconds",
    "42ms": "42 milliseconds",
    "45ms": "45 milliseconds",
    "34ms": "34 milliseconds",
    "50ms": "50 milliseconds",
}


def apply_pronunciation_lexicon(text: str, lexicon: Optional[Dict[str, str]] = None) -> str:
    """Applies whole-word, longest-first pronunciation replacements."""
    lex = lexicon or DEFAULT_TECHNICAL_LEXICON
    if not text or not lex:
        return text

    # Sort keys longest-first to prevent partial collisions (e.g. "TLS 1.3" before "TLS")
    sorted_keys = sorted(lex.keys(), key=len, reverse=True)
    pattern = re.compile(
        r"\b(" + "|".join(re.escape(k) for k in sorted_keys) + r")\b",
        re.IGNORECASE,
    )

    # Key lookup map ignoring case
    key_map = {k.lower(): v for k, v in lex.items()}

    def replace_fn(match: re.Match) -> str:
        word = match.group(0).lower()
        return key_map.get(word, match.group(0))

    return pattern.sub(replace_fn, text)


def process_human_cadence(text: str) -> str:
    """Processes inline emotion, pauses, and cadence tags into natural conversational phrasing.

    Replaces:
    - [pause Nms] -> natural breath pause (punctuation ellipsis)
    - [slow]...[/slow] -> natural phrasing
    - [emphasis]...[/emphasis] -> natural stress
    - Inserts respiratory breath pauses at long clause conjunctions to eliminate robotic run-on delivery.
    """
    if not text:
        return ""

    processed = text

    # 1. Resolve pause markers: [pause 300ms] -> natural conversational breath
    processed = re.sub(r"\[pause\s*(\d+)ms\]", r"... ", processed, flags=re.IGNORECASE)

    # 2. Strip prosody tags while preserving natural text
    processed = re.sub(r"\[/?(slow|fast|emphasis|spell|excited|whispers)\]", "", processed, flags=re.IGNORECASE)

    # 3. Apply technical pronunciation lexicon
    processed = apply_pronunciation_lexicon(processed)

    # 4. Human respiratory phrasing: inject micro-cadence pause before conjunctions
    # in long clauses (>= 4 words) if punctuation is not already present
    conjunction_pattern = re.compile(
        r"(\b\w+\b(?:\s+\b\w+\b){3,})\s+(because|although|whereas|meaning that|rather than)\b",
        re.IGNORECASE,
    )
    processed = conjunction_pattern.sub(r"\1, \2", processed)

    # 5. Clean up redundant punctuation and normalize whitespace
    processed = re.sub(r",\s*,+", ",", processed)
    processed = re.sub(r"\s+([,.:;?!])", r"\1", processed)
    processed = re.sub(r"\s+", " ", processed).strip()

    return processed


def get_vocal_studio_filter() -> str:
    """VoiceStudio mastering chain:
    - 80 Hz high-pass (removes subsonic rumble and plosives)
    - 180 Hz proximity warmth (+2.2 dB, chest resonance emulation)
    - 3200 Hz vocal presence (+1.0 dB, clarity and articulation)
    - 6800 Hz de-esser (-2.5 dB, removes digital sibilance sizzle)
    - Broadcast dynamic compression (2.6:1 optical leveling emulation)
    - Analog harmonic saturation (soft tanh clipping for analog warmth)
    - Broadcast loudness normalization (EBU R128 -16 LUFS, TruePeak -1.5 dB)
    """
    return (
        "highpass=f=80,"
        "equalizer=f=180:t=q:w=1.2:g=2.2,"
        "equalizer=f=3200:t=q:w=1.5:g=1.0,"
        "equalizer=f=6800:t=q:w=2.2:g=-2.5,"
        "acompressor=threshold=-18dB:ratio=2.6:attack=25:release=180,"
        "asoftclip=type=tanh,"
        "loudnorm=I=-16:TP=-1.5:LRA=9"
    )
