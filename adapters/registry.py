from __future__ import annotations

from core.schemas import ModelConfig, ModelProvider

from adapters.base import ModelAdapter
from adapters.huggingface import HuggingFaceAdapter
from adapters.local import LocalEchoAdapter
from adapters.openai import OpenAIAdapter


def create_adapter(config: ModelConfig) -> ModelAdapter:
    if config.provider == ModelProvider.openai:
        return OpenAIAdapter(config)
    if config.provider == ModelProvider.huggingface:
        return HuggingFaceAdapter(config)
    if config.provider == ModelProvider.local:
        return LocalEchoAdapter(config)
    raise ValueError(f"Unknown provider: {config.provider}")

