"""Stable Diffusion WebUI & ComfyUI Adapter."""

import os
from typing import Optional
import requests


class StableDiffusionAdapter:
    """Interfaces with local Stable Diffusion WebUI (port 7860) or ComfyUI (port 8188)."""

    def __init__(self, host: str = "http://127.0.0.1:7860"):
        self.host = host.rstrip("/")

    def is_available(self) -> bool:
        """Checks if local WebUI is active."""
        try:
            resp = requests.get(f"{self.host}/sdapi/v1/options", timeout=1.5)
            return resp.status_code == 200
        except Exception:
            return False

    def generate_image(self, prompt: str, width: int = 1920, height: int = 1080) -> Optional[bytes]:
        """Submits prompt to SD WebUI if present."""
        if not self.is_available():
            return None
        try:
            payload = {
                "prompt": prompt,
                "steps": 20,
                "width": width,
                "height": height,
                "cfg_scale": 7.0,
            }
            resp = requests.post(f"{self.host}/sdapi/v1/txt2img", json=payload, timeout=60.0)
            if resp.status_code == 200:
                import base64
                data = resp.json()
                images = data.get("images", [])
                if images:
                    return base64.b64decode(images[0])
        except Exception:
            pass
        return None
