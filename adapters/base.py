from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from core.schemas import ModelConfig


class ModelAdapter(ABC):
    def __init__(self, config: ModelConfig):
        self.config = config

    @abstractmethod
    async def generate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a model response.

        payload is task-dependent but should generally include:
          - "prompt": str
          - optional task-specific fields
        Returns a dict that is serializable and stored as output_json.
        """

