from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.schemas import ModelConfig, ModelProvider


@dataclass
class ModelRegistry:
    """
    Simple in-memory registry for models/endpoints used across CLI, API and UI.

    model_config example (user-facing schema):
    {
        "name": "llama-3-8b",
        "type": "huggingface" | "api" | "local",
        "endpoint": "http://localhost:8000" | "hf://meta-llama/Llama-3-8b",
        "parameters": {
            "max_tokens": 2048,
            "temperature": 0.7
        }
    }
    """

    _models: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def register_model(self, model_config: Dict[str, Any]) -> None:
        name = model_config.get("name")
        if not name:
            raise ValueError("model_config must contain 'name'")
        self._models[name] = model_config

    def get(self, name: str) -> Optional[Dict[str, Any]]:
        return self._models.get(name)

    def list_all(self) -> List[Dict[str, Any]]:
        return list(self._models.values())

    def list_by_type(self, type_: str) -> List[Dict[str, Any]]:
        return [m for m in self._models.values() if m.get("type") == type_]

    def list_names_by_provider(self, provider: ModelProvider) -> List[str]:
        out: List[str] = []
        for name, cfg in self._models.items():
            t = cfg.get("type")
            if t == "local" and provider == ModelProvider.local:
                out.append(name)
            elif t == "huggingface" and provider == ModelProvider.huggingface:
                out.append(name)
            elif t == "api" and provider == ModelProvider.openai:
                out.append(name)
        return sorted(out)

    def to_model_config(self, name: str) -> ModelConfig:
        cfg = self.get(name)
        if not cfg:
            raise KeyError(f"Unknown model '{name}'")

        t = cfg.get("type")
        if t == "local":
            provider = ModelProvider.local
        elif t == "huggingface":
            provider = ModelProvider.huggingface
        else:
            # generic API; default to OpenAI-compatible
            provider = ModelProvider.openai

        params = cfg.get("parameters") or {}
        return ModelConfig(
            provider=provider,
            model=name,
            base_url=cfg.get("endpoint"),
            generation_params=params,
        )


# Global registry instance with some defaults
registry = ModelRegistry()

registry.register_model(
    {
        "name": "echo",
        "type": "local",
        "endpoint": None,
        "parameters": {"max_tokens": 256, "temperature": 0.0},
    }
)

registry.register_model(
    {
        "name": "gpt-4.1",
        "type": "api",
        "endpoint": "https://api.openai.com/v1/responses",
        "parameters": {"max_tokens": 2048, "temperature": 0.7},
    }
)

registry.register_model(
    {
        "name": "gpt-4o-mini",
        "type": "api",
        "endpoint": "https://api.openai.com/v1/responses",
        "parameters": {"max_tokens": 2048, "temperature": 0.3},
    }
)

registry.register_model(
    {
        "name": "meta-llama/Meta-Llama-3-8B-Instruct",
        "type": "huggingface",
        "endpoint": "hf://meta-llama/Meta-Llama-3-8B-Instruct",
        "parameters": {"max_tokens": 2048, "temperature": 0.7},
    }
)

