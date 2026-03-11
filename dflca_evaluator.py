"""DF-LCA Core Evaluator - encapsulates the 5 key evaluation dimensions."""
from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List, Optional

from adapters.registry import create_adapter
from core.collectors.energy import EnergyCollector
from core.collectors.system_perf import SystemPerfCollector
from core.formulas import (
    FormulaAssumptions,
    carbon_gco2e_from_energy_joules,
    flops_per_s_estimate,
    indicator_data_speed,
    indicator_energy_consumption_per_data,
    indicator_flops_per_data,
    indicator_mips_per_data,
    mips_estimate,
)
from core.schemas import (
    EnergyCollectionMethod,
    EvaluationOptions,
    EvaluationRequest,
    ModelConfig,
    ModelProvider,
    RunMetrics,
)


class DFLCAEvaluator:
    """
    DF-LCA Core Evaluator - encapsulates 5 key evaluation dimensions:
    1. Task Performance (任务性能)
    2. Computational Efficiency (计算效率)
    3. Energy Consumption (能耗分析)
    4. Resource Utilization (资源利用率)
    5. Carbon Footprint (碳排放估算)
    """

    def __init__(
        self,
        *,
        energy_method: EnergyCollectionMethod = EnergyCollectionMethod.cpu_estimate,
        sample_interval_s: float = 0.25,
        formula_assumptions: FormulaAssumptions = FormulaAssumptions(),
    ):
        """
        Initialize the DF-LCA evaluator.

        Args:
            energy_method: Method for energy collection
            sample_interval_s: Sampling interval in seconds
            formula_assumptions: Assumptions for formula calculations
        """
        self.energy_method = energy_method
        self.sample_interval_s = sample_interval_s
        self.assumptions = formula_assumptions

    async def evaluate(
        self,
        model: ModelConfig | Dict[str, Any],
        tasks: List[Dict[str, Any]] | Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Evaluate model on tasks using DF-LCA framework.

        Args:
            model: Model configuration (ModelConfig or dict with provider/model)
            tasks: List of tasks or single task dict with 'prompt' or 'input'

        Returns:
            Dictionary with 5 core dimensions:
            - performance: Task performance metrics
            - efficiency: Computational efficiency metrics
            - energy: Energy consumption metrics
            - carbon: Carbon footprint estimates
            - resource: Resource utilization metrics
        """
        # Normalize model input
        if isinstance(model, dict):
            model_config = ModelConfig(
                provider=ModelProvider(model.get("provider", "local")),
                model=model.get("model", "echo"),
                base_url=model.get("endpoint"),
                generation_params=model.get("parameters", {}),
            )
        else:
            model_config = model

        # Normalize tasks input
        if isinstance(tasks, dict):
            task_list = [tasks]
        else:
            task_list = tasks

        # Run evaluation for each task and aggregate
        all_metrics = []
        for task in task_list:
            task_metrics = await self._evaluate_single_task(model_config, task)
            all_metrics.append(task_metrics)

        # Aggregate metrics across tasks
        return self._aggregate_metrics(all_metrics)

    async def _evaluate_single_task(self, model_config: ModelConfig, task: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a single task."""
        prompt = task.get("prompt") or task.get("input", {}).get("prompt", "hello")
        if not isinstance(prompt, str):
            prompt = str(prompt)

        adapter = create_adapter(model_config)

        # Start collectors
        perf_col = SystemPerfCollector()
        energy_col = EnergyCollector.from_method(self.energy_method.value)

        await perf_col.start()
        await energy_col.start()

        perf_samples: List[Dict[str, Any]] = []
        energy_samples: List[Dict[str, Any]] = []
        stop_sampling = asyncio.Event()

        # Initial snapshot
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
                await asyncio.sleep(self.sample_interval_s)

        sampling_task = asyncio.create_task(sampler())

        # Execute model inference
        t0 = time.perf_counter()
        output = await adapter.generate({"prompt": prompt, "input": task})
        elapsed_s = time.perf_counter() - t0

        stop_sampling.set()
        await sampling_task
        await perf_col.stop()
        await energy_col.stop()

        output_text = str(output.get("text", "")) if isinstance(output, dict) else str(output)
        output_bytes = len(output_text.encode("utf-8"))
        input_bytes = len(prompt.encode("utf-8"))

        # Compute metrics for each dimension
        metrics = {
            "performance": self.measure_performance(prompt, output_text, elapsed_s),
            "efficiency": self.measure_efficiency(perf_samples, elapsed_s, output_bytes),
            "energy": await self.measure_energy_consumption(energy_samples, elapsed_s, output_bytes),
            "carbon": await self.estimate_carbon_footprint(energy_samples, elapsed_s, output_bytes),
            "resource": self.monitor_resource_usage(perf_samples, energy_samples),
        }

        return metrics

    def measure_performance(self, prompt: str, output_text: str, elapsed_s: float) -> Dict[str, Any]:
        """
        Measure task performance (任务性能).

        Returns:
            - latency_ms: Response latency
            - throughput_tokens_per_s: Token generation rate
            - input_tokens: Input token count (estimated)
            - output_tokens: Output token count (estimated)
            - accuracy: Task-specific accuracy (if applicable)
        """
        input_tokens = len(prompt.split())
        output_tokens = len(output_text.split())

        return {
            "latency_ms": elapsed_s * 1000.0,
            "throughput_tokens_per_s": output_tokens / elapsed_s if elapsed_s > 0 else None,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "accuracy": None,  # Task-specific accuracy should be computed separately
        }

    def measure_efficiency(self, perf_samples: List[Dict[str, Any]], elapsed_s: float, output_bytes: int) -> Dict[str, Any]:
        """
        Measure computational efficiency (计算效率).

        Returns:
            - mips_per_byte: MIPS per unit data (I_MI from Part 2 Eq. 5)
            - flops_per_byte: FLOPs per unit data (I_FO from Part 2 Eq. 6)
            - data_speed_bytes_per_s: Data generation speed (I_DS from Part 2 Eq. 7)
            - avg_cpu_utilization: Average CPU utilization
            - avg_cpu_freq_mhz: Average CPU frequency
        """
        if not perf_samples:
            return {
                "mips_per_byte": None,
                "flops_per_byte": None,
                "data_speed_bytes_per_s": None,
                "avg_cpu_utilization": None,
                "avg_cpu_freq_mhz": None,
            }

        # Aggregate CPU metrics
        cpu_utils = [s.get("cpu_utilization", 0) for s in perf_samples if s.get("cpu_utilization") is not None]
        cpu_freqs = [s.get("cpu_freq_mhz", 0) for s in perf_samples if s.get("cpu_freq_mhz") is not None]

        avg_cpu_util = sum(cpu_utils) / len(cpu_utils) if cpu_utils else None
        avg_cpu_freq = sum(cpu_freqs) / len(cpu_freqs) if cpu_freqs else None

        # Compute MIPS estimate
        m_mips = mips_estimate(
            cpu_freq_mhz=avg_cpu_freq,
            cpu_utilization=avg_cpu_util,
            assumptions=self.assumptions,
        )

        # Compute MIPS per data (I_MI)
        i_mi = indicator_mips_per_data(m_mips=m_mips, t_s=elapsed_s, d_bytes=output_bytes)

        # Compute FLOPs per second samples
        flops_samples = []
        dt_samples = []
        for i, s in enumerate(perf_samples):
            if i == 0:
                continue
            dt = s["t_s"] - perf_samples[i - 1]["t_s"]
            if dt > 0:
                flops_per_s = flops_per_s_estimate(
                    cpu_freq_mhz=s.get("cpu_freq_mhz"),
                    cpu_utilization=s.get("cpu_utilization"),
                    assumptions=self.assumptions,
                )
                if flops_per_s is not None:
                    flops_samples.append(flops_per_s)
                    dt_samples.append(dt)

        # Compute FLOPs per data (I_FO)
        i_fo = indicator_flops_per_data(
            flops_per_s_samples=flops_samples,
            dt_s=dt_samples,
            d_bytes=output_bytes,
        )

        # Compute data speed (I_DS)
        i_ds = indicator_data_speed(d_bytes=output_bytes, t_s=elapsed_s)

        return {
            "mips_per_byte": i_mi,
            "flops_per_byte": i_fo,
            "data_speed_bytes_per_s": i_ds,
            "avg_cpu_utilization": avg_cpu_util,
            "avg_cpu_freq_mhz": avg_cpu_freq,
        }

    async def measure_energy_consumption(
        self, energy_samples: List[Dict[str, Any]], elapsed_s: float, output_bytes: int
    ) -> Dict[str, Any]:
        """
        Measure energy consumption (能耗分析).

        Returns:
            - energy_joules: Total energy consumed
            - energy_per_byte: Energy per unit data (I_EC from Part 2 Eq. 11)
            - avg_power_watts: Average power consumption
            - cpu_energy_joules: CPU energy (if available)
            - gpu_energy_joules: GPU energy (if available)
        """
        if not energy_samples:
            return {
                "energy_joules": None,
                "energy_per_byte": None,
                "avg_power_watts": None,
                "cpu_energy_joules": None,
                "gpu_energy_joules": None,
            }

        # Aggregate energy metrics
        energy_j = energy_samples[-1].get("energy_joules") if energy_samples else None
        avg_power = energy_samples[-1].get("average_power_watts") if energy_samples else None
        cpu_energy = energy_samples[-1].get("cpu_energy_joules") if energy_samples else None
        gpu_energy = energy_samples[-1].get("gpu_energy_joules") if energy_samples else None

        # Compute energy per data (I_EC)
        i_ec = indicator_energy_consumption_per_data(energy_joules=energy_j, d_bytes=output_bytes)

        return {
            "energy_joules": energy_j,
            "energy_per_byte": i_ec,
            "avg_power_watts": avg_power,
            "cpu_energy_joules": cpu_energy,
            "gpu_energy_joules": gpu_energy,
        }

    async def estimate_carbon_footprint(
        self, energy_samples: List[Dict[str, Any]], elapsed_s: float, output_bytes: int
    ) -> Dict[str, Any]:
        """
        Estimate carbon footprint (碳排放估算).

        Returns:
            - carbon_gco2e: Total carbon emissions in gCO2e
            - carbon_per_byte: Carbon per unit data (I_CE from Part 2 Eq. 12)
            - carbon_intensity_gco2e_per_kwh: Carbon intensity used
        """
        if not energy_samples:
            return {
                "carbon_gco2e": None,
                "carbon_per_byte": None,
                "carbon_intensity_gco2e_per_kwh": self.assumptions.carbon_intensity_gco2e_per_kwh,
            }

        energy_j = energy_samples[-1].get("energy_joules") if energy_samples else None
        carbon_gco2e = carbon_gco2e_from_energy_joules(energy_joules=energy_j, assumptions=self.assumptions)

        # Compute carbon per data (I_CE = m_c * I_EC)
        # We already have I_EC from measure_energy_consumption, so:
        # I_CE = m_c * (energy_j / output_bytes) if we normalize by data
        carbon_per_byte = None
        if carbon_gco2e is not None and output_bytes > 0:
            carbon_per_byte = carbon_gco2e / float(output_bytes)

        return {
            "carbon_gco2e": carbon_gco2e,
            "carbon_per_byte": carbon_per_byte,
            "carbon_intensity_gco2e_per_kwh": self.assumptions.carbon_intensity_gco2e_per_kwh,
        }

    def monitor_resource_usage(
        self, perf_samples: List[Dict[str, Any]], energy_samples: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Monitor resource utilization (资源利用率).

        Returns:
            - cpu_utilization_pct: CPU utilization percentage
            - memory_usage_mb: Memory usage in MB
            - memory_utilization_pct: Memory utilization percentage
            - peak_cpu_utilization: Peak CPU utilization
            - peak_memory_usage_mb: Peak memory usage
        """
        if not perf_samples:
            return {
                "cpu_utilization_pct": None,
                "memory_usage_mb": None,
                "memory_utilization_pct": None,
                "peak_cpu_utilization": None,
                "peak_memory_usage_mb": None,
            }

        cpu_utils = [s.get("cpu_utilization", 0) for s in perf_samples if s.get("cpu_utilization") is not None]
        memory_mb = [s.get("memory_usage_mb", 0) for s in perf_samples if s.get("memory_usage_mb") is not None]
        memory_utils = [s.get("memory_utilization", 0) for s in perf_samples if s.get("memory_utilization") is not None]

        avg_cpu_util = (sum(cpu_utils) / len(cpu_utils) * 100) if cpu_utils else None
        avg_memory_mb = sum(memory_mb) / len(memory_mb) if memory_mb else None
        avg_memory_util = (sum(memory_utils) / len(memory_utils) * 100) if memory_utils else None
        peak_cpu_util = (max(cpu_utils) * 100) if cpu_utils else None
        peak_memory_mb = max(memory_mb) if memory_mb else None

        return {
            "cpu_utilization_pct": avg_cpu_util,
            "memory_usage_mb": avg_memory_mb,
            "memory_utilization_pct": avg_memory_util,
            "peak_cpu_utilization": peak_cpu_util,
            "peak_memory_usage_mb": peak_memory_mb,
        }

    def _aggregate_metrics(self, all_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate metrics across multiple tasks."""
        if not all_metrics:
            return {
                "performance": {},
                "efficiency": {},
                "energy": {},
                "carbon": {},
                "resource": {},
            }

        # Simple aggregation: average numeric values, keep structure
        aggregated = {
            "performance": self._aggregate_dict_list([m["performance"] for m in all_metrics]),
            "efficiency": self._aggregate_dict_list([m["efficiency"] for m in all_metrics]),
            "energy": self._aggregate_dict_list([m["energy"] for m in all_metrics]),
            "carbon": self._aggregate_dict_list([m["carbon"] for m in all_metrics]),
            "resource": self._aggregate_dict_list([m["resource"] for m in all_metrics]),
        }

        # Add task count
        aggregated["task_count"] = len(all_metrics)

        return aggregated

    def _aggregate_dict_list(self, dicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate a list of dictionaries by averaging numeric values."""
        if not dicts:
            return {}

        result = {}
        for key in dicts[0].keys():
            values = [d.get(key) for d in dicts if d.get(key) is not None]
            if values and all(isinstance(v, (int, float)) for v in values):
                result[key] = sum(values) / len(values)
            elif values:
                # For non-numeric, use first non-None value
                result[key] = values[0] if values else None
            else:
                result[key] = None

        return result


# Convenience function for synchronous usage
def evaluate(model: ModelConfig | Dict[str, Any], tasks: List[Dict[str, Any]] | Dict[str, Any]) -> Dict[str, Any]:
    """
    Synchronous wrapper for DFLCAEvaluator.evaluate.

    Args:
        model: Model configuration
        tasks: Task(s) to evaluate

    Returns:
        Aggregated metrics dictionary
    """
    evaluator = DFLCAEvaluator()
    return asyncio.run(evaluator.evaluate(model, tasks))
