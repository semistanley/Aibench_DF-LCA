from __future__ import annotations

from typing import Any, Dict

from adapters.base import ModelAdapter


class LocalEchoAdapter(ModelAdapter):
    """
    Local reference adapter for development.
    It "generates" by echoing the prompt and parameters back.
    """

    async def generate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        prompt = payload.get("prompt", "")
        return {
            "text": f"[local-echo] {prompt}",
            "model": self.config.model,
            "provider": self.config.provider,
            "generation_params": self.config.generation_params,
        }

