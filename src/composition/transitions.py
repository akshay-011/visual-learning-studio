"""Transition specifications and filtergraph utilities."""

from typing import List


def build_xfade_filter(num_scenes: int, scene_durations: List[float], transition_duration: float = 0.5) -> str:
    """Builds an FFmpeg xfade filtergraph for seamless crossfading between scenes."""
    if num_scenes <= 1:
        return "[0:v]null[v_final]"

    filters = []
    current_out = "0:v"
    cumulative_offset = 0.0

    for i in range(1, num_scenes):
        dur = scene_durations[i - 1]
        offset = max(0.0, cumulative_offset + dur - transition_duration)
        next_out = f"v_xfade_{i}" if i < num_scenes - 1 else "v_final"
        filters.append(
            f"[{current_out}][{i}:v]xfade=transition=fade:duration={transition_duration}:offset={offset:.2f}[{next_out}]"
        )
        current_out = next_out
        cumulative_offset += dur - transition_duration

    return ";".join(filters)
