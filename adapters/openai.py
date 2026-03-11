from __future__ import annotations

import os
from typing import Any, Dict

import httpx

from adapters.base import ModelAdapter


class OpenAIAdapter(ModelAdapter):
    """
    Minimal OpenAI-compatible adapter.

    Note: This is a skeleton; you'll likely want to expand it to support chat completions,
    streaming, tool calls, robust error handling, and token accounting.
    """

    async def generate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        base_url = (self.config.base_url or "https://api.openai.com").rstrip("/")
        api_key = os.getenv(self.config.api_key_env or "OPENAI_API_KEY", "")
        if not api_key:
            return {
                "error": "Missing API key",
                "hint": f"Set env var {self.config.api_key_env or 'OPENAI_API_KEY'}",
            }

        prompt = payload.get("prompt", "")
        req = {
            "model": self.config.model,
            "input": prompt,
            **(self.config.generation_params or {}),
        }

        # OpenAI "Responses API" style endpoint (skeleton)
        url = f"{base_url}/v1/responses"
        headers = {"Authorization": f"Bearer {api_key}"}
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(url, headers=headers, json=req)
            r.raise_for_status()
            data = r.json()

        # Normalize to our output dict
        text = ""
        for item in data.get("output", []) or []:
            for c in item.get("content", []) or []:
                if c.get("type") == "output_text":
                    text += c.get("text", "")
        return {"text": text, "raw": data}

