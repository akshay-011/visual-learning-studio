"""Learning Architect: Converts research dossiers into structured pedagogical lessons."""

from typing import Any, Dict, List, Optional
from src.research.engine import ResearchReport
from src.storyboard.models import AudioSpec, Scene, Storyboard, VisualSpec


def build_30s_lesson(report: ResearchReport, mode: str = "technical") -> Storyboard:
    """Constructs a high-impact, focused 30-second educational storyboard."""
    title = report.title
    voice = "en-US-AndrewNeural" if mode == "technical" else ("en-US-BrianNeural" if mode == "beginner" else "en-US-AvaNeural")

    # Nodes for architecture diagram in 1920x1080 coordinate space
    nodes_30s = [
        {"id": "client", "label": "Client App", "x": 300, "y": 540, "color": "#38BDF8", "icon": "laptop"},
        {"id": "gateway", "label": "API Gateway", "x": 750, "y": 540, "color": "#818CF8", "icon": "shield"},
        {"id": "service", "label": "Order Service", "x": 1200, "y": 540, "color": "#34D399", "icon": "server"},
        {"id": "db", "label": "Database", "x": 1620, "y": 540, "color": "#F472B6", "icon": "database"},
    ]
    edges_30s = [
        {"from": "client", "to": "gateway", "label": "HTTPS / TLS"},
        {"from": "gateway", "to": "service", "label": "gRPC Mesh"},
        {"from": "service", "to": "db", "label": "SQL Query"},
    ]

    scenes = [
        # Scene 1: Hook & Core Question (8.0s)
        Scene(
            scene_id="scene_01_hook",
            duration=8.0,
            narration="Every time you click a button online, a complex packet journey begins across distributed networks.",
            educational_objective="Hook the viewer with the invisible complexity of modern backend systems.",
            visual_type="cinematic_title",
            visual_spec=VisualSpec(
                headline=title.upper(),
                subline="The Invisible Journey of Distributed Systems",
                badge="DISTRIBUTED SYSTEMS 101",
                theme="dark_cyan",
            ),
            audio_spec=AudioSpec(
                narration_voice=voice,
                sfx_cue="impactSoft_medium_001.ogg",
                music_track="happy-beats-business-moves-vol-10-by-ende-dot-app.mp3",
                music_volume=0.12,
            ),
            transition="crossfade",
        ),
        # Scene 2: The Core Mechanism & Animated Flow (14.0s)
        Scene(
            scene_id="scene_02_mechanism",
            duration=14.0,
            narration="Your request first hits the API Gateway for TLS termination and authentication, then routes directly through internal microservices into database indexes.",
            educational_objective="Demonstrate multi-tier gateway routing, security validation, and database access.",
            visual_type="flow_animation",
            visual_spec=VisualSpec(
                headline="REQUEST ROUTING PIPELINE",
                subline="TLS Termination → JWT Auth → Microservice Routing",
                badge="STAGE 2: PACKET TRAVERSAL",
                diagram_nodes=nodes_30s,
                diagram_edges=edges_30s,
                flow_packets=[
                    {"from": "client", "to": "gateway", "t_start": 0.0, "t_end": 0.35, "label": "POST /order"},
                    {"from": "gateway", "to": "service", "t_start": 0.35, "t_end": 0.70, "label": "Auth OK"},
                    {"from": "service", "to": "db", "t_start": 0.70, "t_end": 1.0, "label": "Index Lookup"},
                ],
                theme="cyber_dark",
            ),
            audio_spec=AudioSpec(
                narration_voice=voice,
                sfx_cue="impactSoft_medium_004.ogg",
                music_track="happy-beats-business-moves-vol-10-by-ende-dot-app.mp3",
                music_volume=0.10,
            ),
            transition="crossfade",
        ),
        # Scene 3: The Payoff & Performance Metrics (8.0s)
        Scene(
            scene_id="scene_03_takeaway",
            duration=8.0,
            narration="In less than fifty milliseconds, state is committed and confirmed, delivering sub-second experiences to millions of users.",
            educational_objective="Anchor the speed and engineering discipline of modern architectures.",
            visual_type="metric_grid",
            visual_spec=VisualSpec(
                headline="SYSTEM PERFORMANCE METRICS",
                subline="Deterministic Low-Latency Delivery",
                badge="PRODUCTION METRICS",
                metric_cards=[
                    {"label": "TLS Handshake", "value": "12 ms", "desc": "Encrypted session"},
                    {"label": "Gateway Auth", "value": "3 ms", "desc": "JWT validation"},
                    {"label": "Database Query", "value": "18 ms", "desc": "B-Tree indexed lookup"},
                    {"label": "Total Latency", "value": "45 ms", "desc": "Round-trip completed"},
                ],
                theme="dark_cyan",
            ),
            audio_spec=AudioSpec(
                narration_voice=voice,
                sfx_cue="impactSoft_medium_002.ogg",
                music_track="happy-beats-business-moves-vol-10-by-ende-dot-app.mp3",
                music_volume=0.12,
            ),
            transition="crossfade",
        ),
    ]

    return Storyboard(
        title=f"{title} (30s Edition)",
        mode=mode,
        target_duration=30.0,
        aspect_ratio="16:9",
        width=1920,
        height=1080,
        fps=30,
        scenes=scenes,
    )


