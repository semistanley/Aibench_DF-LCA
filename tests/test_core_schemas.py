"""Basic tests for core schemas."""
import pytest
from core.schemas import (
    PerformanceMetrics,
    EnergyMetrics,
    ValueMetrics,
    ModelProvider,
    ModelConfig,
    EvaluationRequest,
)


def test_performance_metrics_defaults():
    """Test PerformanceMetrics with default values."""
    pm = PerformanceMetrics()
    assert pm.latency_ms is None
    assert pm.throughput_tokens_per_s is None
    assert pm.accuracy is None


def test_energy_metrics_defaults():
    """Test EnergyMetrics with default values."""
    em = EnergyMetrics()
    assert em.energy_joules is None
    assert em.carbon_gco2e is None


def test_value_metrics_defaults():
    """Test ValueMetrics with default values."""
    vm = ValueMetrics()
    assert vm.cost_usd is None
    assert vm.roi is None
    assert vm.sustainability_index is None


def test_model_provider_enum():
    """Test ModelProvider enum values."""
    assert ModelProvider.local.value == "local"
    assert ModelProvider.openai.value == "openai"
    assert ModelProvider.huggingface.value == "huggingface"


def test_evaluation_request_creation():
    """Test creating an EvaluationRequest."""
    req = EvaluationRequest(
        task_name="test",
        input={"prompt": "hello"},
        model=ModelConfig(provider=ModelProvider.local, model="echo"),
    )
    assert req.task_name == "test"
    assert req.input == {"prompt": "hello"}
    assert req.model.provider == ModelProvider.local
