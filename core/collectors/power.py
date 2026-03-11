from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class PowerSample:
    t_s: float
    watts: float | None
    extra: Dict[str, Any]
    method: str


class PowerMeter(ABC):
    """
    Abstract power meter interface.
    Implementations may use:
    - CPU-based estimation
    - External power meters
    - Hardware sensors / vendor SDKs
    """

    @abstractmethod
    async def start(self) -> None: ...

    @abstractmethod
    async def sample(self) -> PowerSample: ...

    @abstractmethod
    async def stop(self) -> None: ...


class ExternalMeterStub(PowerMeter):
    """
    Placeholder for external power meter integration.
    """

    def __init__(self, *, device: str | None = None):
        self.device = device

    async def start(self) -> None:
        return None

    async def sample(self) -> PowerSample:
        return PowerSample(
            t_s=time.time(),
            watts=None,
            extra={"device": self.device, "note": "external meter not configured"},
            method="external_meter_stub",
        )

    async def stop(self) -> None:
        return None


class SensorsStub(PowerMeter):
    """
    Placeholder for GPU/CPU sensor library integration (e.g., NVML, Intel RAPL).
    """

    def __init__(self, *, backend: str | None = None):
        self.backend = backend

    async def start(self) -> None:
        return None

    async def sample(self) -> PowerSample:
        return PowerSample(
            t_s=time.time(),
            watts=None,
            extra={"backend": self.backend, "note": "sensors backend not configured"},
            method="sensors_stub",
        )

    async def stop(self) -> None:
        return None