def build_60s_lesson(report: ResearchReport, mode: str = "technical") -> Storyboard:
    """Constructs a comprehensive, multi-scene 60-second educational storyboard."""
    title = report.title
    voice = "en-US-AndrewNeural" if mode == "technical" else ("en-US-BrianNeural" if mode == "beginner" else "en-US-AvaNeural")

    # Complete 5-tier architecture nodes for 60s
    nodes_60s = [
        {"id": "client", "label": "Client / Browser", "x": 240, "y": 540, "color": "#38BDF8", "icon": "laptop"},
        {"id": "dns_cdn", "label": "Edge / DNS", "x": 600, "y": 380, "color": "#FBBF24", "icon": "globe"},
        {"id": "gateway", "label": "API Gateway", "x": 960, "y": 540, "color": "#818CF8", "icon": "shield"},
        {"id": "service", "label": "Order Service", "x": 1340, "y": 420, "color": "#34D399", "icon": "server"},
        {"id": "cache", "label": "Redis Cache", "x": 1340, "y": 700, "color": "#F87171", "icon": "layers"},
        {"id": "db", "label": "PostgreSQL DB", "x": 1680, "y": 540, "color": "#C084FC", "icon": "database"},
    ]
    edges_60s = [
        {"from": "client", "to": "dns_cdn", "label": "DNS Query"},
        {"from": "client", "to": "gateway", "label": "HTTPS TLS 1.3"},
        {"from": "gateway", "to": "service", "label": "Internal Mesh"},
        {"from": "service", "to": "cache", "label": "Sub-millisecond Read"},
        {"from": "service", "to": "db", "label": "Indexed SQL Write"},
    ]

    code_sample = [
        "@app.post('/api/checkout')",
        "async def handle_order(req: OrderRequest, user = Depends(verify_jwt)):",
        "    cached_session = await redis_client.get(f'user:{user.id}')",
        "    if not cached_session:",
        "        raise HTTPException(status_code=401, detail='Session Expired')",
        "    order_id = await db.orders.insert({'user': user.id, 'items': req.items})",
        "    await event_bus.publish('order_placed', {'order_id': order_id})",
        "    return {'status': 'confirmed', 'order_id': order_id, 'latency_ms': 34}",
    ]

    scenes = [
        # Scene 1: Cinematic Hook (9.0s)
        Scene(
            scene_id="scene_01_hook",
            duration=9.0,
            narration="Every time you tap 'Buy Now', an invisible journey begins across modern distributed infrastructure.",
            educational_objective="Capture immediate interest with the hidden scale of an everyday digital transaction.",
            visual_type="cinematic_title",
            visual_spec=VisualSpec(
                headline="HOW AN API REQUEST TRAVELS",
                subline="Anatomy of a Distributed Backend Transaction",
                badge="SYSTEM ARCHITECTURE",
                theme="dark_cyan",
            ),
            audio_spec=AudioSpec(
                narration_voice=voice,
                sfx_cue="impactSoft_medium_001.ogg",
                music_track="happy-beats-business-moves-vol-1-by-ende-dot-app.mp3",
                music_volume=0.12,
            ),
            transition="crossfade",
        ),
        # Scene 2: Entry Gate & Security Inspection (13.0s)
        Scene(
            scene_id="scene_02_gateway",
            duration=13.0,
            narration="Your request connects to the API Gateway. Here, TLS encryption terminates, JWT security tokens are verified, and rate limits are strictly enforced.",
            educational_objective="Explain the critical security, proxy, and rate-limiting roles of the API gateway tier.",
            visual_type="architecture_diagram",
            visual_spec=VisualSpec(
                headline="THE INGRESS GATEWAY",
                subline="TLS 1.3 Termination • JWT Token Verification • Rate Limiting",
                badge="TIER 1: EDGE & INGRESS",
                diagram_nodes=nodes_60s[:3],
                diagram_edges=edges_60s[:2],
                theme="cyber_dark",
            ),
            audio_spec=AudioSpec(
                narration_voice=voice,
                sfx_cue="impactSoft_medium_004.ogg",
                music_track="happy-beats-business-moves-vol-1-by-ende-dot-app.mp3",
                music_volume=0.10,
            ),
            transition="crossfade",
        ),
        # Scene 3: Internal Routing & Distributed Packet Traversal (15.0s)
        Scene(
            scene_id="scene_03_flow",
            duration=15.0,
            narration="Inside the private cluster, the request routes to the Order Service. It queries an in-memory Redis cache before reaching database indexes in microseconds.",
            educational_objective="Visualize distributed service mesh routing, caching layers, and database lookups.",
            visual_type="flow_animation",
            visual_spec=VisualSpec(
                headline="DISTRIBUTED SERVICE MESH",
                subline="High-Speed Inter-Process RPC & Memory Cache Inspection",
                badge="TIER 2: SERVICE DISPATCH",
                diagram_nodes=nodes_60s,
                diagram_edges=edges_60s,
                flow_packets=[
                    {"from": "client", "to": "gateway", "t_start": 0.0, "t_end": 0.25, "label": "HTTPS Request"},
                    {"from": "gateway", "to": "service", "t_start": 0.25, "t_end": 0.50, "label": "Internal RPC"},
                    {"from": "service", "to": "cache", "t_start": 0.50, "t_end": 0.75, "label": "Cache Check"},
                    {"from": "service", "to": "db", "t_start": 0.75, "t_end": 1.0, "label": "SQL Commit"},
                ],
                theme="cyber_dark",
            ),
            audio_spec=AudioSpec(
                narration_voice=voice,
                sfx_cue="impactSoft_medium_003.ogg",
                music_track="happy-beats-business-moves-vol-1-by-ende-dot-app.mp3",
                music_volume=0.10,
            ),
            transition="crossfade",
        ),
        # Scene 4: Code Demonstration & Transaction Commit (13.0s)
        Scene(
            scene_id="scene_04_code",
            duration=13.0,
            narration="Here in the backend controller, asynchronous workers process business validation, commit database transactions, and dispatch confirmation events.",
            educational_objective="Anchor the architecture with real executable controller logic and database mutations.",
            visual_type="code_walkthrough",
            visual_spec=VisualSpec(
                headline="CONTROLLER IMPLEMENTATION",
                subline="Asynchronous Non-Blocking Request Handling",
                badge="SOURCE CODE INSPECTION",
                code_lines=code_sample,
                highlighted_line=5,
                theme="cyber_dark",
            ),
            audio_spec=AudioSpec(
                narration_voice=voice,
                sfx_cue="keyboard/keypress-001.wav",
                music_track="happy-beats-business-moves-vol-1-by-ende-dot-app.mp3",
                music_volume=0.10,
            ),
            transition="crossfade",
        ),
        # Scene 5: Resolution & Production Takeaway (10.0s)
        Scene(
            scene_id="scene_05_summary",
            duration=10.0,
            narration="In under fifty milliseconds, the response returns—a testament to the precision of modern distributed software engineering.",
            educational_objective="Synthesize the educational takeaways with performance metrics and closing reflection.",
            visual_type="metric_grid",
            visual_spec=VisualSpec(
                headline="TRANSACTION SUMMARY",
                subline="End-to-End Latency: 42ms • Zero Data Loss",
                badge="KEY TAKEAWAYS",
                metric_cards=[
                    {"label": "Edge Routing", "value": "11 ms", "desc": "TLS & DNS overhead"},
                    {"label": "Auth & Gateway", "value": "4 ms", "desc": "Token validation"},
                    {"label": "Cache Query", "value": "1 ms", "desc": "Redis memory hit"},
                    {"label": "Database Write", "value": "19 ms", "desc": "B-Tree indexed commit"},
                ],
                theme="dark_cyan",
            ),
            audio_spec=AudioSpec(
                narration_voice=voice,
                sfx_cue="impactSoft_medium_002.ogg",
                music_track="happy-beats-business-moves-vol-1-by-ende-dot-app.mp3",
                music_volume=0.12,
            ),
            transition="crossfade",
        ),
    ]

    return Storyboard(
        title=f"{title} (Full 60s Edition)",
        mode=mode,
        target_duration=60.0,
        aspect_ratio="16:9",
        width=1920,
        height=1080,
        fps=30,
        scenes=scenes,
    )


def plan_storyboard(report: ResearchReport, mode: str = "technical", duration: float = 60.0) -> Storyboard:
    """Master pedagogical planner selecting appropriate scene distribution."""
    if duration <= 35.0:
        return build_30s_lesson(report, mode=mode)
    else:
        return build_60s_lesson(report, mode=mode)
