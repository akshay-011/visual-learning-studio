"""High-Definition 1080p Programmatic Animation Engine."""

import math
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from src.storyboard.models import Scene, VisualSpec

FONT_DIR = Path("/usr/share/fonts/liberation")


def get_font(name: str = "bold", size: int = 32) -> ImageFont.FreeTypeFont:
    """Safe font loader with fallback."""
    font_map = {
        "bold": FONT_DIR / "LiberationSans-Bold.ttf",
        "regular": FONT_DIR / "LiberationSans-Regular.ttf",
        "mono": FONT_DIR / "LiberationMono-Regular.ttf",
        "mono_bold": FONT_DIR / "LiberationMono-Bold.ttf",
    }
    font_path = font_map.get(name, font_map["regular"])
    if font_path.exists():
        try:
            return ImageFont.truetype(str(font_path), size)
        except Exception:
            pass
    return ImageFont.load_default()


def draw_cyber_grid(draw: ImageDraw.ImageDraw, width: int, height: int, t: float) -> None:
    """Draws subtle background cyber grid points and coordinates."""
    grid_spacing = 80
    dot_color = (25, 36, 56)
    for x in range(40, width, grid_spacing):
        for y in range(40, height, grid_spacing):
            draw.ellipse([x - 1, y - 1, x + 1, y + 1], fill=dot_color)


def draw_header_banner(
    draw: ImageDraw.ImageDraw,
    spec: VisualSpec,
    width: int,
    t: float,
) -> None:
    """Draws standardized, cinematic top banner with category badge and typography."""
    font_badge = get_font("bold", 18)
    font_head = get_font("bold", 44)
    font_sub = get_font("regular", 24)

    # 1. Badge Pill
    if spec.badge:
        badge_text = spec.badge.upper()
        bbox = font_badge.getbbox(badge_text)
        bw = bbox[2] - bbox[0] + 32
        bh = 34
        bx = 90
        by = 50
        # Pill background
        draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=17, fill=(15, 35, 55), outline=(0, 242, 254), width=1)
        draw.text((bx + 16, by + 7), badge_text, font=font_badge, fill=(0, 242, 254))

    # 2. Main Headline
    if spec.headline:
        draw.text((90, 96), spec.headline, font=font_head, fill=(248, 250, 252))

    # 3. Subline
    if spec.subline:
        draw.text((90, 150), spec.subline, font=font_sub, fill=(148, 163, 184))

    # Decorative accent gradient bar
    draw.rectangle([90, 192, 90 + int(width * 0.88), 194], fill=(30, 41, 59))
    accent_width = int(220 + 80 * math.sin(t * math.pi))
    draw.rectangle([90, 192, 90 + accent_width, 194], fill=(0, 242, 254))


