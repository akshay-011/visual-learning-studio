"""Voice Recording, Enrollment, and Voice Cloning Engine.

Enables local users to record their voice via system microphone or import an existing
audio reference, extract acoustic signatures (fundamental pitch F0, vocal tract
formant distribution, and dynamic profile), and synthesize narration matching their
cloned vocal timbre at zero monetary cost.
"""

from __future__ import annotations

import json
import logging
import math
import shutil
import subprocess
import time
import wave
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from pydantic import BaseModel, Field

from src.audio.voicestudio import get_vocal_studio_filter

logger = logging.getLogger("visual_studio.cloner")

DEFAULT_PROMPT_SENTENCE = (
    "Distributed architectures achieve resilient state consistency through "
    "asynchronous replication, cryptographic handshakes, and in-memory caching."
)

# Reference baseline frequencies and matching base neural models
BASE_VOICE_REGISTERS = [
    # (max_f0, voice_name, typical_f0, register_label)
    (135.0, "en-US-AndrewNeural", 118.0, "Baritone / Bass"),
    (175.0, "en-US-BrianNeural", 145.0, "Tenor / Neutral"),
    (225.0, "en-US-AvaNeural", 195.0, "Alto / Contralto"),
    (9999.0, "en-US-JennyNeural", 235.0, "Soprano / Mezzo"),
]

# Standard reference spectral energy percentages for neutral vocal
TARGET_BAND_PERCENTAGES = {
    "sub_bass": 48.0,   # 80 - 250 Hz
    "low_mid": 30.0,    # 250 - 800 Hz
    "mid": 12.0,        # 800 - 2500 Hz
    "high_mid": 7.0,    # 2500 - 5000 Hz
    "presence": 3.0,    # 5000 - 12000 Hz
}

# Google Assistant-style 4-stage Voice Match calibration prompts
VOICE_MATCH_PROMPTS = [
    {
        "id": 1,
        "title": "Conversational Greeting",
        "text": "Hey Studio, what's on the schedule for today?",
        "tip": "Speak in your natural, friendly conversational tone.",
        "duration": 5.0,
    },
    {
        "id": 2,
        "title": "Declarative Architecture",
        "text": "Distributed architectures scale horizontally by partitioning database tables.",
        "tip": "Speak with clear declarative confidence and firm pacing.",
        "duration": 5.5,
    },
    {
        "id": 3,
        "title": "Interrogative Inflection",
        "text": "How does an in-memory cache prevent database read bottlenecks?",
        "tip": "Speak naturally with a slight rising inflection at the end of the question.",
        "duration": 5.0,
    },
    {
        "id": 4,
        "title": "Technical Mechanics",
        "text": "Consensus protocols like Raft ensure exact replica synchronization across nodes.",
        "tip": "Speak with crisp consonants and articulate pronunciation.",
        "duration": 5.5,
    },
]


class VoiceProfile(BaseModel):
    """Enrolled acoustic profile of a user or cloned speaker."""

    profile_name: str
    reference_audio: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    duration_seconds: float
    f0_mean_hz: float
    f0_median_hz: float
    f0_std_hz: float
    f0_log_mean: float = 4.80
    f0_log_std: float = 0.25
    vocal_register: str
    base_voice: str
    base_f0_hz: float
    pitch_ratio: float
    pitch_semitones: float
    eq_gains: Dict[str, float]
    speech_rms: float
    formants: List[float] = Field(default_factory=list)
    spectral_signature_path: Optional[str] = None
    speaker_embedding_path: Optional[str] = None
    takes: List[str] = Field(default_factory=list)
    audition_audio: Optional[str] = None
    is_valid: bool = True


def record_voice_clip(
    output_wav: Path,
    duration_seconds: float = 8.0,
    device: str = "default",
) -> Path:
    """Records audio from system microphone using PulseAudio/PipeWire or ALSA."""
    output_wav.parent.mkdir(parents=True, exist_ok=True)
    temp_raw = output_wav.with_suffix(".raw.wav")

    # Attempt 1: FFmpeg with PulseAudio/PipeWire default source
    cmd_pulse = [
        "ffmpeg",
        "-y",
        "-f", "pulse",
        "-i", device,
        "-t", str(duration_seconds),
        "-ar", "48000",
        "-ac", "2",
        "-c:a", "pcm_s16le",
        str(temp_raw),
    ]

    try:
        subprocess.run(cmd_pulse, capture_output=True, check=True)
    except Exception as e1:
        logger.warning(f"Pulse capture failed ({e1}), falling back to ALSA...")
        # Attempt 2: FFmpeg with ALSA
        cmd_alsa = [
            "ffmpeg",
            "-y",
            "-f", "alsa",
            "-i", "default",
            "-t", str(duration_seconds),
            "-ar", "48000",
            "-ac", "2",
            "-c:a", "pcm_s16le",
            str(temp_raw),
        ]
        try:
            subprocess.run(cmd_alsa, capture_output=True, check=True)
        except Exception as e2:
            # Attempt 3: pw-record
            cmd_pw = [
                "pw-record",
                "--rate", "48000",
                "--channels", "2",
                str(temp_raw),
            ]
            try:
                proc = subprocess.Popen(cmd_pw)
                time.sleep(duration_seconds)
                proc.terminate()
                proc.wait(timeout=2.0)
            except Exception as e3:
                raise RuntimeError(
                    f"Microphone recording failed across all interfaces (Pulse, ALSA, PipeWire): {e1} | {e2} | {e3}"
                )

    if not temp_raw.exists() or temp_raw.stat().st_size < 1000:
        raise RuntimeError("Recorded audio file is empty or capture failed.")

    # Clean and calibrate the recorded raw audio
    clean_voice_sample(temp_raw, output_wav)
    if temp_raw.exists():
        temp_raw.unlink()

    return output_wav


