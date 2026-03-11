"""Example: Generate comprehensive evaluation reports."""
import asyncio
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.schemas import (
    EvaluationResult,
    ModelConfig,
    ModelProvider,
    RunMetrics,
    PerformanceMetrics,
    EnergyMetrics,
    ValueMetrics,
)
from dflca_evaluator import DFLCAEvaluator
from reporter import ReportGenerator


async def main():
    """Generate a comprehensive evaluation report."""
    # Run evaluation
    print("Running DF-LCA evaluation...")
    evaluator = DFLCAEvaluator()
    model = ModelConfig(provider=ModelProvider.local, model="echo")
    tasks = [{"prompt": "What is 2+2?"}, {"prompt": "Explain quantum computing."}]

    result_dict = await evaluator.evaluate(model, tasks)
    print("Evaluation completed!")

    # Convert to EvaluationResult format for report generation
    # (In practice, you would use the actual EvaluationResult from tasks.engine)
    result = EvaluationResult(
        run_id="example_run_123",
        created_at=datetime.now(timezone.utc),
        task_name="demo",
        model=model,
        input={"prompt": tasks[0]["prompt"]},
        output={"text": "Example output"},
        metrics=RunMetrics(
            performance=PerformanceMetrics(
                latency_ms=result_dict["performance"]["latency_ms"],
                throughput_tokens_per_s=result_dict["performance"]["throughput_tokens_per_s"],
                input_tokens=result_dict["performance"]["input_tokens"],
                output_tokens=result_dict["performance"]["output_tokens"],
            ),
            energy=EnergyMetrics(
                energy_joules=result_dict["energy"]["energy_joules"],
                average_power_watts=result_dict["energy"]["avg_power_watts"],
                carbon_gco2e=result_dict["carbon"]["carbon_gco2e"],
                cpu_energy_joules=result_dict["energy"].get("cpu_energy_joules"),
            ),
            value=ValueMetrics(
                quality_score=0.85,
                roi=0.15,
            ),
        ),
        tags={"task": "demo", "example": "true"},
    )

    # Generate HTML report
    print("\nGenerating HTML report...")
    generator = ReportGenerator()
    html_path = generator.generate_report(
        result,
        format="html",
        output_path="example_report.html",
        include_charts=True,
    )
    print(f"HTML report generated: {html_path}")

    # Try to generate PDF (if weasyprint is available)
    try:
        print("\nGenerating PDF report...")
        pdf_path = generator.generate_report(
            result,
            format="pdf",
            output_path="example_report.pdf",
            include_charts=True,
        )
        print(f"PDF report generated: {pdf_path}")
    except ImportError:
        print("PDF generation skipped (weasyprint not installed)")
    except Exception as e:
        print(f"PDF generation failed: {e}")

    print("\n✅ Report generation completed!")


if __name__ == "__main__":
    asyncio.run(main())
