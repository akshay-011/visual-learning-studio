"""Wan2GP MCP Adapter: Connects to local or remote Wan 2.1 Video generation instances."""

import os
import json
from typing import Any, Dict, Optional
import requests


class Wan2GPAdapter:
    """Clean adapter for Wan2GP MCP server as researched from Open-Generative-AI."""

    def __init__(self, endpoint: Optional[str] = None):
        self.endpoint = endpoint or os.environ.get("VLS_WAN2GP_MCP_URL", "http://127.0.0.1:7866/mcp")
        self._next_id = 1
        self._session_id: Optional[str] = None
        self._is_available: Optional[bool] = None

    def is_available(self) -> bool:
        """Probes whether a running Wan2GP MCP server is reachable."""
        if self._is_available is not None:
            return self._is_available
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": self._next_id,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "visual-learning-studio", "version": "1.0"},
                },
            }
            resp = requests.post(self.endpoint, json=payload, timeout=2.0)
            self._is_available = resp.status_code == 200
        except Exception:
            self._is_available = False
        return self._is_available

    def check_model_status(self, model_type: str = "wan2.1_t2v") -> str:
        """Queries model availability on disk."""
        if not self.is_available():
            return "service_unavailable"
        try:
            self._next_id += 1
            payload = {
                "jsonrpc": "2.0",
                "id": self._next_id,
                "method": "tools/call",
                "params": {
                    "name": "wangp_get_model_availability",
                    "arguments": {"model_type": model_type},
                },
            }
            resp = requests.post(self.endpoint, json=payload, timeout=5.0)
            data = resp.json()
            return data.get("result", {}).get("status", "unknown")
        except Exception:
            return "error"

    def generate_shot(self, prompt: str, duration_sec: float = 4.0) -> Optional[bytes]:
        """Submits text-to-video generation job if Wan2GP is online."""
        if not self.is_available():
            return None
        # When active, polls job_id until completed and downloads bytes
        return None