def render_cinematic_title_frame(spec: VisualSpec, t: float, width: int = 1920, height: int = 1080) -> Image.Image:
    """Renders high-impact opening cinematic title card."""
    img = Image.new("RGB", (width, height), color=(10, 15, 26))
    draw = ImageDraw.Draw(img)

    draw_cyber_grid(draw, width, height, t)

    # Center glowing radial halo
    center_x = width // 2
    center_y = height // 2 - 20
    pulse = math.sin(t * 2 * math.pi) * 20
    r = int(280 + pulse)
    draw.ellipse([center_x - r, center_y - r, center_x + r, center_y + r], outline=(15, 45, 75), width=2)
    draw.ellipse([center_x - r - 40, center_y - r - 40, center_x + r + 40, center_y + r + 40], outline=(12, 28, 48), width=1)

    # Badge
    if spec.badge:
        font_b = get_font("bold", 22)
        badge_text = spec.badge.upper()
        bbox = font_b.getbbox(badge_text)
        bw = bbox[2] - bbox[0] + 40
        draw.rounded_rectangle(
            [center_x - bw // 2, center_y - 140, center_x + bw // 2, center_y - 95],
            radius=22,
            fill=(14, 30, 50),
            outline=(0, 242, 254),
            width=2,
        )
        draw.text((center_x - bw // 2 + 20, center_y - 132), badge_text, font=font_b, fill=(0, 242, 254))

    # Headline
    font_title = get_font("bold", 64)
    bbox_t = font_title.getbbox(spec.headline)
    tw = bbox_t[2] - bbox_t[0]
    draw.text((center_x - tw // 2, center_y - 40), spec.headline, font=font_title, fill=(255, 255, 255))

    # Accent bar
    draw.rectangle([center_x - 160, center_y + 45, center_x + 160, center_y + 49], fill=(0, 242, 254))

    # Subline
    font_sub = get_font("regular", 28)
    bbox_s = font_sub.getbbox(spec.subline)
    sw = bbox_s[2] - bbox_s[0]
    draw.text((center_x - sw // 2, center_y + 75), spec.subline, font=font_sub, fill=(148, 163, 184))

    return img


def render_architecture_frame(spec: VisualSpec, t: float, width: int = 1920, height: int = 1080) -> Image.Image:
    """Renders crystal-clear system architecture diagram with nodes and connecting edges."""
    img = Image.new("RGB", (width, height), color=(9, 13, 22))
    draw = ImageDraw.Draw(img)

    draw_cyber_grid(draw, width, height, t)
    draw_header_banner(draw, spec, width, t)

    node_dict = {n["id"]: n for n in spec.diagram_nodes}

    # 1. Draw connecting edges
    font_edge = get_font("mono_bold", 18)
    for edge in spec.diagram_edges:
        u = node_dict.get(edge["from"])
        v = node_dict.get(edge["to"])
        if not u or not v:
            continue
        ux, uy = u["x"], u["y"]
        vx, vy = v["x"], v["y"]

        # Edge line
        draw.line([ux, uy, vx, vy], fill=(45, 65, 95), width=3)

        # Midpoint protocol label
        mx, my = (ux + vx) // 2, (uy + vy) // 2
        label = edge.get("label", "")
        if label:
            bbox = font_edge.getbbox(label)
            lw = bbox[2] - bbox[0] + 16
            lh = bbox[3] - bbox[1] + 10
            draw.rounded_rectangle([mx - lw // 2, my - lh // 2 - 16, mx + lw // 2, my + lh // 2 - 16], radius=6, fill=(13, 22, 38), outline=(56, 189, 248), width=1)
            draw.text((mx - lw // 2 + 8, my - lh // 2 - 14), label, font=font_edge, fill=(56, 189, 248))

    # 2. Draw nodes
    font_node = get_font("bold", 22)
    card_w, card_h = 220, 110

    for idx, node in enumerate(spec.diagram_nodes):
        nx, ny = node["x"], node["y"]
        # Gentle floating offset
        float_y = int(4 * math.sin((t * 2 * math.pi) + idx))
        top_left = (nx - card_w // 2, ny - card_h // 2 + float_y)
        bot_right = (nx + card_w // 2, ny + card_h // 2 + float_y)

        # Node container
        draw.rounded_rectangle([top_left[0], top_left[1], bot_right[0], bot_right[1]], radius=14, fill=(17, 24, 39), outline=(55, 65, 81), width=2)

        # Left color bar
        accent_color = node.get("color", "#38BDF8")
        draw.rounded_rectangle([top_left[0], top_left[1], top_left[0] + 8, bot_right[1]], radius=4, fill=accent_color)

        # Glowing outline for active node
        if idx == int(t * len(spec.diagram_nodes)) % len(spec.diagram_nodes):
            draw.rounded_rectangle([top_left[0] - 3, top_left[1] - 3, bot_right[0] + 3, bot_right[1] + 3], radius=16, outline=accent_color, width=2)

        # Node text
        label = node.get("label", "Node")
        bbox = font_node.getbbox(label)
        lw = bbox[2] - bbox[0]
        draw.text((nx - lw // 2, ny - 14 + float_y), label, font=font_node, fill=(243, 244, 246))

    return img


def render_flow_animation_frame(spec: VisualSpec, t: float, width: int = 1920, height: int = 1080) -> Image.Image:
    """Renders architecture diagram overlaid with glowing, traveling data packets."""
    img = render_architecture_frame(spec, t, width, height)
    draw = ImageDraw.Draw(img)

    node_dict = {n["id"]: n for n in spec.diagram_nodes}

    # Packet traversal calculation
    for packet in spec.flow_packets:
        t_start = packet.get("t_start", 0.0)
        t_end = packet.get("t_end", 1.0)
        if t < t_start or t > t_end:
            continue

        prog = (t - t_start) / (t_end - t_start + 1e-6)
        # Cubic ease in-out
        ease_prog = prog * prog * (3 - 2 * prog)

        u = node_dict.get(packet["from"])
        v = node_dict.get(packet["to"])
        if not u or not v:
            continue

        px = int(u["x"] + ease_prog * (v["x"] - u["x"]))
        py = int(u["y"] + ease_prog * (v["y"] - u["y"]))

        # Draw glowing packet orb
        draw.ellipse([px - 18, py - 18, px + 18, py + 18], fill=(0, 242, 254), outline=(255, 255, 255), width=2)
        # Outer glow ring
        draw.ellipse([px - 26, py - 26, px + 26, py + 26], outline=(0, 242, 254), width=1)

        # Label tag
        label = packet.get("label", "DATA")
        font_p = get_font("bold", 18)
        bbox = font_p.getbbox(label)
        pw = bbox[2] - bbox[0] + 16
        draw.rounded_rectangle([px - pw // 2, py + 24, px + pw // 2, py + 52], radius=6, fill=(15, 23, 42), outline=(0, 242, 254), width=1)
        draw.text((px - pw // 2 + 8, py + 29), label, font=font_p, fill=(248, 250, 252))

    return img


def render_code_walkthrough_frame(spec: VisualSpec, t: float, width: int = 1920, height: int = 1080) -> Image.Image:
    """Renders IDE window with syntax-highlighted code and spotlight line focus."""
    img = Image.new("RGB", (width, height), color=(10, 15, 26))
    draw = ImageDraw.Draw(img)

    draw_cyber_grid(draw, width, height, t)
    draw_header_banner(draw, spec, width, t)

    # IDE Window bounds
    wx, wy = 120, 230
    ww, wh = width - 240, 760

    # Window frame
    draw.rounded_rectangle([wx, wy, wx + ww, wy + wh], radius=16, fill=(15, 23, 42), outline=(30, 41, 59), width=2)
    # Window header bar
    draw.rounded_rectangle([wx, wy, wx + ww, wy + 50], radius=16, fill=(20, 30, 52))
    draw.rectangle([wx, wy + 30, wx + ww, wy + 50], fill=(20, 30, 52))

    # Window traffic lights
    draw.ellipse([wx + 20, wy + 18, wx + 34, wy + 32], fill=(239, 68, 68))
    draw.ellipse([wx + 44, wy + 18, wx + 58, wy + 32], fill=(234, 179, 8))
    draw.ellipse([wx + 68, wy + 18, wx + 82, wy + 32], fill=(34, 197, 94))

    # Filename tab
    font_tab = get_font("mono_bold", 18)
    draw.text((wx + 110, wy + 16), "controller/checkout_pipeline.py", font=font_tab, fill=(148, 163, 184))

    # Code lines
    font_code = get_font("mono", 22)
    line_y = wy + 80
    highlight_idx = spec.highlighted_line if spec.highlighted_line is not None else 3

    for idx, line_text in enumerate(spec.code_lines):
        # Line number
        draw.text((wx + 30, line_y), f"{idx + 1:2d}", font=font_code, fill=(71, 85, 105))

        # Highlight background for active line
        if idx == highlight_idx:
            draw.rounded_rectangle([wx + 75, line_y - 4, wx + ww - 30, line_y + 30], radius=6, fill=(30, 58, 138), outline=(56, 189, 248), width=1)
            line_color = (255, 255, 255)
        else:
            line_color = (226, 232, 240)

        draw.text((wx + 90, line_y), line_text, font=font_code, fill=line_color)
        line_y += 42

    return img


def render_metric_grid_frame(spec: VisualSpec, t: float, width: int = 1920, height: int = 1080) -> Image.Image:
    """Renders 4-card metric dashboard with glowing KPI values."""
    img = Image.new("RGB", (width, height), color=(10, 15, 26))
    draw = ImageDraw.Draw(img)

    draw_cyber_grid(draw, width, height, t)
    draw_header_banner(draw, spec, width, t)

    cards = spec.metric_cards or [
        {"label": "DNS & TLS", "value": "12 ms", "desc": "Edge resolution"},
        {"label": "Gateway Auth", "value": "3 ms", "desc": "JWT validation"},
        {"label": "Cache Lookup", "value": "1 ms", "desc": "In-memory hit"},
        {"label": "Database Commit", "value": "18 ms", "desc": "B-Tree indexed write"},
    ]

    card_w, card_h = 400, 240
    start_x = (width - (4 * card_w + 3 * 30)) // 2
    card_y = 420

    font_val = get_font("bold", 54)
    font_lbl = get_font("bold", 22)
    font_desc = get_font("regular", 18)

    for idx, card in enumerate(cards[:4]):
        cx = start_x + idx * (card_w + 30)

        # Highlight currently featured card
        is_active = (idx == int(t * 4) % 4)
        border_col = (0, 242, 254) if is_active else (30, 41, 59)
        bg_col = (18, 30, 52) if is_active else (15, 23, 42)

        draw.rounded_rectangle([cx, card_y, cx + card_w, card_y + card_h], radius=16, fill=bg_col, outline=border_col, width=2)

        # Accent top bar
        draw.rounded_rectangle([cx, card_y, cx + card_w, card_y + 8], radius=4, fill=border_col)

        # Value
        draw.text((cx + 30, card_y + 40), card["value"], font=font_val, fill=(0, 242, 254) if is_active else (255, 255, 255))
        # Label
        draw.text((cx + 30, card_y + 120), card["label"], font=font_lbl, fill=(248, 250, 252))
        # Description
        draw.text((cx + 30, card_y + 160), card.get("desc", ""), font=font_desc, fill=(148, 163, 184))

    return img


def render_scene_frame(scene: Scene, t: float, width: int = 1920, height: int = 1080) -> Image.Image:
    """Dispatches scene rendering to the appropriate specialized visual engine."""
    vtype = scene.visual_type
    spec = scene.visual_spec

    if vtype == "cinematic_title":
        return render_cinematic_title_frame(spec, t, width, height)
    elif vtype == "architecture_diagram":
        return render_architecture_frame(spec, t, width, height)
    elif vtype == "flow_animation":
        return render_flow_animation_frame(spec, t, width, height)
    elif vtype == "code_walkthrough":
        return render_code_walkthrough_frame(spec, t, width, height)
    elif vtype == "metric_grid":
        return render_metric_grid_frame(spec, t, width, height)
    else:
        # Fallback to architecture frame
        return render_architecture_frame(spec, t, width, height)
