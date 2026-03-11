from __future__ import annotations

from typing import Any, Dict

from core.schemas import EvaluationResult


def standardized_report(result: EvaluationResult) -> Dict[str, Any]:
    """
    Standardized machine-readable report.
    Keep it stable for downstream dashboards.
    """
    return {
        "run_id": result.run_id,
        "created_at": result.created_at.isoformat(),
        "task_name": result.task_name,
        "model": result.model.model,
        "provider": result.model.provider.value,
        "metrics": result.metrics.model_dump(),
        "tags": result.tags,
        "artifacts": [a.model_dump() for a in result.artifacts],
    }


def report_markdown(result: EvaluationResult) -> str:
    m = result.metrics
    derived = (m.extra or {}).get("derived", {}) if hasattr(m, "extra") else {}
    per_unit = (m.extra or {}).get("per_unit_data", {}) if hasattr(m, "extra") else {}
    part2 = (m.extra or {}).get("df_lca_part2", {}) if hasattr(m, "extra") else {}
    part2_ind = (part2 or {}).get("indicators", {}) if isinstance(part2, dict) else {}

    lines = []
    lines.append(f"# DF-LCA Evaluation Report\n")
    lines.append(f"- run_id: `{result.run_id}`\n")
    lines.append(f"- task: `{result.task_name}`\n")
    lines.append(f"- model: `{result.model.provider.value}:{result.model.model}`\n")
    lines.append("\n## Performance\n")
    lines.append(f"- latency_ms: {m.performance.latency_ms}\n")
    lines.append(f"- throughput_tokens_per_s: {m.performance.throughput_tokens_per_s}\n")
    lines.append(f"- accuracy: {m.performance.accuracy}\n")
    lines.append("\n## Energy\n")
    lines.append(f"- energy_joules: {m.energy.energy_joules}\n")
    lines.append(f"- average_power_watts: {m.energy.average_power_watts}\n")
    lines.append(f"- carbon_gco2e: {m.energy.carbon_gco2e}\n")
    lines.append(f"- notes: {m.energy.notes}\n")
    lines.append("\n## Value\n")
    lines.append(f"- cost_usd: {m.value.cost_usd}\n")
    lines.append(f"- roi: {m.value.roi}\n")
    lines.append(f"- sustainability_index: {m.value.sustainability_index}\n")
    lines.append(f"- quality_score: {m.value.quality_score}\n")
    lines.append("\n## Normalized (unit data)\n")
    lines.append(f"- latency_ms_per_kb: {per_unit.get('latency_ms_per_kb')}\n")
    lines.append(f"- energy_j_per_kb: {per_unit.get('energy_j_per_kb')}\n")
    lines.append("\n## Derived indicators (estimates)\n")
    lines.append(f"- mips_est: {derived.get('mips_est')}\n")
    lines.append(f"- flops_per_s_est: {derived.get('flops_per_s_est')}\n")
    lines.append(f"- effort_rate_j_per_byte: {derived.get('effort_rate_j_per_byte')}\n")

    if part2_ind:
        lines.append("\n## DF-LCA Part 2 standardized indicators (per unit data)\n")
        lines.append(f"- reference_doi: {((part2.get('paper') or {}).get('doi'))}\n")
        for k, v in part2_ind.items():
            lines.append(f"- {k}: {v}\n")
    return "".join(lines)

