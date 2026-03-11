from __future__ import annotations

import time

try:
    import psutil  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    psutil = None  # type: ignore

from core.collectors.base import Collector, CollectorSnapshot
from core.collectors.power import ExternalMeterStub, PowerMeter, PowerSample, SensorsStub


class CpuEstimatePowerMeter(PowerMeter):
    """
    Default (always-available) power estimator based on CPU utilization.
    """

    def __init__(self, *, baseline_watts: float = 15.0):
        self.baseline_watts = baseline_watts

    async def start(self) -> None:
        if psutil is not None:
            psutil.cpu_percent(interval=None)

    async def sample(self) -> PowerSample:
        now = time.time()
        if psutil is None:
            return PowerSample(t_s=now, watts=None, extra={"psutil": "missing"}, method="cpu_estimate_unavailable")
        cpu_util = (psutil.cpu_percent(interval=None) or 0.0) / 100.0
        watts = self.baseline_watts * max(0.05, min(1.0, cpu_util))
        return PowerSample(
            t_s=now,
            watts=watts,
            extra={"cpu_utilization": cpu_util, "baseline_watts": self.baseline_watts},
            method="cpu_estimate",
        )

    async def stop(self) -> None:
        return None


class EnergyCollector(Collector):
    """
    Pluggable energy collector.

    Integrates instantaneous power (W) over time to energy (J).
    """

    def __init__(self, meter: PowerMeter):
        self.meter = meter
        self._last_t: float | None = None
        self._acc_energy_j: float = 0.0
        self._last_power: PowerSample | None = None

    @staticmethod
    def from_method(method: str) -> "EnergyCollector":
        if method == "cpu_estimate":
            return EnergyCollector(CpuEstimatePowerMeter())
        if method == "external_meter":
            return EnergyCollector(ExternalMeterStub())
        if method == "sensors":
            return EnergyCollector(SensorsStub())
        return EnergyCollector(CpuEstimatePowerMeter())

    async def start(self) -> None:
        self._last_t = time.time()
        await self.meter.start()

    async def sample(self) -> CollectorSnapshot:
        now = time.time()
        if self._last_t is None:
            self._last_t = now
        dt = max(0.0, now - self._last_t)
        self._last_t = now

        ps = await self.meter.sample()
        self._last_power = ps

        if ps.watts is not None:
            self._acc_energy_j += float(ps.watts) * dt

        values = {
            "energy_joules": self._acc_energy_j if self._acc_energy_j > 0 else None,
            "avg_power_watts": ps.watts,
            "method": ps.method,
            **(ps.extra or {}),
        }
        return CollectorSnapshot(t_s=now, values=values)

    async def stop(self) -> None:
        await self.meter.stop()

