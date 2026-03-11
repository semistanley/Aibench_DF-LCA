from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from adapters.registry import create_adapter
from core.collectors.energy import EnergyCollector
from core.collectors.system_perf import SystemPerfCollector
from core.dpu import DPUNode, DPUProcess
from core.formulas import (
    FormulaAssumptions,
    carbon_gco2e_from_energy_joules,
    effort_rate,
    flops_per_s_estimate,
    indicator_carbon_emission_per_data,
    indicator_cost_per_data,
    indicator_data_speed,
    indicator_energy_consumption_per_data,
    indicator_flops_per_data,
    indicator_mips_per_data,
    indicator_profit_per_data,
    mips_estimate,
)
from core.functional_unit import UnitData
from core.schemas import Artifact, EvaluationRequest, EvaluationResult, RunMetrics, utc_now


@dataclass
class EngineConfig:
    sample_interval_s: float = 0.25
    formula_assumptions: FormulaAssumptions = FormulaAssumptions()


async def evaluate_dpu(req: EvaluationRequest, *, cfg: EngineConfig = EngineConfig()) -> EvaluationResult:
    """
    DPU evaluation engine:
    - start real-time collectors
    - execute model adapter generation
    - stop collectors and aggregate
    - compute derived indicators (MIPS/FLOPs/Effort rate/CO2e) with explicit assumptions
    - emit standardized artifacts
    """
    run_id = __import__("uuid").uuid4().hex
    created_at = utc_now()

    adapter = create_adapter(req.model)
    prompt = req.input.get("prompt")
    if not isinstance(prompt, str):
        prompt = str(req.input)

    perf_col = SystemPerfCollector()
    energy_col = EnergyCollector.from_method(req.options.energy_method.value)

    await perf_col.start()
    await energy_col.start()

    perf_samples: List[Dict[str, Any]] = []
    energy_samples: List[Dict[str, Any]] = []
    stop_sampling = asyncio.Event()

    # Ensure at least one snapshot exists even for very fast tasks.
    ps0 = await perf_col.sample()
    es0 = await energy_col.sample()
    perf_samples.append({"t_s": ps0.t_s, **ps0.values})
    energy_samples.append({"t_s": es0.t_s, **es0.values})

    async def sampler():
        while not stop_sampling.is_set():
            ps = await perf_col.sample()
            es = await energy_col.sample()
            perf_samples.append({"t_s": ps.t_s, **ps.values})
            energy_samples.append({"t_s": es.t_s, **es.values})
            await asyncio.sleep(req.options.sample_interval_s)

    sampling_task = asyncio.create_task(sampler())

    t0 = time.perf_counter()
    output = await adapter.generate({"prompt": prompt, "input": req.input})
    elapsed_s = time.perf_counter() - t0

    stop_sampling.set()
    await sampling_task
    await perf_col.stop()
    await energy_col.stop()

    output_text = str(output.get("text", "")) if isinstance(output, dict) else str(output)

    metrics = RunMetrics()
    metrics.performance.latency_ms = elapsed_s * 1000.0
    metrics.performance.input_tokens = len((prompt or "").split())
    metrics.performance.output_tokens = len((output_text or "").split())
    metrics.performance.throughput_tokens_per_s = (
        (metrics.performance.output_tokens or 0) / elapsed_s if elapsed_s > 0 else None
    )
    metrics.performance.accuracy = None

    # Aggregate energy (use last available estimate if present)
    energy_j = None
    avg_power = None
    energy_method = None
    if energy_samples:
        last = energy_samples[-1]
        energy_j = last.get("energy_joules")
        avg_power = last.get("avg_power_watts")
        energy_method = last.get("method")

    metrics.energy.energy_joules = energy_j
    metrics.energy.average_power_watts = avg_power
    metrics.energy.notes = energy_method or "unknown"
    metrics.energy.carbon_gco2e = carbon_gco2e_from_energy_joules(energy_j, assumptions=cfg.formula_assumptions)

    metrics.value.cost_usd = None
    metrics.value.quality_score = None
    metrics.value.roi = None
    metrics.value.sustainability_index = None

    unit = UnitData(
        input_bytes=len(prompt.encode("utf-8", errors="ignore")),
        output_bytes=len(output_text.encode("utf-8", errors="ignore")),
        input_tokens=metrics.performance.input_tokens or 0,
        output_tokens=metrics.performance.output_tokens or 0,
    )

    # Derived indicators based on perf collector (take last sample)
    last_perf = perf_samples[-1] if perf_samples else {}
    cpu_util = (last_perf.get("cpu_percent") or 0.0) / 100.0 if "cpu_percent" in last_perf else None
    cpu_freq_mhz = last_perf.get("cpu_freq_mhz")

    # Build discrete samples for Eq. (6)/(8)
    dt_s: List[float] = []
    cpu_util_s: List[float] = []
    mem_util_s: List[float] = []
    flops_s: List[float] = []
    for i in range(1, len(perf_samples)):
        t0 = float(perf_samples[i - 1].get("t_s", 0.0))
        t1 = float(perf_samples[i].get("t_s", 0.0))
        dt = max(0.0, t1 - t0)
        dt_s.append(dt)

        cpu_u = (perf_samples[i].get("cpu_percent") or 0.0) / 100.0
        cpu_util_s.append(max(0.0, min(1.0, float(cpu_u))))

        mem_used = perf_samples[i].get("mem_used_bytes")
        mem_total = perf_samples[i].get("mem_total_bytes")
        mem_u = (float(mem_used) / float(mem_total)) if mem_used and mem_total else 0.0
        mem_util_s.append(max(0.0, min(1.0, float(mem_u))))

        f = flops_per_s_estimate(
            cpu_freq_mhz=perf_samples[i].get("cpu_freq_mhz"),
            cpu_utilization=cpu_util_s[-1],
            assumptions=cfg.formula_assumptions,
        )
        flops_s.append(float(f) if f is not None else 0.0)

    # Part 2 Eq. (5): I_MI = m_MIPS * T / D
    m_mips = mips_estimate(cpu_freq_mhz=cpu_freq_mhz, cpu_utilization=cpu_util, assumptions=cfg.formula_assumptions)
    i_mi = indicator_mips_per_data(m_mips=m_mips, t_s=elapsed_s, d_bytes=unit.total_bytes)

    # Part 2 Eq. (6): I_FO = ∫ FLOPS(t) dt / D (discrete sum)
    i_fo = indicator_flops_per_data(flops_per_s_samples=flops_s, dt_s=dt_s, d_bytes=unit.total_bytes)

    # Part 2 Eq. (7): I_DS = DV / T
    i_ds = indicator_data_speed(d_bytes=unit.total_bytes, t_s=elapsed_s)

    # Part 2 Eq. (11)/(12): energy/carbon per data
    i_ec = indicator_energy_consumption_per_data(energy_joules=energy_j, d_bytes=unit.total_bytes)
    i_ce = indicator_carbon_emission_per_data(
        energy_joules=energy_j, d_bytes=unit.total_bytes, assumptions=cfg.formula_assumptions
    )

    # Part 2 Eq. (8): Effort rate (needs compute/storage util + power fractions).
    # We approximate:
    #  - compute util: cpu utilization
    #  - storage util: memory utilization
    #  - power split: not yet measured -> currently returns None (by design, to avoid fake precision)
    i_eff = effort_rate(
        compute_util_samples=cpu_util_s,
        storage_util_samples=mem_util_s,
        dt_s=dt_s,
        compute_power_w=None,
        storage_power_w=None,
        total_power_w=avg_power,
        d_bytes=unit.total_bytes,
    )

    # Value indicators (Eq. 13/14) require cost + ROI
    i_cpd = indicator_cost_per_data(cost=metrics.value.cost_usd, d_bytes=unit.total_bytes)
    i_ppd = indicator_profit_per_data(cost=metrics.value.cost_usd, roi=metrics.value.roi, d_bytes=unit.total_bytes)

    metrics.extra["df_lca_part2"] = {
        "paper": {"doi": "10.1016/j.compag.2024.109206"},
        "indicators": {
            "I_MI_mips_per_byte": i_mi,
            "I_FO_flop_per_byte": i_fo,
            "I_DS_bytes_per_s": i_ds,
            "I_EC_j_per_byte": i_ec,
            "I_CE_gco2e_per_byte": i_ce,
            "I_EffortRate_per_byte": i_eff,
            "I_CPD_usd_per_byte": i_cpd,
            "I_PPD_usd_per_byte": i_ppd,
        },
        "assumptions": {
            "ipc_estimate": cfg.formula_assumptions.ipc_estimate,
            "flops_per_cycle_estimate": cfg.formula_assumptions.flops_per_cycle_estimate,
            "carbon_intensity_gco2e_per_kwh": cfg.formula_assumptions.carbon_intensity_gco2e_per_kwh,
            "effort_rate_note": "Eq(8) requires compute/storage power split; currently not measured so EffortRate may be null.",
        },
    }
    metrics.extra["samples"] = {"system_perf": perf_samples, "energy": energy_samples}
    metrics.extra["per_unit_data"] = {
        "latency_ms_per_kb": (metrics.performance.latency_ms / (unit.total_bytes / 1024.0))
        if unit.total_bytes > 0 and metrics.performance.latency_ms is not None
        else None,
        "energy_j_per_kb": (energy_j / (unit.total_bytes / 1024.0)) if unit.total_bytes > 0 and energy_j else None,
    }

    dpu = DPUNode(
        id=run_id,
        name="model_inference",
        type=f"{req.model.provider.value}:{req.model.model}",
        inputs=[{"kind": "prompt", "bytes": unit.input_bytes, "tokens_est": unit.input_tokens}],
        output={"kind": "text", "bytes": unit.output_bytes, "tokens_est": unit.output_tokens},
        processes=[DPUProcess.computing, DPUProcess.create, DPUProcess.transfer],
        indicators={"performance": metrics.performance.model_dump(), "energy": metrics.energy.model_dump(), "value": metrics.value.model_dump()},
        context={"host": last_perf},
        subnodes=[],
    )

    artifacts = [
        Artifact(kind="prompt", payload={"prompt": prompt}),
        Artifact(kind="output", payload={"text": output_text}),
        Artifact(
            kind="meta",
            payload={
                "df_lca": {
                    "functional_unit": "unit_data",
                    "run": {"sample_interval_s": req.options.sample_interval_s},
                    "options": req.options.model_dump(mode="json"),
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
    ]

    return EvaluationResult(
        run_id=run_id,
        created_at=created_at,
        task_name=req.task_name,
        model=req.model,
        input=req.input,
        output=output if isinstance(output, dict) else {"raw": output},
        metrics=metrics,
        artifacts=artifacts,
        tags=req.tags,
    )

