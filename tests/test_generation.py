"""Tests for programmatic frame rendering."""

from src.generation.programmatic_animator import (
    render_cinematic_title_frame,
    render_architecture_frame,
    render_flow_animation_frame,
    render_code_walkthrough_frame,
    render_metric_grid_frame,
)
from src.storyboard.models import VisualSpec


def test_render_all_frame_types():
    spec = VisualSpec(
        headline="DISTRIBUTED ARCHITECTURE",
        subline="Packet Flow Verification",
        badge="PRODUCTION GRADE",
        diagram_nodes=[
            {"id": "a", "label": "Client", "x": 400, "y": 540},
            {"id": "b", "label": "Server", "x": 1400, "y": 540},
        ],
        diagram_edges=[{"from": "a", "to": "b", "label": "HTTP"}],
        flow_packets=[{"from": "a", "to": "b", "t_start": 0.0, "t_end": 1.0, "label": "DATA"}],
        code_lines=["def handle():", "    return 200"],
        metric_cards=[{"label": "RTT", "value": "20ms", "desc": "Ping"}],
    )

    f1 = render_cinematic_title_frame(spec, 0.5)
    assert f1.size == (1920, 1080)

    f2 = render_architecture_frame(spec, 0.5)
    assert f2.size == (1920, 1080)

    f3 = render_flow_animation_frame(spec, 0.5)
    assert f3.size == (1920, 1080)

    f4 = render_code_walkthrough_frame(spec, 0.5)
    assert f4.size == (1920, 1080)

    f5 = render_metric_grid_frame(spec, 0.5)
    assert f5.size == (1920, 1080)