def clean_voice_sample(raw_wav: Path, clean_wav: Path) -> Path:
    """Cleans recorded voice sample: cuts rumble, gates silence, and normalizes."""
    clean_wav.parent.mkdir(parents=True, exist_ok=True)
    filter_chain = (
        "highpass=f=80,"
        "silenceremove=start_periods=1:start_duration=0.08:start_threshold=-45dB:"
        "stop_periods=1:stop_duration=0.3:stop_threshold=-45dB,"
        "loudnorm=I=-16:TP=-1.5:LRA=9"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(raw_wav),
        "-af", filter_chain,
        "-ar", "48000",
        "-ac", "2",
        "-c:a", "pcm_s16le",
        str(clean_wav),
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return clean_wav


def analyze_voice_acoustics(wav_path: Path) -> Dict[str, Any]:
    """Extracts fundamental pitch F0 and 5-band spectral formant distribution."""
    if not wav_path.exists():
        raise FileNotFoundError(f"Audio file not found: {wav_path}")

    with wave.open(str(wav_path), "rb") as wf:
        sample_rate = wf.getframerate()
        n_channels = wf.getnchannels()
        n_frames = wf.getnframes()
        raw_bytes = wf.readframes(n_frames)

    audio = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    if n_channels > 1:
        audio = audio.reshape(-1, n_channels).mean(axis=1)

    duration = float(len(audio) / sample_rate)
    speech_rms = float(np.sqrt(np.mean(audio**2)))

    # 1. Pitch Extraction via Short-Time Autocorrelation
    frame_len = int(sample_rate * 0.035)  # 35ms window
    hop_len = int(sample_rate * 0.010)    # 10ms hop
    min_lag = int(sample_rate / 400.0)    # 400 Hz upper pitch limit
    max_lag = int(sample_rate / 65.0)     # 65 Hz lower pitch limit

    pitches = []
    for start in range(0, len(audio) - frame_len, hop_len):
        frame = audio[start : start + frame_len]
        frame_rms = np.sqrt(np.mean(frame**2))
        if frame_rms < 0.015:  # Ignore background silence/breaths
            continue

        w_frame = frame * np.hamming(len(frame))
        corr = np.correlate(w_frame, w_frame, mode="full")
        corr = corr[len(corr) // 2 :]

        if len(corr) < max_lag:
            continue

        peak_lag = min_lag + int(np.argmax(corr[min_lag:max_lag]))
        # Harmonic quality threshold
        if corr[0] > 0 and (corr[peak_lag] / corr[0]) > 0.28:
            pitch = sample_rate / float(peak_lag)
            if 65.0 <= pitch <= 400.0:
                pitches.append(pitch)

    if pitches:
        f0_mean = float(np.mean(pitches))
        f0_median = float(np.median(pitches))
        f0_std = float(np.std(pitches))
    else:
        # Fallback to neutral default pitch if audio was unvoiced/whispered
        f0_mean = 135.0
        f0_median = 135.0
        f0_std = 25.0

    # 2. Spectral Band Energy & Formant Analysis
    fft_vals = np.abs(np.fft.rfft(audio))
    freqs = np.fft.rfftfreq(len(audio), 1.0 / sample_rate)

    bands = {
        "sub_bass": (80.0, 250.0),
        "low_mid": (250.0, 800.0),
        "mid": (800.0, 2500.0),
        "high_mid": (2500.0, 5000.0),
        "presence": (5000.0, 12000.0),
    }

    raw_energies = {}
    for name, (low, high) in bands.items():
        idx = (freqs >= low) & (freqs < high)
        raw_energies[name] = float(np.mean(fft_vals[idx])) if np.any(idx) else 0.0

    total_energy = sum(raw_energies.values()) or 1.0
    measured_pct = {k: (v / total_energy) * 100.0 for k, v in raw_energies.items()}

    # Compute 5-band EQ offsets relative to standard target vocal curve
    eq_gains = {}
    for band_name, target_pct in TARGET_BAND_PERCENTAGES.items():
        diff_pct = measured_pct.get(band_name, target_pct) - target_pct
        # 10% deviation roughly corresponds to ~1.5 dB EQ offset, clamped to [-4.5, +4.5] dB
        gain_db = round(float(np.clip(diff_pct * 0.15, -4.5, 4.5)), 2)
        eq_gains[band_name] = gain_db

    # 3. Base Neural Voice Matching
    selected_voice = "en-US-AndrewNeural"
    base_f0 = 118.0
    vocal_register = "Baritone / Bass"

    for max_f0, voice_name, ref_f0, reg_label in BASE_VOICE_REGISTERS:
        if f0_median < max_f0:
            selected_voice = voice_name
            base_f0 = ref_f0
            vocal_register = reg_label
            break

    # Calculate required pitch shifting factor
    pitch_ratio = round(float(f0_median / base_f0), 4)
    # Clamp pitch ratio to prevent synthetic distortion
    pitch_ratio = float(np.clip(pitch_ratio, 0.72, 1.38))
    pitch_semitones = round(12.0 * math.log2(pitch_ratio), 2)

    return {
        "duration_seconds": round(duration, 2),
        "speech_rms": round(speech_rms, 4),
        "f0_mean_hz": round(f0_mean, 1),
        "f0_median_hz": round(f0_median, 1),
        "f0_std_hz": round(f0_std, 1),
        "vocal_register": vocal_register,
        "base_voice": selected_voice,
        "base_f0_hz": base_f0,
        "pitch_ratio": pitch_ratio,
        "pitch_semitones": pitch_semitones,
        "eq_gains": eq_gains,
    }


def extract_world_acoustic_profile(wav_path: Path) -> Dict[str, Any]:
    """Extracts continuous log-F0 statistics, vocal tract spectral envelope, and formants using WORLD vocoder."""
    import soundfile as sf
    import pyworld as pw
    import scipy.signal
    import scipy.linalg

    x, fs = sf.read(str(wav_path))
    if x.ndim > 1:
        x = x.mean(axis=1)
    x = x.astype(np.float64)

    # 1. Pitch & Formant Analysis using WORLD vocoder
    _f0, t_f0 = pw.dio(x, fs)
    f0 = pw.stonemask(x, _f0, t_f0, fs)
    sp = pw.cheaptrick(x, f0, t_f0, fs)
    ap = pw.d4c(x, f0, t_f0, fs)

    voiced = f0 > 40.0
    if np.any(voiced):
        f0_voiced = f0[voiced]
        f0_mean = float(np.mean(f0_voiced))
        f0_median = float(np.median(f0_voiced))
        f0_std = float(np.std(f0_voiced))
        f0_log_mean = float(np.mean(np.log(f0_voiced)))
        f0_log_std = float(np.std(np.log(f0_voiced)))
        mean_sp = np.mean(sp[voiced], axis=0)
        mean_ap = np.mean(ap[voiced], axis=0)
    else:
        f0_mean = 130.0
        f0_median = 130.0
        f0_std = 25.0
        f0_log_mean = float(np.log(130.0))
        f0_log_std = 0.20
        mean_sp = np.mean(sp, axis=0) if len(sp) > 0 else np.ones(1025)
        mean_ap = np.mean(ap, axis=0) if len(ap) > 0 else np.ones(1025) * 0.5

    # 2. Extract 4 Primary Formants via 18th-order LPC analysis
    formants = []
    try:
        order = 18
        win_size = min(len(x), int(fs * 0.04))
        center = len(x) // 2
        seg = x[max(0, center - win_size // 2) : min(len(x), center + win_size // 2)]
        if len(seg) > order:
            w_seg = seg * np.hamming(len(seg))
            r = np.correlate(w_seg, w_seg, mode="full")
            r = r[len(r) // 2 : len(r) // 2 + order + 1]
            if r[0] > 1e-6:
                a = scipy.linalg.solve_toeplitz((r[:-1], r[:-1]), r[1:])
                lpc_poly = np.concatenate(([1.0], -a))
                roots = np.roots(lpc_poly)
                valid_roots = [
                    rt for rt in roots if np.imag(rt) > 0.01 and 0.70 < np.abs(rt) < 1.05
                ]
                extracted = sorted([np.angle(rt) * (fs / (2.0 * np.pi)) for rt in valid_roots])
                formants = [round(float(f), 1) for f in extracted if 250.0 <= f <= 4500.0][:4]
    except Exception as e:
        logger.warning(f"LPC formant extraction error: {e}")

    if not formants:
        formants = [650.0, 1200.0, 2500.0, 3600.0]

    return {
        "f0_mean_hz": round(f0_mean, 1),
        "f0_median_hz": round(f0_median, 1),
        "f0_std_hz": round(f0_std, 1),
        "f0_log_mean": round(f0_log_mean, 4),
        "f0_log_std": round(f0_log_std, 4),
        "formants": formants,
        "mean_sp": mean_sp,
        "mean_ap": mean_ap,
    }


def enroll_voice(
    reference_path: Path,
    profile_name: str = "my_voice",
    voices_dir: Optional[Path] = None,
) -> VoiceProfile:
    """Enrolls an audio reference into a persistent VoiceProfile with WORLD vocoder signatures."""
    if not reference_path.exists():
        raise FileNotFoundError(f"Reference voice audio not found: {reference_path}")

    if voices_dir is None:
        voices_dir = Path(__file__).resolve().parent.parent.parent / "assets" / "voices"

    profile_dir = voices_dir / profile_name
    profile_dir.mkdir(parents=True, exist_ok=True)

    dest_ref = profile_dir / "reference.wav"
    clean_voice_sample(reference_path, dest_ref)

    acoustics = analyze_voice_acoustics(dest_ref)
    world_data = extract_world_acoustic_profile(dest_ref)

    sig_file = profile_dir / "spectral_signature.npz"
    np.savez_compressed(
        str(sig_file),
        mean_sp=world_data["mean_sp"],
        mean_ap=world_data["mean_ap"],
    )

    # Extract & cache deep neural speaker embedding
    speaker_emb_path = None
    try:
        from src.audio.neural_cloner import get_neural_converter
        converter = get_neural_converter()
        se_file = profile_dir / "speaker_embedding.pt"
        converter.extract_speaker_embedding(dest_ref, cache_path=se_file)
        speaker_emb_path = str(se_file.resolve())
    except Exception as e_neural:
        logger.warning(f"Neural speaker embedding extraction failed; WORLD fallback preserved: {e_neural}")

    profile = VoiceProfile(
        profile_name=profile_name,
        reference_audio=str(dest_ref.resolve()),
        duration_seconds=acoustics["duration_seconds"],
        f0_mean_hz=acoustics["f0_mean_hz"],
        f0_median_hz=acoustics["f0_median_hz"],
        f0_std_hz=acoustics["f0_std_hz"],
        f0_log_mean=world_data["f0_log_mean"],
        f0_log_std=world_data["f0_log_std"],
        formants=world_data["formants"],
        spectral_signature_path=str(sig_file.resolve()),
        speaker_embedding_path=speaker_emb_path,
        vocal_register=acoustics["vocal_register"],
        base_voice=acoustics["base_voice"],
        base_f0_hz=acoustics["base_f0_hz"],
        pitch_ratio=acoustics["pitch_ratio"],
        pitch_semitones=acoustics["pitch_semitones"],
        eq_gains=acoustics["eq_gains"],
        speech_rms=acoustics["speech_rms"],
        is_valid=True,
    )

    profile_json = profile_dir / "profile.json"
    with open(profile_json, "w", encoding="utf-8") as f:
        f.write(profile.model_dump_json(indent=2))

    logger.info(
        f"Enrolled voice profile '{profile_name}': F0={profile.f0_median_hz}Hz, "
        f"Base={profile.base_voice}, PitchRatio={profile.pitch_ratio}"
    )
    return profile


def load_voice_profile(
    name_or_path: str,
    voices_dir: Optional[Path] = None,
) -> VoiceProfile:
    """Loads an enrolled VoiceProfile by name, directory path, or audio file."""
    if voices_dir is None:
        voices_dir = Path(__file__).resolve().parent.parent.parent / "assets" / "voices"

    target_path = Path(name_or_path)

    # 1. Direct path to profile.json
    if target_path.is_file() and target_path.suffix == ".json":
        with open(target_path, "r", encoding="utf-8") as f:
            return VoiceProfile.model_validate_json(f.read())

    # 2. Named profile directory
    named_json = voices_dir / name_or_path / "profile.json"
    if named_json.exists():
        with open(named_json, "r", encoding="utf-8") as f:
            return VoiceProfile.model_validate_json(f.read())

    # 3. Direct audio file passed (e.g. sample.wav) -> Enroll on the fly
    if target_path.is_file() and target_path.suffix.lower() in [".wav", ".mp3", ".m4a", ".ogg", ".flac"]:
        stem_name = target_path.stem.replace(" ", "_").lower()
        return enroll_voice(target_path, profile_name=stem_name, voices_dir=voices_dir)

    raise FileNotFoundError(
        f"Voice profile '{name_or_path}' not found. Searched: {named_json} and {target_path}"
    )


def list_voice_profiles(voices_dir: Optional[Path] = None) -> List[VoiceProfile]:
    """Lists all enrolled voice profiles found in assets/voices."""
    if voices_dir is None:
        voices_dir = Path(__file__).resolve().parent.parent.parent / "assets" / "voices"

    if not voices_dir.exists():
        return []

    profiles = []
    for json_file in sorted(voices_dir.glob("*/profile.json")):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                profiles.append(VoiceProfile.model_validate_json(f.read()))
        except Exception as e:
            logger.warning(f"Failed to read profile at {json_file}: {e}")
    return profiles


def get_voice_clone_filter(profile: VoiceProfile) -> str:
    """Constructs the real-time DSP filter chain transforming base TTS to the cloned voice."""
    eq = profile.eq_gains
    filters = [
        # Formant-preserving pitch shifting via librubberband
        f"rubberband=pitch={profile.pitch_ratio:.4f}:pitchq=quality:formant=preserved",
        # 5-band vocal tract parametric resonance EQ
        f"equalizer=f=120:t=q:w=1.2:g={eq.get('sub_bass', 0.0):.2f}",
        f"equalizer=f=350:t=q:w=1.2:g={eq.get('low_mid', 0.0):.2f}",
        f"equalizer=f=1500:t=q:w=1.5:g={eq.get('mid', 0.0):.2f}",
        f"equalizer=f=3800:t=q:w=1.5:g={eq.get('high_mid', 0.0):.2f}",
        f"equalizer=f=8000:t=q:w=1.5:g={eq.get('presence', 0.0):.2f}",
        # Broadcast vocal studio mastering (highpass, de-esser, compressor, loudnorm)
        get_vocal_studio_filter(),
    ]
    return ",".join(filters)


def morph_voice_world(
    base_wav: Path,
    target_profile: VoiceProfile,
    output_wav: Path,
) -> Path:
    """Acoustically morphs base TTS audio to target voice profile using WORLD vocoder.

    Pipeline:
    1. Continuous Log-F0 Dynamic Gaussian Mapping (transfers pitch register + intonation dynamics)
    2. 1025-Bin Smoothed Vocal Tract Spectral Envelope Transfer
    3. Aperiodicity (breathiness/roughness) spectral blending
    4. WORLD vocoder resynthesis
    5. Broadcast vocal mastering (highpass, de-esser, transparent compression, loudness normalization)
    """
    output_wav.parent.mkdir(parents=True, exist_ok=True)
    temp_synth = output_wav.with_suffix(".world_synth.wav")

    try:
        import soundfile as sf
        import pyworld as pw

        x_base, fs = sf.read(str(base_wav))
        if x_base.ndim > 1:
            x_base = x_base.mean(axis=1)
        x_base = x_base.astype(np.float64)

        if len(x_base) < int(fs * 0.1):
            logger.warning("Audio too short for WORLD morphing; bypassing")
            shutil.copyfile(base_wav, output_wav)
            return output_wav

        # 1. WORLD Decomposition of Base Synthesis
        _f0, t_f0 = pw.dio(x_base, fs)
        f0_base = pw.stonemask(x_base, _f0, t_f0, fs)
        sp_base = pw.cheaptrick(x_base, f0_base, t_f0, fs)
        ap_base = pw.d4c(x_base, f0_base, t_f0, fs)

        # 2. Continuous Log-F0 Dynamic Gaussian Mapping
        voiced = f0_base > 40.0
        f0_morph = np.zeros_like(f0_base)

        if np.any(voiced):
            log_f0_base = np.log(f0_base[voiced])
            mu_base = float(np.mean(log_f0_base))
            std_base = max(float(np.std(log_f0_base)), 0.05)

            mu_target = (
                float(target_profile.f0_log_mean)
                if target_profile.f0_log_mean
                else math.log(max(target_profile.f0_median_hz, 60.0))
            )
            std_target = (
                float(target_profile.f0_log_std)
                if target_profile.f0_log_std
                else 0.20
            )
            std_target = max(std_target, 0.05)

            # Expressive variance scaling clamped to avoid robotic flatness or hyper-inflection
            scale = float(np.clip(std_target / std_base, 0.60, 1.40))
            log_f0_morph = mu_target + scale * (log_f0_base - mu_base)
            f0_morph[voiced] = np.clip(np.exp(log_f0_morph), 50.0, 480.0)
        else:
            f0_morph = np.copy(f0_base)

        # 3. 1025-Bin Smoothed Vocal Tract Spectral Envelope Transfer
        mean_sp_target = None
        mean_ap_target = None

        sig_path = getattr(target_profile, "spectral_signature_path", None)
        if sig_path and Path(sig_path).exists():
            try:
                sig_data = np.load(sig_path)
                mean_sp_target = sig_data["mean_sp"]
                if "mean_ap" in sig_data:
                    mean_ap_target = sig_data["mean_ap"]
            except Exception as e:
                logger.warning(f"Failed to load spectral signature from {sig_path}: {e}")

        if mean_sp_target is None and target_profile.reference_audio and Path(target_profile.reference_audio).exists():
            try:
                ref_profile = extract_world_acoustic_profile(Path(target_profile.reference_audio))
                mean_sp_target = ref_profile["mean_sp"]
                mean_ap_target = ref_profile["mean_ap"]
            except Exception as e:
                logger.warning(f"Failed to extract profile from reference: {e}")

        sp_morph = np.copy(sp_base)
        num_bins = sp_base.shape[1]

        if mean_sp_target is not None:
            if len(mean_sp_target) != num_bins:
                x_old = np.linspace(0, 1, len(mean_sp_target))
                x_new = np.linspace(0, 1, num_bins)
                mean_sp_target = np.interp(x_new, x_old, mean_sp_target)

            if np.any(voiced):
                mean_sp_base = np.mean(sp_base[voiced], axis=0)
            else:
                mean_sp_base = np.mean(sp_base, axis=0)

            eps = 1e-7
            ratio = (mean_sp_target + eps) / (mean_sp_base + eps)

            # Frequency smoothing filter across 25 frequency bins (~580 Hz)
            k_size = 25
            kernel = np.ones(k_size) / float(k_size)
            ratio_smooth = np.convolve(ratio, kernel, mode="same")

            med_ratio = float(np.median(ratio_smooth))
            if med_ratio > 0:
                ratio_smooth = ratio_smooth / med_ratio

            ratio_clamped = np.clip(ratio_smooth, 0.20, 4.00)
            alpha = 0.85
            transfer_curve = np.power(ratio_clamped, alpha)
            sp_morph = sp_base * transfer_curve[np.newaxis, :]

        # 4. Aperiodicity Blending
        ap_morph = np.copy(ap_base)
        if mean_ap_target is not None:
            if len(mean_ap_target) != num_bins:
                x_old = np.linspace(0, 1, len(mean_ap_target))
                x_new = np.linspace(0, 1, num_bins)
                mean_ap_target = np.interp(x_new, x_old, mean_ap_target)
            beta = 0.25
            ap_morph = np.clip((1.0 - beta) * ap_base + beta * mean_ap_target[np.newaxis, :], 0.0, 1.0)

        # 5. WORLD Synthesis
        y_synth = pw.synthesize(f0_morph, sp_morph, ap_morph, fs)
        max_amp = float(np.max(np.abs(y_synth)))
        if max_amp > 1e-4:
            y_synth = (y_synth / max_amp) * 0.92

        sf.write(str(temp_synth), y_synth, fs, subtype="PCM_16")

        # 6. Broadcast Vocal Studio Mastering (Highpass 80Hz, De-esser, Compression, Loudnorm)
        cmd_master = [
            "ffmpeg",
            "-y",
            "-i", str(temp_synth),
            "-af", get_vocal_studio_filter(),
            "-ar", "48000",
            "-ac", "2",
            "-c:a", "pcm_s16le",
            str(output_wav),
        ]
        subprocess.run(cmd_master, capture_output=True, check=True)

    except Exception as e:
        logger.warning(
            f"WORLD vocoder morphing encountered error ({e}); falling back to DSP filter chain"
        )
        filter_str = get_voice_clone_filter(target_profile)
        cmd_fallback = [
            "ffmpeg",
            "-y",
            "-i", str(base_wav),
            "-af", filter_str,
            "-ar", "48000",
            "-ac", "2",
            "-c:a", "pcm_s16le",
            str(output_wav),
        ]
        subprocess.run(cmd_fallback, capture_output=True, check=True)

    finally:
        if temp_synth.exists():
            temp_synth.unlink()

    return output_wav


def fuse_voice_takes(take_wavs: List[Path], output_composite_wav: Path) -> Path:
    """Fuses multiple voice calibration takes into a single master reference WAV."""
    if not take_wavs:
        raise ValueError("Cannot fuse empty list of voice takes.")

    output_composite_wav.parent.mkdir(parents=True, exist_ok=True)
    if len(take_wavs) == 1:
        shutil.copyfile(take_wavs[0], output_composite_wav)
        return output_composite_wav

    inputs = []
    filter_inputs = []
    for idx, take in enumerate(take_wavs):
        inputs.extend(["-i", str(take)])
        filter_inputs.append(f"[{idx}:a]")

    filter_complex = f"{''.join(filter_inputs)}concat=n={len(take_wavs)}:v=0:a=1[out]"
    cmd = [
        "ffmpeg",
        "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-ar", "48000",
        "-ac", "2",
        "-c:a", "pcm_s16le",
        str(output_composite_wav),
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_composite_wav


def play_audio_clip(wav_path: Path) -> bool:
    """Plays an audio file using PipeWire (pw-play), ALSA (aplay), or FFmpeg (ffplay)."""
    if not wav_path.exists():
        return False

    for cmd in [
        ["pw-play", str(wav_path)],
        ["paplay", str(wav_path)],
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(wav_path)],
        ["aplay", "-q", str(wav_path)],
    ]:
        try:
            subprocess.run(cmd, timeout=8.0, check=True, capture_output=True)
            return True
        except Exception:
            continue
    return False


def run_voice_match_setup(
    profile_name: str = "my_voice",
    voices_dir: Optional[Path] = None,
    interactive: bool = True,
    custom_takes: Optional[List[Path]] = None,
    synthesize_audition: bool = True,
) -> VoiceProfile:
    """Interactive Google Assistant-style 4-phase Voice Match calibration wizard."""
    if voices_dir is None:
        voices_dir = Path(__file__).resolve().parent.parent.parent / "assets" / "voices"

    profile_dir = voices_dir / profile_name
    profile_dir.mkdir(parents=True, exist_ok=True)

    take_paths: List[Path] = []

    if custom_takes is not None:
        # Pre-supplied takes (for deterministic tests or automated batch enrollment)
        take_paths = list(custom_takes)
    else:
        # Live interactive recording of the 4 Google Assistant-style calibration sentences
        print("\n" + "=" * 70)
        print(" 🎙️  VISUAL LEARNING STUDIO — VOICE MATCH SETUP")
        print("=" * 70)
        print(" Like setting up Google Assistant, you will speak 4 calibration phrases")
        print(" to build your personalized voice model for video narration.")
        print("-" * 70)
        print(f" Target Profile:    '{profile_name}'")
        print(f" Capture Interface: Default Audio Input (PipeWire / ALSA)")
        print("=" * 70 + "\n")

        total_prompts = len(VOICE_MATCH_PROMPTS)
        for idx, prompt in enumerate(VOICE_MATCH_PROMPTS, start=1):
            # Render visual phase indicator: [● ○ ○ ○]
            dots = ["●" if i <= idx else "○" for i in range(1, total_prompts + 1)]
            indicator = " ".join(dots)

            take_wav = profile_dir / f"take_{idx}.wav"
            captured = False

            while not captured:
                print(f"┌{'─' * 68}┐")
                print(f"│ [{indicator}] Phrase {idx} of {total_prompts}: {prompt['title']:<42} │")
                print(f"├{'─' * 68}┤")
                print(f"│                                                                    │")
                print(f"│  \"{prompt['text']}\"")
                print(f"│                                                                    │")
                print(f"│  💡 Tip: {prompt['tip']:<57} │")
                print(f"└{'─' * 68}┘")

                if interactive:
                    try:
                        input(f"\nPress [ENTER] when ready to speak ({prompt['duration']:.1f}s take)... ")
                    except (EOFError, KeyboardInterrupt):
                        print("\nStarting take immediately...")

                print(f"[*] 🎙️ Listening... Speak now! ({prompt['duration']:.1f}s)")
                record_voice_clip(take_wav, duration_seconds=prompt["duration"])

                # Check capture energy
                acoustics = analyze_voice_acoustics(take_wav)
                if acoustics["speech_rms"] < 0.012:
                    print("\n[!] ⚠️ Take was too quiet or microphone was silent.")
                    print("[!] Please check microphone input and try again.\n")
                    if not interactive:
                        # In non-interactive mode, avoid infinite loop on quiet audio
                        captured = True
                        take_paths.append(take_wav)
                else:
                    print(f"[✓] Phrase {idx} captured! (Pitch: {acoustics['f0_median_hz']:.1f} Hz, Register: {acoustics['vocal_register']})\n")
                    captured = True
                    take_paths.append(take_wav)
                    time.sleep(0.4)

    # 1. Fuse all 4 takes into a master composite training reference
    print("[*] ⚙️ Fusing voice calibration takes and extracting composite acoustics...")
    master_ref = profile_dir / "reference.wav"
    fuse_voice_takes(take_paths, master_ref)

    # 2. Extract multi-sentence acoustic profile across the entire calibration corpus
    acoustics = analyze_voice_acoustics(master_ref)
    world_data = extract_world_acoustic_profile(master_ref)

    sig_file = profile_dir / "spectral_signature.npz"
    np.savez_compressed(
        str(sig_file),
        mean_sp=world_data["mean_sp"],
        mean_ap=world_data["mean_ap"],
    )

    # Extract & cache deep neural speaker embedding
    speaker_emb_path = None
    try:
        from src.audio.neural_cloner import get_neural_converter
        converter = get_neural_converter()
        se_file = profile_dir / "speaker_embedding.pt"
        converter.extract_speaker_embedding(master_ref, cache_path=se_file)
        speaker_emb_path = str(se_file.resolve())
    except Exception as e_neural:
        logger.warning(f"Neural speaker embedding extraction failed; WORLD fallback preserved: {e_neural}")

    # 3. Synthesize Audition Test Clip with the newly enrolled voice
    audition_path: Optional[Path] = None
    if synthesize_audition:
        try:
            print("[*] 🔊 Synthesizing audition test clip with your cloned voice...")
            from src.audio.tts_engine import synthesize_narration

            temp_profile = VoiceProfile(
                profile_name=profile_name,
                reference_audio=str(master_ref.resolve()),
                duration_seconds=acoustics["duration_seconds"],
                f0_mean_hz=acoustics["f0_mean_hz"],
                f0_median_hz=acoustics["f0_median_hz"],
                f0_std_hz=acoustics["f0_std_hz"],
                f0_log_mean=world_data["f0_log_mean"],
                f0_log_std=world_data["f0_log_std"],
                formants=world_data["formants"],
                spectral_signature_path=str(sig_file.resolve()),
                speaker_embedding_path=speaker_emb_path,
                vocal_register=acoustics["vocal_register"],
                base_voice=acoustics["base_voice"],
                base_f0_hz=acoustics["base_f0_hz"],
                pitch_ratio=acoustics["pitch_ratio"],
                pitch_semitones=acoustics["pitch_semitones"],
                eq_gains=acoustics["eq_gains"],
                speech_rms=acoustics["speech_rms"],
                takes=[str(p.resolve()) for p in take_paths],
                is_valid=True,
            )

            audition_wav = profile_dir / "audition.wav"
            synthesize_narration(
                "Voice Match complete. Your personalized voice model is calibrated and ready to produce educational videos.",
                audition_wav,
                voice_profile=temp_profile,
            )
            audition_path = audition_wav
        except Exception as e:
            logger.warning(f"Audition synthesis skipped: {e}")

    # 4. Save Persistent Profile JSON
    profile = VoiceProfile(
        profile_name=profile_name,
        reference_audio=str(master_ref.resolve()),
        duration_seconds=acoustics["duration_seconds"],
        f0_mean_hz=acoustics["f0_mean_hz"],
        f0_median_hz=acoustics["f0_median_hz"],
        f0_std_hz=acoustics["f0_std_hz"],
        f0_log_mean=world_data["f0_log_mean"],
        f0_log_std=world_data["f0_log_std"],
        formants=world_data["formants"],
        spectral_signature_path=str(sig_file.resolve()),
        speaker_embedding_path=speaker_emb_path,
        vocal_register=acoustics["vocal_register"],
        base_voice=acoustics["base_voice"],
        base_f0_hz=acoustics["base_f0_hz"],
        pitch_ratio=acoustics["pitch_ratio"],
        pitch_semitones=acoustics["pitch_semitones"],
        eq_gains=acoustics["eq_gains"],
        speech_rms=acoustics["speech_rms"],
        takes=[str(p.resolve()) for p in take_paths],
        audition_audio=str(audition_path.resolve()) if audition_path else None,
        is_valid=True,
    )

    profile_json = profile_dir / "profile.json"
    with open(profile_json, "w", encoding="utf-8") as f:
        f.write(profile.model_dump_json(indent=2))

    # 5. Print Confirmation Card
    print("\n" + "=" * 70)
    print(" 🎉 VOICE MATCH CALIBRATION COMPLETE!")
    print("=" * 70)
    print(f" Profile Name:      '{profile.profile_name}'")
    print(f" Calibration Audio: {profile.duration_seconds:.1f}s total across {len(take_paths)} takes")
    print(f" Detected Pitch:    {profile.f0_median_hz:.1f} Hz (Log F0: {profile.f0_log_mean:.2f} ± {profile.f0_log_std:.2f})")
    print(f" Extracted Formants:{', '.join(f'{f:.0f}Hz' for f in profile.formants) if profile.formants else 'Standard'}")
    print(f" Base Model Match:  {profile.base_voice} (Pitch Shift: {profile.pitch_ratio:.2f}x, {profile.pitch_semitones:+.1f} st)")
    print(f" Spectral Signature:{sig_file.name} (WORLD Vocoder 1025 frequency bins)")
    print(f" Master Reference:  {profile.reference_audio}")
    if profile.audition_audio:
        print(f" Audition Audio:    {profile.audition_audio}")
    print("=" * 70)
    print(f" To create videos using your cloned voice, run:")
    print(f"   ./scripts/run_production.sh --topic \"...\" --voice-profile {profile.profile_name}")
    print("=" * 70)

    # 6. Interactive Audition Playback
    if interactive and audition_path and audition_path.exists():
        try:
            choice = input("\nWould you like to listen to your voice model audition sample? [Y/n]: ").strip().lower()
            if choice in ["", "y", "yes"]:
                print("[*] 🔊 Playing audition sample...")
                play_audio_clip(audition_path)
        except (EOFError, KeyboardInterrupt):
            pass

    return profile
