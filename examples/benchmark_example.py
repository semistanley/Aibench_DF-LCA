"""Example: Using BenchmarkTasks with DFLCAEvaluator."""
import asyncio
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmark_tasks import BenchmarkTasks
from core.schemas import ModelConfig, ModelProvider
from dflca_evaluator import DFLCAEvaluator


async def main():
    """Run benchmark evaluation on a standard task."""
    # Initialize components
    tasks = BenchmarkTasks()
    evaluator = DFLCAEvaluator()

    # Configure model
    model = ModelConfig(provider=ModelProvider.local, model="echo")

    # Load a small sample from GSM8K
    print("Loading GSM8K dataset...")
    samples = tasks.load_dataset("gsm8k", limit=3)
    print(f"Loaded {len(samples)} samples")

    # Convert to evaluation format
    eval_tasks = [{"prompt": s["prompt"], "target": s.get("target")} for s in samples]

    # Run evaluation
    print("\nRunning DF-LCA evaluation...")
    result = await evaluator.evaluate(model, eval_tasks)

    # Display results
    print("\n=== Evaluation Results ===")
    print(f"Task count: {result['task_count']}")
    print(f"\nPerformance:")
    print(f"  Latency: {result['performance']['latency_ms']:.2f} ms")
    print(f"  Throughput: {result['performance']['throughput_tokens_per_s']:.2f} tokens/s")

    print(f"\nEfficiency:")
    print(f"  Data speed: {result['efficiency']['data_speed_bytes_per_s']:.2f} bytes/s")
    if result['efficiency']['mips_per_byte']:
        print(f"  MIPS per byte: {result['efficiency']['mips_per_byte']:.6f}")

    print(f"\nEnergy:")
    if result['energy']['energy_joules']:
        print(f"  Energy: {result['energy']['energy_joules']:.6f} J")
        print(f"  Energy per byte: {result['energy']['energy_per_byte']:.6f} J/byte")

    print(f"\nCarbon:")
    if result['carbon']['carbon_gco2e']:
        print(f"  Carbon: {result['carbon']['carbon_gco2e']:.6f} gCO2e")
        print(f"  Carbon per byte: {result['carbon']['carbon_per_byte']:.6f} gCO2e/byte")

    print(f"\nResource:")
    if result['resource']['cpu_utilization_pct']:
        print(f"  CPU utilization: {result['resource']['cpu_utilization_pct']:.2f}%")
    if result['resource']['memory_usage_mb']:
        print(f"  Memory usage: {result['resource']['memory_usage_mb']:.2f} MB")


if __name__ == "__main__":
    asyncio.run(main())
