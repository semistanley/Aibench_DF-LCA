from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class CollectorSnapshot:
    t_s: float
    values: Dict[str, Any]


class Collector(ABC):
    """
    Real-time collectors support start/stop and periodic sampling.
    """

    @abstractmethod
    async def start(self) -> None: ...

    @abstractmethod
    async def sample(self) -> CollectorSnapshot: ...

    @abstractmethod
    async def stop(self) -> None: ...

