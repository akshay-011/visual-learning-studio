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

    args = parser.parse_args()

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

    mp4_path, storyboard, qc = produce_video(
        source_input=source,
        output_dir=output_dir,
        mode=args.mode,
        target_duration=args.duration,
        burn_subtitles=burn_subs,
        include_music=args.include_music,
        include_sfx=args.include_sfx,
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
