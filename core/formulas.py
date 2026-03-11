from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass(frozen=True)
class FormulaAssumptions:
    """
    Assumptions / defaults used when direct metrics are unavailable.

    Part 2 paper: indicators are computed from measurable metrics m(t) over time dimension T
    and standardized by data dimension D (output data volume).
    """

    ipc_estimate: float = 1.0
    flops_per_cycle_estimate: float = 4.0
    carbon_intensity_gco2e_per_kwh: float = 475.0  # m_c in Eq. (12); should be region/time specific


def joules_to_kwh(j: float) -> float:
    return j / 3_600_000.0


def carbon_gco2e_from_energy_joules(
    energy_joules: float | None, *, assumptions: FormulaAssumptions = FormulaAssumptions()
) -> float | None:
    """
    Part 2 Eq. (12): I_CE = m_c * I_EC
    Here we compute absolute CO2e from absolute energy (J) using m_c (gCO2e/kWh).
    """
    if energy_joules is None:
        return None
    return joules_to_kwh(energy_joules) * assumptions.carbon_intensity_gco2e_per_kwh


def mips_estimate(
    *, cpu_freq_mhz: float | None, cpu_utilization: float | None, assumptions: FormulaAssumptions = FormulaAssumptions()
) -> float | None:
    """
    Estimate MIPS metric m_MIPS (paper Eq. (5) uses m_MIPS from benchmark/spec DB).
    This is a best-effort estimate from frequency and utilization:
      m_MIPS ~= cycles/s * IPC * util / 1e6
    """
    if cpu_freq_mhz is None or cpu_utilization is None:
        return None
    cycles_per_s = cpu_freq_mhz * 1_000_000.0
    return (cycles_per_s * assumptions.ipc_estimate * max(0.0, min(1.0, cpu_utilization))) / 1_000_000.0


def flops_per_s_estimate(
    *, cpu_freq_mhz: float | None, cpu_utilization: float | None, assumptions: FormulaAssumptions = FormulaAssumptions()
) -> float | None:
    """
    Estimate FLOPS metric m_FLOPS(t) (paper Eq. (6)).
    FLOPs/s ~= cycles/s * flops_per_cycle * util
    """
    if cpu_freq_mhz is None or cpu_utilization is None:
        return None
    cycles_per_s = cpu_freq_mhz * 1_000_000.0
    return cycles_per_s * assumptions.flops_per_cycle_estimate * max(0.0, min(1.0, cpu_utilization))


def indicator_mips_per_data(*, m_mips: float | None, t_s: float, d_bytes: int) -> float | None:
    """
    Part 2 Eq. (5): I_MI = m_MIPS * T / D
    """
    if m_mips is None or t_s <= 0 or d_bytes <= 0:
        return None
    return (m_mips * t_s) / float(d_bytes)


def indicator_flops_per_data(*, flops_per_s_samples: Sequence[float], dt_s: Sequence[float], d_bytes: int) -> float | None:
    """
    Part 2 Eq. (6): I_FO = ( ∫_0^T m_FLOPS(t) dt ) / D
    Discrete approximation: sum(flops_i * dt_i) / D
    """
    if d_bytes <= 0 or not flops_per_s_samples or not dt_s or len(flops_per_s_samples) != len(dt_s):
        return None
    total = 0.0
    for f, dt in zip(flops_per_s_samples, dt_s):
        total += float(f) * float(max(0.0, dt))
    return total / float(d_bytes)


def indicator_data_speed(*, d_bytes: int, t_s: float) -> float | None:
    """
    Part 2 Eq. (7): I_DS = m_DV / T (average data generation speed)
    """
    if d_bytes <= 0 or t_s <= 0:
        return None
    return float(d_bytes) / float(t_s)


def indicator_energy_consumption_per_data(*, energy_joules: float | None, d_bytes: int) -> float | None:
    """
    Part 2 Eq. (11): I_EC = ( ∫_0^T p(t) dt ) / D
    If energy_joules is available, ∫ p(t)dt = energy (J).
    """
    if energy_joules is None or d_bytes <= 0:
        return None
    return float(energy_joules) / float(d_bytes)


def indicator_carbon_emission_per_data(
    *, energy_joules: float | None, d_bytes: int, assumptions: FormulaAssumptions = FormulaAssumptions()
) -> float | None:
    """
    Part 2 Eq. (12): I_CE = m_c * I_EC
    Returns gCO2e per byte.
    """
    if energy_joules is None or d_bytes <= 0:
        return None
    g = carbon_gco2e_from_energy_joules(energy_joules, assumptions=assumptions)
    if g is None:
        return None
    return g / float(d_bytes)


def indicator_cost_per_data(*, cost: float | None, d_bytes: int) -> float | None:
    """
    Part 2 Eq. (13): I_CPD = m_Cost / D
    """
    if cost is None or d_bytes <= 0:
        return None
    return float(cost) / float(d_bytes)


def indicator_profit_per_data(*, cost: float | None, roi: float | None, d_bytes: int) -> float | None:
    """
    Part 2 Eq. (14): I_PPD = m_Profit / D = (m_Cost * m_ROI) / D
    """
    if cost is None or roi is None or d_bytes <= 0:
        return None
    return (float(cost) * float(roi)) / float(d_bytes)


def effort_rate(
    *,
    compute_util_samples: Sequence[float],
    storage_util_samples: Sequence[float],
    dt_s: Sequence[float],
    compute_power_w: float | None,
    storage_power_w: float | None,
    total_power_w: float | None,
    d_bytes: int,
) -> float | None:
    """
    Part 2 Eq. (8): Effort rate (unit data Effort indicator).
      I_EffortRate = ( ∫ (a*f(m_c(t)) + b*f(m_s(t))) dt ) / D
      where a=m_cp/m_pa, b=m_sp/m_pa
    This implementation assumes compute/storage utilization are already scaled to [0,1].
    """
    if d_bytes <= 0 or not dt_s:
        return None
    if (
        compute_power_w is None
        or storage_power_w is None
        or total_power_w is None
        or total_power_w <= 0
        or len(compute_util_samples) != len(dt_s)
        or len(storage_util_samples) != len(dt_s)
    ):
        return None
    a = float(compute_power_w) / float(total_power_w)
    b = float(storage_power_w) / float(total_power_w)
    total = 0.0
    for cu, su, dt in zip(compute_util_samples, storage_util_samples, dt_s):
        total += (a * float(cu) + b * float(su)) * float(max(0.0, dt))
    return total / float(d_bytes)

