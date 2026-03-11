from __future__ import annotations

import time

try:
    import psutil  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    psutil = None  # type: ignore

from core.collectors.base import Collector, CollectorSnapshot


class SystemPerfCollector(Collector):
    """
    Collects coarse host-level performance signals.
    """

    async def start(self) -> None:
        if psutil is not None:
            # prime cpu percent measurement
            psutil.cpu_percent(interval=None)

    async def sample(self) -> CollectorSnapshot:
        now = time.time()
        if psutil is None:
            return CollectorSnapshot(t_s=now, values={"psutil": "missing"})

        freq = psutil.cpu_freq()
        vm = psutil.virtual_memory()
        values = {
            "cpu_percent": psutil.cpu_percent(interval=None),
            "cpu_freq_mhz": getattr(freq, "current", None),
            "mem_used_bytes": getattr(vm, "used", None),
            "mem_total_bytes": getattr(vm, "total", None),
        }
        return CollectorSnapshot(t_s=now, values=values)

    async def stop(self) -> None:
        return None

