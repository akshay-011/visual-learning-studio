#!/usr/bin/env python3
"""Visual Learning Studio - Command-Line Interface."""

import argparse
import json
import sys
from pathlib import Path

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from src.audio.cloner import (
    DEFAULT_PROMPT_SENTENCE,
    enroll_voice,
    list_voice_profiles,
    load_voice_profile,
    record_voice_clip,
    run_voice_match_setup,
)
from src.discovery.hardware import detect_hardware
from src.orchestration.pipeline import produce_video


def main():
    parser = argparse.ArgumentParser(
        description="Visual Learning Studio: Zero-Cost Autonomous Educational Video Production."
    )
    parser.add_argument(
        "--check-hardware",
        action="store_true",
        help="Probe and report host hardware, GPU VRAM, and production profile.",
    )
    parser.add_argument(
        "--topic",
        type=str,
        help="Technical topic or subject to explain (e.g. 'How an API request travels').",
    )
    parser.add_argument(
        "--repo",
        type=str,
        help="GitHub repository URL or local project folder path.",
    )
    parser.add_argument(
        "--pdf",
        type=str,
        help="Path to research paper or documentation PDF.",
    )
    parser.add_argument(
        "--url",
        type=str,
        help="Web documentation or article URL.",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["beginner", "technical", "documentary"],
        default="technical",
        help="Educational format profile.",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=60.0,
        help="Target video duration in seconds (e.g. 30, 60, 90).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output/run",
        help="Directory to save final MP4, storyboard, subtitles, and narration.",
    )
    parser.add_argument(
        "--burn-subtitles",
        action="store_true",
        default=False,
        help="Burn styled subtitle text into final MP4 (default: False).",
    )
    parser.add_argument(
        "--no-subtitles",
        action="store_true",
        default=False,
        help="Do not burn subtitles on exported video (default behavior).",
    )
    parser.add_argument(
        "--include-music",
        action="store_true",
        default=False,
        help="Include background music in audio mix (default: False).",
    )
    parser.add_argument(
        "--include-sfx",
        action="store_true",
        default=False,
        help="Include contextual sound effects in audio mix (default: False).",
    )
    parser.add_argument(
        "--setup-voice",
        action="store_true",
        help="Launch the Google Assistant-style 4-phrase Voice Match calibration wizard.",
    )
    parser.add_argument(
        "--record-voice",
        action="store_true",
        help="Record voice from microphone and enroll a new cloned voice profile.",
    )
    parser.add_argument(
        "--record-seconds",
        type=float,
        default=8.0,
        help="Duration in seconds to record voice sample (default: 8.0).",
    )
    parser.add_argument(
        "--voice-profile",
        type=str,
        default=None,
        help="Voice profile name to use (e.g. 'my_voice', or a custom enrolled profile name).",
    )
    parser.add_argument(
        "--voice",
        type=str,
        default=None,
        help="Built-in neural voice (e.g. 'andrew', 'brian', 'ava', 'jenny', or full name 'en-US-AndrewNeural').",
    )
    parser.add_argument(
        "--clone-voice",
        type=str,
        default=None,
        help="Path to an existing audio file (.wav, .mp3) to clone into a voice profile.",
    )
    parser.add_argument(
        "--list-voices",
        action="store_true",
        help="List all enrolled local voice profiles and built-in neural voices.",
    )

    args = parser.parse_args()

    # Built-in Voice Aliases
    voice_aliases = {
        "andrew": "en-US-AndrewNeural",
        "brian": "en-US-BrianNeural",
        "ava": "en-US-AvaNeural",
        "jenny": "en-US-JennyNeural",
        "guy": "en-US-GuyNeural",
        "aria": "en-US-AriaNeural",
    }
    selected_voice = voice_aliases.get(args.voice.lower(), args.voice) if args.voice else None

    if args.list_voices:
        profiles = list_voice_profiles()
        print("=" * 68)
        print(" 🎙️  VISUAL LEARNING STUDIO — VOICE ROSTER")
        print("=" * 68)
        print(" [1] ENROLLED CLONED VOICES (Local Neural Voice Cloning):")
        print("-" * 68)
        if not profiles:
            print("  No cloned voice profiles enrolled yet.")
            print("  To enroll your voice (Google Assistant style), run:")
            print("    ./scripts/voice_setup.sh my_voice")
        else:
            for p in profiles:
                neural_status = "Active (OpenVoice V2)" if getattr(p, "speaker_embedding_path", None) else "WORLD Fallback"
                print(f"  • Profile Name:    '{p.profile_name}'")
                print(f"    Neural Cloner:   {neural_status}")
                print(f"    Detected Pitch:  {p.f0_median_hz:.1f} Hz ({p.vocal_register})")
                print(f"    Base Voice:      {p.base_voice}")
                print(f"    Usage Command:   --voice-profile {p.profile_name}")
                print("-" * 68)
        print("\n [2] BUILT-IN NEURAL VOICES:")
        print("-" * 68)
        print("  • andrew:  en-US-AndrewNeural (Warm, authoritative Baritone)")
        print("  • brian:   en-US-BrianNeural  (Engaging, conversational Tenor)")
        print("  • ava:     en-US-AvaNeural    (Warm, expressive Alto)")
        print("  • jenny:   en-US-JennyNeural  (Clear, bright Soprano)")
        print("=" * 68)
        print(" Natural Language Prompts in AGY:")
        print("  - \"Create a video about X using my voice\"       -> --voice-profile my_voice")
        print("  - \"Create a video about X using <name>'s voice\"  -> --voice-profile <name>")
        print("  - \"Create a video about X using Brian's voice\"   -> --voice brian")
        print("  - \"Create a video about X using Ava's voice\"     -> --voice ava")
        print("=" * 68)
        return

    # Handle Google Assistant-style 4-Phase Voice Match Calibration
    if args.setup_voice:
        profile_name = args.voice_profile or "my_voice"
        run_voice_match_setup(profile_name=profile_name)
        if not (args.topic or args.repo or args.pdf or args.url):
            return

    # Handle Single-Pass Voice Enrollment via Microphone Recording
    if args.record_voice:
        profile_name = args.voice_profile or "my_voice"
        print("=" * 65)
        print(" VISUAL LEARNING STUDIO - VOICE ENROLLMENT")
        print("=" * 65)
        print(f"Target Profile:    '{profile_name}'")
        print(f"Capture Interface: Default System Audio Input (PipeWire / ALSA)")
        print(f"Duration:          {args.record_seconds:.1f} seconds")
        print("-" * 65)
        print("Please read this calibration passage clearly into your microphone:")
        print(f"\n  \"{DEFAULT_PROMPT_SENTENCE}\"\n")
        print("-" * 65)

        try:
            input("Press [Enter] when ready to begin speaking (recording starts immediately)... ")
        except (EOFError, KeyboardInterrupt):
            print("\nStarting recording immediately...")

        print(f"[*] Recording for {args.record_seconds:.1f}s... (Speak now!)")
        temp_rec = Path(f"/tmp/enroll_{profile_name}_{int(time.time())}.wav")
        try:
            record_voice_clip(temp_rec, duration_seconds=args.record_seconds)
            profile = enroll_voice(temp_rec, profile_name=profile_name)
            print("\n" + "=" * 65)
            print(" VOICE ENROLLMENT COMPLETED SUCCESSFULLY")
            print("=" * 65)
            print(f"Profile Name:     {profile.profile_name}")
            print(f"Reference Audio:  {profile.reference_audio}")
            print(f"Detected Pitch:   {profile.f0_median_hz} Hz ({profile.vocal_register})")
            print(f"Base Model Match: {profile.base_voice} (Shift: {profile.pitch_ratio:.2f}x, {profile.pitch_semitones:+.1f} st)")
            print(f"Formant Offsets:  Sub:{profile.eq_gains.get('sub_bass',0):+.1f}dB | "
                  f"Mid:{profile.eq_gains.get('mid',0):+.1f}dB | "
                  f"Pres:{profile.eq_gains.get('presence',0):+.1f}dB")
            print("=" * 65)
            print(f"To use your cloned voice in any video:")
            print(f"  ./scripts/run_production.sh --topic \"...\" --voice-profile {profile.profile_name}")
            print("=" * 65)
        finally:
            if temp_rec.exists():
                temp_rec.unlink()

        # If user only wanted to record voice and provided no topic/repo, exit now
        if not (args.topic or args.repo or args.pdf or args.url):
            return

    # Handle Voice Enrollment via Audio File Import
    if args.clone_voice and not (args.topic or args.repo or args.pdf or args.url):
        sample_path = Path(args.clone_voice)
        profile_name = args.voice_profile or sample_path.stem.replace(" ", "_").lower()
        profile = enroll_voice(sample_path, profile_name=profile_name)
        print("=" * 65)
        print(f" VOICE ENROLLED FROM AUDIO FILE: '{sample_path.name}'")
        print("=" * 65)
        print(f"Profile Name:     {profile.profile_name}")
        print(f"Detected Pitch:   {profile.f0_median_hz} Hz ({profile.vocal_register})")
        print(f"Base Model Match: {profile.base_voice} (Shift: {profile.pitch_ratio:.2f}x)")
        print(f"Reference Audio:  {profile.reference_audio}")
        print("=" * 65)
        return

    if args.check_hardware:
        hw = detect_hardware()
        print("=" * 60)
        print(" VISUAL LEARNING STUDIO - HARDWARE DISCOVERY REPORT")
        print("=" * 60)
        print(f"OS:                  {hw.os_name}")
        print(f"CPU:                 {hw.cpu_model} ({hw.cpu_cores} cores)")
        print(f"RAM:                 {hw.ram_gb:.1f} GB")
        print(f"Disk Available:      {hw.disk_available_gb:.1f} GB")
        print(f"GPU:                 {hw.gpu_name or 'None'} ({hw.vram_mb or 0} MB VRAM)")
        print(f"CUDA Available:      {hw.has_cuda}")
        print(f"Recommended Encoder: {hw.recommended_encoder}")
        print(f"Ollama Active:       {hw.ollama_running}")
        print(f"Production Profile:  {hw.profile}")
        print("=" * 60)
        return

    # Determine input source
    source = args.topic or args.repo or args.pdf or args.url
    if not source:
        parser.print_help()
        print("\nError: Please provide an input source (--topic, --repo, --pdf, or --url).")
        sys.exit(1)

    output_dir = Path(args.output_dir)
    print(f"[*] Starting Visual Learning Studio production...")
    print(f"[*] Source:   {source}")
    print(f"[*] Mode:     {args.mode}")
    print(f"[*] Duration: {args.duration:.1f}s")
    print(f"[*] Output:   {output_dir}")

    burn_subs = args.burn_subtitles and not args.no_subtitles
    voice_prof = args.voice_profile or args.clone_voice

    mp4_path, storyboard, qc = produce_video(
        source_input=source,
        output_dir=output_dir,
        mode=args.mode,
        target_duration=args.duration,
        burn_subtitles=burn_subs,
        include_music=args.include_music,
        include_sfx=args.include_sfx,
        voice_profile=voice_prof,
        default_voice=selected_voice,
    )

    print("\n" + "=" * 60)
    print(" PRODUCTION COMPLETED SUCCESSFULLY")
    print("=" * 60)
    print(f"Final MP4:     {mp4_path}")
    print(f"File Size:     {qc.file_size_mb} MB")
    print(f"Duration:      {qc.duration_seconds}s (Target: {qc.duration_target}s)")
    print(f"Resolution:    {qc.width}x{qc.height} @ {qc.fps}fps")
    print(f"Quality Check: {'PASSED' if qc.is_valid else 'FAILED'}")
    print(f"Summary:       {qc.summary}")
    print("=" * 60)


if __name__ == "__main__":
    main()
