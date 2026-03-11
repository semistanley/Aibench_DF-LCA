"""Example: Using different report templates."""
from datetime import datetime, timezone

from core.schemas import (
    EvaluationResult,
    ModelConfig,
    ModelProvider,
    RunMetrics,
    PerformanceMetrics,
    EnergyMetrics,
    ValueMetrics,
)
from reporter import ReportGenerator, REPORT_TEMPLATES


def create_sample_result():
    """Create a sample evaluation result for testing."""
    return EvaluationResult(
        run_id="example_123",
        created_at=datetime.now(timezone.utc),
        task_name="demo",
        model=ModelConfig(provider=ModelProvider.local, model="test-model"),
        input={"prompt": "Hello, world!"},
        output={"text": "Hello! How can I help you?"},
        metrics=RunMetrics(
            performance=PerformanceMetrics(
                latency_ms=150.5,
                throughput_tokens_per_s=50.2,
                accuracy=0.85,
                input_tokens=10,
                output_tokens=8,
            ),
            energy=EnergyMetrics(
                energy_joules=0.001,
                average_power_watts=5.5,
                carbon_gco2e=0.0001,
            ),
            value=ValueMetrics(
                quality_score=0.9,
                roi=0.15,
            ),
        ),
    )


def main():
    """Generate reports with different templates."""
    result = create_sample_result()
    
    print("=" * 60)
    print("Report Template Examples")
    print("=" * 60)
    
    print("\nAvailable templates:")
    for name, config in REPORT_TEMPLATES.items():
        print(f"  {name}: {config['name']} - {config['description']}")
    
    print("\nGenerating reports with different templates...")
    
    for template_name in REPORT_TEMPLATES.keys():
        try:
            print(f"\n[{template_name}] Generating report...")
            generator = ReportGenerator(template=template_name)
            report_path = generator.generate_report(
                result,
                format="html",
                output_path=f"example_report_{template_name}.html",
                include_charts=True,
            )
            print(f"  Report generated: {report_path}")
        except Exception as e:
            print(f"  Error: {e}")
    
    print("\n" + "=" * 60)
    print("All reports generated successfully!")
    print("=" * 60)
    print("\nYou can open the HTML files in a browser to view the reports.")


if __name__ == "__main__":
    main()
