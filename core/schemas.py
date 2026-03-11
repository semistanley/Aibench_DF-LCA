from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class MetricDimension(str, Enum):
    performance = "performance"
    energy = "energy"
    value = "value"


class PerformanceMetrics(BaseModel):
    latency_ms: Optional[float] = None
    throughput_tokens_per_s: Optional[float] = None
    accuracy: Optional[float] = Field(
        default=None, description="Task-specific accuracy/score (e.g., accuracy, exact match, pass rate)."
    )
    output_tokens: Optional[int] = None
    input_tokens: Optional[int] = None


class EnergyMetrics(BaseModel):
    energy_joules: Optional[float] = None
    average_power_watts: Optional[float] = None
    cpu_energy_joules: Optional[float] = None
    gpu_energy_joules: Optional[float] = None
    carbon_gco2e: Optional[float] = Field(
        default=None,
        description="Estimated carbon footprint in gCO2e (method/country/PUE should be recorded in artifacts).",
    )
    notes: Optional[str] = None


class ValueMetrics(BaseModel):
    quality_score: Optional[float] = Field(
        default=None, description="Task-specific score (e.g., exact match, BLEU, pass@k, etc.)"
    )
    cost_usd: Optional[float] = None
    roi: Optional[float] = Field(
        default=None, description="Return on investment; definition depends on business context."
    )
    sustainability_index: Optional[float] = Field(
        default=None,
        description="Composite sustainability index; should be defined and versioned in artifacts.",
    )


class RunMetrics(BaseModel):
    performance: PerformanceMetrics = Field(default_factory=PerformanceMetrics)
    energy: EnergyMetrics = Field(default_factory=EnergyMetrics)
    value: ValueMetrics = Field(default_factory=ValueMetrics)
    extra: Dict[str, Any] = Field(default_factory=dict)


class ModelProvider(str, Enum):
    openai = "openai"
    huggingface = "huggingface"
    local = "local"


class ModelConfig(BaseModel):
    provider: ModelProvider
    model: str
    base_url: Optional[str] = None
    api_key_env: Optional[str] = None
    generation_params: Dict[str, Any] = Field(default_factory=dict)


class EvaluationRequest(BaseModel):
    task_name: str
    input: Dict[str, Any]
    model: ModelConfig
    options: "EvaluationOptions" = Field(default_factory=lambda: EvaluationOptions())
    tags: Dict[str, str] = Field(default_factory=dict)


class Artifact(BaseModel):
    kind: Literal["prompt", "output", "trace", "meta"] = "meta"
    payload: Dict[str, Any] = Field(default_factory=dict)


class EvaluationResult(BaseModel):
    run_id: str
    created_at: datetime
    task_name: str
    model: ModelConfig
    input: Dict[str, Any]
    output: Dict[str, Any]
    metrics: RunMetrics
    artifacts: List[Artifact] = Field(default_factory=list)
    tags: Dict[str, str] = Field(default_factory=dict)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EnergyCollectionMethod(str, Enum):
    cpu_estimate = "cpu_estimate"
    external_meter = "external_meter"
    sensors = "sensors"


class EvaluationOptions(BaseModel):
    """
    Options that change how metrics are collected/derived.
    Recorded into artifacts for traceability.
    """

    energy_method: EnergyCollectionMethod = EnergyCollectionMethod.cpu_estimate
    sample_interval_s: float = Field(default=0.25, ge=0.05, le=10.0)

