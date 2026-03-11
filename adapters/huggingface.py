from __future__ import annotations

import os
from typing import Any, Dict

import httpx

from adapters.base import ModelAdapter


class HuggingFaceAdapter(ModelAdapter):
    """
    Minimal Hugging Face Inference API adapter (skeleton).
    """

    async def generate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        api_key = os.getenv(self.config.api_key_env or "HF_API_TOKEN", "")
        if not api_key:
            return {
                "error": "Missing HF API token",
                "hint": f"Set env var {self.config.api_key_env or 'HF_API_TOKEN'}",
            }

        base_url = (self.config.base_url or "https://api-inference.huggingface.co").rstrip("/")
        prompt = payload.get("prompt", "")
        url = f"{base_url}/models/{self.config.model}"
        headers = {"Authorization": f"Bearer {api_key}"}
        req = {"inputs": prompt, "parameters": self.config.generation_params or {}}
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(url, headers=headers, json=req)
            r.raise_for_status()
            data = r.json()

        # Many HF models return a list of dicts with generated_text
        text = ""
        if isinstance(data, list) and data and isinstance(data[0], dict):
            text = data[0].get("generated_text", "") or ""
        return {"text": text, "raw": data}

