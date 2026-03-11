from __future__ import annotations

import time
import uuid
from typing import Any, Dict

try:
    import psutil  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    psutil = None  # type: ignore

from adapters.registry import create_adapter
from core.dpu import DPUNode, DPUProcess
from core.functional_unit import UnitData
from core.schemas import Artifact, EvaluationRequest, EvaluationResult, RunMetrics, utc_now


def _estimate_energy_joules(elapsed_s: float) -> float | None:
    """
    Placeholder energy estimation.
    Real DF-LCA energy accounting should integrate OS/driver counters or external meters.
    """
    try:
        if psutil is None:
            return None
        # very rough: CPU utilization * TDP-esque 15W baseline; purely for scaffold
        cpu_pct = psutil.cpu_percent(interval=None) / 100.0
        watts = 15.0 * max(0.05, min(1.0, cpu_pct))
        return watts * elapsed_s
    except Exception:
        return None


def _count_tokens_placeholder(text: str) -> int:
    # Placeholder: approximate tokens by whitespace split.
    return len((text or "").split())

def _hardware_context() -> Dict[str, Any]:
    if psutil is None:
        return {"psutil": "missing"}
    try:
        return {
            "cpu_count_logical": psutil.cpu_count(logical=True),
            "cpu_count_physical": psutil.cpu_count(logical=False),
            "memory_total_bytes": getattr(psutil.virtual_memory(), "total", None),
        }
    except Exception:
        return {"psutil": "error"}


async def run_evaluation(req: EvaluationRequest) -> EvaluationResult:
    run_id = uuid.uuid4().hex
    created_at = utc_now()

    adapter = create_adapter(req.model)

    prompt = req.input.get("prompt")
    if not isinstance(prompt, str):
        # Keep it simple for the scaffold; tasks can define their own input schema later.
        prompt = str(req.input)

    t0 = time.perf_counter()
    output = await adapter.generate({"prompt": prompt, "input": req.input})
    elapsed_s = time.perf_counter() - t0

    output_text = str(output.get("text", "")) if isinstance(output, dict) else str(output)

    metrics = RunMetrics()
    metrics.performance.latency_ms = elapsed_s * 1000.0
    metrics.performance.input_tokens = _count_tokens_placeholder(prompt)
    metrics.performance.output_tokens = _count_tokens_placeholder(output_text)
    if elapsed_s > 0:
        metrics.performance.throughput_tokens_per_s = (metrics.performance.output_tokens or 0) / elapsed_s

    metrics.energy.energy_joules = _estimate_energy_joules(elapsed_s)
    metrics.energy.notes = "placeholder_estimate"
    metrics.energy.carbon_gco2e = None

    # Value dimension placeholders; cost/carbon/quality are task+provider specific.
    metrics.value.cost_usd = None
    metrics.value.quality_score = None
    metrics.value.roi = None
    metrics.value.sustainability_index = None
    metrics.performance.accuracy = None

    unit = UnitData(
        input_bytes=len(prompt.encode("utf-8", errors="ignore")),
        output_bytes=len(output_text.encode("utf-8", errors="ignore")),
        input_tokens=metrics.performance.input_tokens or 0,
        output_tokens=metrics.performance.output_tokens or 0,
    )
    # Standardize indicators by allocating them to unit data (paper: DF-LCA functional unit = unit data)
    metrics.extra["per_unit_data"] = {
        "latency_ms_per_kb": (metrics.performance.latency_ms / (unit.total_bytes / 1024.0))
        if unit.total_bytes > 0 and metrics.performance.latency_ms is not None
        else None,
        "energy_j_per_kb": (metrics.energy.energy_joules / (unit.total_bytes / 1024.0))
        if unit.total_bytes > 0 and metrics.energy.energy_joules is not None
        else None,
    }

    dpu = DPUNode(
        id=run_id,
        name="model_inference",
        type=f"{req.model.provider.value}:{req.model.model}",
        inputs=[{"kind": "prompt", "bytes": unit.input_bytes, "tokens_est": unit.input_tokens}],
        output={"kind": "text", "bytes": unit.output_bytes, "tokens_est": unit.output_tokens},
        processes=[DPUProcess.computing, DPUProcess.create],
        indicators={
            "performance": metrics.performance.model_dump(),
            "energy": metrics.energy.model_dump(),
            "value": metrics.value.model_dump(),
        },
        context=_hardware_context(),
        subnodes=[],
    )

    return EvaluationResult(
        run_id=run_id,
        created_at=created_at,
        task_name=req.task_name,
        model=req.model,
        input=req.input,
        output=output if isinstance(output, dict) else {"raw": output},
        metrics=metrics,
        artifacts=[
            Artifact(kind="prompt", payload={"prompt": prompt}),
            Artifact(
                kind="meta",
                payload={
                    "df_lca": {
                        "paper": {
                            "title": "How to assess the digitization and digital effort: A framework for Digitization Footprint (Part 1)",
                            "doi": "10.1016/j.compag.2024.109875",
                        },
                        "functional_unit": "unit_data",
                    },
                    "unit_data": {
                        "input_bytes": unit.input_bytes,
                        "output_bytes": unit.output_bytes,
                        "input_tokens_est": unit.input_tokens,
                        "output_tokens_est": unit.output_tokens,
                    },
                    "dpu": dpu.model_dump(),
                },
            ),
        ],
        tags=req.tags,
    )

