"""Report Generator - Generate comprehensive HTML/PDF reports with analysis and recommendations."""
from __future__ import annotations

import base64
import json
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    import plotly.graph_objects as go
    from plotly import offline
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

try:
    from weasyprint import HTML
    HAS_WEASYPRINT = True
except ImportError:
    HAS_WEASYPRINT = False

from core.schemas import EvaluationResult


# 报告模板定义
REPORT_TEMPLATES = {
    "academic": {
        "name": "Academic",
        "description": "适合论文发表的格式",
        "features": ["详细的实验方法", "完整的统计数据", "引用格式", "图表说明"],
    },
    "engineering": {
        "name": "Engineering",
        "description": "工程师关注的性能指标",
        "features": ["技术指标详细", "性能对比", "系统架构", "优化建议"],
    },
    "executive": {
        "name": "Executive",
        "description": "给管理层的简明报告",
        "features": ["关键指标摘要", "商业价值", "成本分析", "决策建议"],
    },
    "sustainability": {
        "name": "Sustainability",
        "description": "侧重环保和碳足迹的报告",
        "features": ["碳排放详细分析", "环境影响评估", "可持续性指标", "绿色建议"],
    },
}


class ReportGenerator:
    """
    Generate comprehensive evaluation reports in HTML/PDF format.
    
    Reports include:
    1. Overall score (综合评分)
    2. Performance comparison charts (性能对比图表)
    3. Energy efficiency analysis (能效分析)
    4. Improvement recommendations (改进建议)
    
    Supports multiple templates:
    - academic: 适合论文发表的格式
    - engineering: 工程师关注的性能指标
    - executive: 给管理层的简明报告
    - sustainability: 侧重环保和碳足迹的报告
    """

    def __init__(self, *, template_dir: Optional[Path] = None, template: str = "engineering"):
        """
        Initialize ReportGenerator.

        Args:
            template_dir: Optional directory for custom HTML templates
            template: Report template name (academic, engineering, executive, sustainability)
        """
        self.template_dir = template_dir
        if template not in REPORT_TEMPLATES:
            raise ValueError(f"Unknown template: {template}. Available: {list(REPORT_TEMPLATES.keys())}")
        self.template = template
        self.template_config = REPORT_TEMPLATES[template]

    def generate_report(
        self,
        evaluation_results: Union[EvaluationResult, List[EvaluationResult]],
        *,
        format: str = "html",
        output_path: Optional[str] = None,
        include_charts: bool = True,
        compare_models: bool = False,
        template: Optional[str] = None,
    ) -> str:
        """
        Generate a comprehensive evaluation report.

        Args:
            evaluation_results: Single EvaluationResult or list of results
            format: Output format ("html" or "pdf")
            output_path: Optional output file path
            include_charts: Whether to include interactive charts
            compare_models: Whether to generate comparison charts (requires multiple results)

        Returns:
            Path to generated report file

        Raises:
            ValueError: If format is not supported or PDF generation fails
        """
        # Normalize input
        if isinstance(evaluation_results, EvaluationResult):
            results = [evaluation_results]
            single_result = True
        else:
            results = evaluation_results
            single_result = False

        if not results:
            raise ValueError("No evaluation results provided")

        # Use provided template or default
        current_template = template or self.template
        if current_template not in REPORT_TEMPLATES:
            current_template = self.template

        # Generate report content
        html_content = self._generate_html(
            results,
            single_result=single_result,
            include_charts=include_charts,
            compare_models=compare_models and len(results) > 1,
            template=current_template,
        )

        # Determine output path
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if single_result:
                run_id = results[0].run_id[:8]
                filename = f"report_{run_id}_{timestamp}.{format}"
            else:
                filename = f"report_comparison_{timestamp}.{format}"
            output_path = filename

        output_path = Path(output_path)

        # Generate HTML
        if format == "html":
            output_path.write_text(html_content, encoding="utf-8")
            return str(output_path)

        # Generate PDF
        elif format == "pdf":
            if not HAS_WEASYPRINT:
                raise ImportError(
                    "weasyprint required for PDF generation. Install with: pip install weasyprint"
                )
            try:
                HTML(string=html_content).write_pdf(output_path)
                return str(output_path)
            except Exception as e:
                raise ValueError(f"PDF generation failed: {e}") from e

        else:
            raise ValueError(f"Unsupported format: {format}. Use 'html' or 'pdf'")

    def _generate_html(
        self,
        results: List[EvaluationResult],
        *,
        single_result: bool,
        include_charts: bool,
        compare_models: bool,
        template: str = "engineering",
    ) -> str:
        """Generate HTML report content."""
        # Calculate overall scores
        scores = [self._calculate_overall_score(r) for r in results]

        # Generate charts
        charts_html = ""
        if include_charts:
            if compare_models and len(results) > 1:
                charts_html = self._generate_comparison_charts(results, scores)
            else:
                charts_html = self._generate_single_result_charts(results[0])

        # Generate recommendations
        recommendations = self._generate_recommendations(results[0])

        # Generate template-specific content
        if template == "academic":
            content = self._generate_academic_content(results, scores, charts_html, recommendations, single_result)
        elif template == "executive":
            content = self._generate_executive_content(results, scores, charts_html, recommendations, single_result)
        elif template == "sustainability":
            content = self._generate_sustainability_content(results, scores, charts_html, recommendations, single_result)
        else:  # engineering (default)
            content = self._generate_engineering_content(results, scores, charts_html, recommendations, single_result)

        # Build HTML
        template_name = REPORT_TEMPLATES[template]["name"]
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DF-LCA Evaluation Report - {template_name}</title>
    <style>
        {self._get_css(template)}
    </style>
    {self._get_plotly_js() if include_charts and HAS_PLOTLY else ''}
</head>
<body>
    <div class="container template-{template}">
        <header>
            <h1>📊 DF-LCA Evaluation Report</h1>
            <p class="template-badge">Template: {template_name}</p>
            <p class="timestamp">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </header>

        {content}
    </div>
</body>
</html>"""

        return html

    def _calculate_overall_score(self, result: EvaluationResult) -> Dict[str, Any]:
        """
        Calculate overall score (综合评分) based on multiple dimensions.

        Returns:
            Dictionary with score breakdown and total score (0-100)
        """
        m = result.metrics
        scores = {}

        # Performance score (0-30 points)
        perf_score = 0
        if m.performance.latency_ms is not None:
            # Lower latency is better (normalize: <100ms = 30, >1000ms = 0)
            latency_score = max(0, 30 * (1 - min(m.performance.latency_ms / 1000, 1)))
            perf_score += latency_score
        if m.performance.throughput_tokens_per_s is not None:
            # Higher throughput is better (normalize: >100 tokens/s = 10, <10 = 0)
            throughput_score = min(10, m.performance.throughput_tokens_per_s / 10)
            perf_score += throughput_score
        if m.performance.accuracy is not None:
            # Accuracy score (0-10 points)
            acc = m.performance.accuracy
            if acc <= 1.0:  # Percentage
                acc_score = acc * 10
            else:  # Absolute value, normalize
                acc_score = min(10, acc / 10)
            perf_score += acc_score
        scores["performance"] = min(30, perf_score)

        # Energy efficiency score (0-25 points)
        energy_score = 0
        if m.energy.energy_joules is not None and m.performance.output_tokens:
            # Energy per token (lower is better)
            energy_per_token = m.energy.energy_joules / max(m.performance.output_tokens, 1)
            # Normalize: <0.001 J/token = 25, >0.01 J/token = 0
            energy_score = max(0, 25 * (1 - min(energy_per_token / 0.01, 1)))
        scores["energy"] = energy_score

        # Carbon footprint score (0-20 points)
        carbon_score = 0
        if m.energy.carbon_gco2e is not None and m.performance.output_tokens:
            # Carbon per token (lower is better)
            carbon_per_token = m.energy.carbon_gco2e / max(m.performance.output_tokens, 1)
            # Normalize: <0.0001 gCO2e/token = 20, >0.001 = 0
            carbon_score = max(0, 20 * (1 - min(carbon_per_token / 0.001, 1)))
        scores["carbon"] = carbon_score

        # Value score (0-15 points)
        value_score = 0
        if m.value.quality_score is not None:
            qs = m.value.quality_score
            if qs <= 1.0:
                value_score = qs * 10
            else:
                value_score = min(10, qs / 10)
        if m.value.roi is not None:
            # ROI score (0-5 points)
            roi_score = min(5, max(0, m.value.roi * 5)) if m.value.roi > 0 else 0
            value_score += roi_score
        scores["value"] = min(15, value_score)

        # Resource utilization score (0-10 points)
        resource_score = 0
        # This would need resource metrics from artifacts or extra fields
        # For now, give a baseline score
        resource_score = 5  # Placeholder
        scores["resource"] = resource_score

        # Total score
        total_score = sum(scores.values())
        scores["total"] = total_score
        scores["percentage"] = (total_score / 100) * 100

        return scores

    def _generate_summary_section(self, results: List[EvaluationResult], scores: List[Dict[str, Any]]) -> str:
        """Generate summary section."""
        result = results[0]
        score = scores[0]

        return f"""
        <section class="summary">
            <h2>📋 Summary</h2>
            <div class="summary-grid">
                <div class="summary-item">
                    <span class="label">Run ID:</span>
                    <span class="value">{result.run_id}</span>
                </div>
                <div class="summary-item">
                    <span class="label">Task:</span>
                    <span class="value">{result.task_name}</span>
                </div>
                <div class="summary-item">
                    <span class="label">Model:</span>
                    <span class="value">{result.model.provider.value}/{result.model.model}</span>
                </div>
                <div class="summary-item">
                    <span class="label">Created:</span>
                    <span class="value">{result.created_at.strftime("%Y-%m-%d %H:%M:%S")}</span>
                </div>
                <div class="summary-item">
                    <span class="label">Overall Score:</span>
                    <span class="value score-value">{score['percentage']:.1f}%</span>
                </div>
            </div>
        </section>
        """

    def _generate_overall_score_section(self, result: EvaluationResult, score: Dict[str, Any]) -> str:
        """Generate overall score breakdown section."""
        return f"""
        <section class="score-section">
            <h2>🎯 Overall Score Breakdown</h2>
            <div class="score-breakdown">
                <div class="score-item">
                    <div class="score-label">Performance</div>
                    <div class="score-bar">
                        <div class="score-fill" style="width: {score['performance']/30*100}%"></div>
                    </div>
                    <div class="score-value">{score['performance']:.1f}/30</div>
                </div>
                <div class="score-item">
                    <div class="score-label">Energy Efficiency</div>
                    <div class="score-bar">
                        <div class="score-fill" style="width: {score['energy']/25*100}%"></div>
                    </div>
                    <div class="score-value">{score['energy']:.1f}/25</div>
                </div>
                <div class="score-item">
                    <div class="score-label">Carbon Footprint</div>
                    <div class="score-bar">
                        <div class="score-fill" style="width: {score['carbon']/20*100}%"></div>
                    </div>
                    <div class="score-value">{score['carbon']:.1f}/20</div>
                </div>
                <div class="score-item">
                    <div class="score-label">Value</div>
                    <div class="score-bar">
                        <div class="score-fill" style="width: {score['value']/15*100}%"></div>
                    </div>
                    <div class="score-value">{score['value']:.1f}/15</div>
                </div>
                <div class="score-item">
                    <div class="score-label">Resource Utilization</div>
                    <div class="score-bar">
                        <div class="score-fill" style="width: {score['resource']/10*100}%"></div>
                    </div>
                    <div class="score-value">{score['resource']:.1f}/10</div>
                </div>
            </div>
            <div class="total-score">
                <span class="total-label">Total Score:</span>
                <span class="total-value">{score['total']:.1f}/100 ({score['percentage']:.1f}%)</span>
            </div>
        </section>
        """

    def _generate_comparison_scores_section(self, results: List[EvaluationResult], scores: List[Dict[str, Any]]) -> str:
        """Generate comparison scores section for multiple results."""
        html = """
        <section class="score-section">
            <h2>🎯 Overall Score Comparison</h2>
            <div class="comparison-table">
                <table>
                    <thead>
                        <tr>
                            <th>Model</th>
                            <th>Performance</th>
                            <th>Energy</th>
                            <th>Carbon</th>
                            <th>Value</th>
                            <th>Total</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        for result, score in zip(results, scores):
            model_name = f"{result.model.provider.value}/{result.model.model}"
            html += f"""
                        <tr>
                            <td>{model_name}</td>
                            <td>{score['performance']:.1f}</td>
                            <td>{score['energy']:.1f}</td>
                            <td>{score['carbon']:.1f}</td>
                            <td>{score['value']:.1f}</td>
                            <td><strong>{score['total']:.1f}</strong></td>
                        </tr>
            """
        html += """
                    </tbody>
                </table>
            </div>
        </section>
        """
        return html

    def _generate_single_result_charts(self, result: EvaluationResult) -> str:
        """Generate charts for a single result."""
        if not HAS_PLOTLY:
            return "<!-- Charts require plotly library -->"

        m = result.metrics

        # Performance metrics chart
        perf_fig = go.Figure()
        if m.performance.latency_ms:
            perf_fig.add_trace(go.Bar(
                x=["Latency (ms)", "Throughput (tokens/s)"],
                y=[m.performance.latency_ms, m.performance.throughput_tokens_per_s or 0],
                marker_color=["#1f77b4", "#ff7f0e"],
                name="Performance",
            ))
        perf_fig.update_layout(
            title="Performance Metrics",
            yaxis_title="Value",
            height=300,
        )
        perf_chart = offline.plot(perf_fig, output_type="div", include_plotlyjs=False)

        # Energy metrics chart
        energy_fig = go.Figure()
        energy_data = []
        if m.energy.energy_joules:
            energy_data.append(("Energy (J)", m.energy.energy_joules))
        if m.energy.cpu_energy_joules:
            energy_data.append(("CPU Energy (J)", m.energy.cpu_energy_joules))
        if m.energy.gpu_energy_joules:
            energy_data.append(("GPU Energy (J)", m.energy.gpu_energy_joules))

        if energy_data:
            energy_fig.add_trace(go.Bar(
                x=[d[0] for d in energy_data],
                y=[d[1] for d in energy_data],
                marker_color="#2ca02c",
            ))
        energy_fig.update_layout(
            title="Energy Consumption Breakdown",
            yaxis_title="Energy (Joules)",
            height=300,
        )
        energy_chart = offline.plot(energy_fig, output_type="div", include_plotlyjs=False)

        return f"""
        <section class="charts-section">
            <h2>📊 Performance & Energy Charts</h2>
            <div class="charts-grid">
                <div class="chart-container">
                    {perf_chart}
                </div>
                <div class="chart-container">
                    {energy_chart}
                </div>
            </div>
        </section>
        """

    def _generate_comparison_charts(self, results: List[EvaluationResult], scores: List[Dict[str, Any]]) -> str:
        """Generate comparison charts for multiple results."""
        if not HAS_PLOTLY:
            return "<!-- Charts require plotly library -->"

        model_names = [f"{r.model.provider.value}/{r.model.model}" for r in results]

        # Score comparison chart
        score_fig = go.Figure()
        score_fig.add_trace(go.Bar(
            x=model_names,
            y=[s['total'] for s in scores],
            marker_color="#9467bd",
        ))
        score_fig.update_layout(
            title="Overall Score Comparison",
            yaxis_title="Score (0-100)",
            height=300,
        )
        score_chart = offline.plot(score_fig, output_type="div", include_plotlyjs=False)

        # Performance comparison
        perf_fig = go.Figure()
        latencies = [r.metrics.performance.latency_ms for r in results]
        throughputs = [r.metrics.performance.throughput_tokens_per_s or 0 for r in results]
        perf_fig.add_trace(go.Bar(
            name="Latency (ms)",
            x=model_names,
            y=latencies,
            marker_color="#1f77b4",
        ))
        perf_fig.add_trace(go.Bar(
            name="Throughput (tokens/s)",
            x=model_names,
            y=throughputs,
            marker_color="#ff7f0e",
        ))
        perf_fig.update_layout(
            title="Performance Comparison",
            yaxis_title="Value",
            barmode="group",
            height=300,
        )
        perf_chart = offline.plot(perf_fig, output_type="div", include_plotlyjs=False)

        return f"""
        <section class="charts-section">
            <h2>📊 Comparison Charts</h2>
            <div class="charts-grid">
                <div class="chart-container">
                    {score_chart}
                </div>
                <div class="chart-container">
                    {perf_chart}
                </div>
            </div>
        </section>
        """

    def _generate_performance_section(self, result: EvaluationResult) -> str:
        """Generate performance metrics section."""
        m = result.metrics.performance
        return f"""
        <section class="metrics-section">
            <h2>⚡ Performance Metrics</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">Latency</div>
                    <div class="metric-value">{m.latency_ms:.2f} ms</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Throughput</div>
                    <div class="metric-value">{m.throughput_tokens_per_s:.2f} tokens/s</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Input Tokens</div>
                    <div class="metric-value">{m.input_tokens or 'N/A'}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Output Tokens</div>
                    <div class="metric-value">{m.output_tokens or 'N/A'}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Accuracy</div>
                    <div class="metric-value">{m.accuracy if m.accuracy is not None else 'N/A'}</div>
                </div>
            </div>
        </section>
        """

    def _generate_comparison_performance_section(self, results: List[EvaluationResult]) -> str:
        """Generate performance comparison section."""
        html = """
        <section class="metrics-section">
            <h2>⚡ Performance Comparison</h2>
            <div class="comparison-table">
                <table>
                    <thead>
                        <tr>
                            <th>Model</th>
                            <th>Latency (ms)</th>
                            <th>Throughput (tokens/s)</th>
                            <th>Input Tokens</th>
                            <th>Output Tokens</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        for result in results:
            m = result.metrics.performance
            model_name = f"{result.model.provider.value}/{result.model.model}"
            html += f"""
                        <tr>
                            <td>{model_name}</td>
                            <td>{m.latency_ms:.2f if m.latency_ms else 'N/A'}</td>
                            <td>{m.throughput_tokens_per_s:.2f if m.throughput_tokens_per_s else 'N/A'}</td>
                            <td>{m.input_tokens or 'N/A'}</td>
                            <td>{m.output_tokens or 'N/A'}</td>
                        </tr>
            """
        html += """
                    </tbody>
                </table>
            </div>
        </section>
        """
        return html

    def _generate_energy_section(self, result: EvaluationResult) -> str:
        """Generate energy metrics section."""
        m = result.metrics.energy
        return f"""
        <section class="metrics-section">
            <h2>🔋 Energy Metrics</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">Total Energy</div>
                    <div class="metric-value">{m.energy_joules:.6f} J</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Average Power</div>
                    <div class="metric-value">{m.average_power_watts:.2f} W</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Carbon Footprint</div>
                    <div class="metric-value">{m.carbon_gco2e:.6f} gCO2e</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">CPU Energy</div>
                    <div class="metric-value">{m.cpu_energy_joules:.6f} J</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">GPU Energy</div>
                    <div class="metric-value">{m.gpu_energy_joules:.6f} J</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Collection Method</div>
                    <div class="metric-value">{m.notes or 'N/A'}</div>
                </div>
            </div>
        </section>
        """

    def _generate_comparison_energy_section(self, results: List[EvaluationResult]) -> str:
        """Generate energy comparison section."""
        html = """
        <section class="metrics-section">
            <h2>🔋 Energy Comparison</h2>
            <div class="comparison-table">
                <table>
                    <thead>
                        <tr>
                            <th>Model</th>
                            <th>Energy (J)</th>
                            <th>Power (W)</th>
                            <th>Carbon (gCO2e)</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        for result in results:
            m = result.metrics.energy
            model_name = f"{result.model.provider.value}/{result.model.model}"
            html += f"""
                        <tr>
                            <td>{model_name}</td>
                            <td>{m.energy_joules:.6f if m.energy_joules else 'N/A'}</td>
                            <td>{m.average_power_watts:.2f if m.average_power_watts else 'N/A'}</td>
                            <td>{m.carbon_gco2e:.6f if m.carbon_gco2e else 'N/A'}</td>
                        </tr>
            """
        html += """
                    </tbody>
                </table>
            </div>
        </section>
        """
        return html

    def _generate_efficiency_analysis_section(self, result: EvaluationResult) -> str:
        """Generate energy efficiency analysis section."""
        m = result.metrics
        extra = m.extra or {}

        # Calculate efficiency metrics
        efficiency_metrics = []
        if m.performance.output_tokens and m.energy.energy_joules:
            energy_per_token = m.energy.energy_joules / m.performance.output_tokens
            efficiency_metrics.append(("Energy per Token", f"{energy_per_token:.6f} J/token"))

        if m.performance.output_tokens and m.energy.carbon_gco2e:
            carbon_per_token = m.energy.carbon_gco2e / m.performance.output_tokens
            efficiency_metrics.append(("Carbon per Token", f"{carbon_per_token:.6f} gCO2e/token"))

        if m.performance.latency_ms and m.performance.output_tokens:
            tokens_per_second = (m.performance.output_tokens / m.performance.latency_ms) * 1000
            efficiency_metrics.append(("Tokens per Second", f"{tokens_per_second:.2f} tokens/s"))

        # DF-LCA Part 2 indicators
        part2 = extra.get("df_lca_part2", {}).get("indicators", {})
        part2_items = []
        if part2:
            for key, value in part2.items():
                if value is not None:
                    part2_items.append((key.replace("_", " ").title(), f"{value:.6f}"))

        html = """
        <section class="efficiency-section">
            <h2>⚙️ Energy Efficiency Analysis</h2>
            <div class="efficiency-grid">
        """
        for label, value in efficiency_metrics:
            html += f"""
                <div class="efficiency-item">
                    <span class="efficiency-label">{label}:</span>
                    <span class="efficiency-value">{value}</span>
                </div>
            """
        html += """
            </div>
        """
        if part2_items:
            html += """
            <h3>DF-LCA Part 2 Standardized Indicators</h3>
            <div class="efficiency-grid">
            """
            for label, value in part2_items:
                html += f"""
                    <div class="efficiency-item">
                        <span class="efficiency-label">{label}:</span>
                        <span class="efficiency-value">{value}</span>
                    </div>
                """
            html += """
            </div>
        """
        html += """
        </section>
        """
        return html

    def _generate_recommendations_section(self, recommendations: List[str]) -> str:
        """Generate improvement recommendations section."""
        if not recommendations:
            return ""

        html = """
        <section class="recommendations-section">
            <h2>💡 Improvement Recommendations</h2>
            <ul class="recommendations-list">
        """
        for rec in recommendations:
            html += f"<li>{rec}</li>"
        html += """
            </ul>
        </section>
        """
        return html

    def _generate_recommendations(self, result: EvaluationResult) -> List[str]:
        """
        Generate improvement recommendations based on evaluation results.

        Returns:
            List of recommendation strings
        """
        recommendations = []
        m = result.metrics

        # Performance recommendations
        if m.performance.latency_ms and m.performance.latency_ms > 1000:
            recommendations.append(
                "⚠️ High latency detected (>1000ms). Consider optimizing model inference or using a faster model."
            )

        if m.performance.throughput_tokens_per_s and m.performance.throughput_tokens_per_s < 10:
            recommendations.append(
                "⚠️ Low throughput detected (<10 tokens/s). Consider batch processing or model optimization."
            )

        # Energy recommendations
        if m.energy.energy_joules and m.performance.output_tokens:
            energy_per_token = m.energy.energy_joules / m.performance.output_tokens
            if energy_per_token > 0.01:
                recommendations.append(
                    "🔋 High energy consumption per token. Consider using more energy-efficient hardware or model quantization."
                )

        if m.energy.carbon_gco2e and m.performance.output_tokens:
            carbon_per_token = m.energy.carbon_gco2e / m.performance.output_tokens
            if carbon_per_token > 0.001:
                recommendations.append(
                    "🌍 High carbon footprint per token. Consider using renewable energy sources or optimizing inference."
                )

        # Accuracy recommendations
        if m.performance.accuracy is not None:
            acc = m.performance.accuracy
            if acc <= 1.0 and acc < 0.7:
                recommendations.append(
                    "📊 Low accuracy detected (<70%). Consider fine-tuning the model or using a more capable model."
                )

        # General recommendations
        if not recommendations:
            recommendations.append("✅ Overall performance is good. Continue monitoring and optimizing as needed.")

        return recommendations

    def _generate_details_section(self, result: EvaluationResult) -> str:
        """Generate detailed information section."""
        return f"""
        <section class="details-section">
            <h2>📄 Detailed Information</h2>
            <div class="details-content">
                <h3>Input</h3>
                <pre>{json.dumps(result.input, indent=2, ensure_ascii=False)}</pre>
                <h3>Output</h3>
                <pre>{json.dumps(result.output, indent=2, ensure_ascii=False)}</pre>
                <h3>Tags</h3>
                <pre>{json.dumps(result.tags, indent=2, ensure_ascii=False)}</pre>
            </div>
        </section>
        """

    def _generate_engineering_content(
        self,
        results: List[EvaluationResult],
        scores: List[Dict[str, Any]],
        charts_html: str,
        recommendations: List[str],
        single_result: bool,
    ) -> str:
        """生成工程模板内容（默认）"""
        return f"""
        {self._generate_summary_section(results, scores)}
        {self._generate_overall_score_section(results[0], scores[0]) if single_result else self._generate_comparison_scores_section(results, scores)}
        {charts_html}
        {self._generate_performance_section(results[0]) if single_result else self._generate_comparison_performance_section(results)}
        {self._generate_energy_section(results[0]) if single_result else self._generate_comparison_energy_section(results)}
        {self._generate_efficiency_analysis_section(results[0]) if single_result else ''}
        {self._generate_recommendations_section(recommendations)}
        {self._generate_details_section(results[0]) if single_result else ''}
        """

    def _generate_academic_content(
        self,
        results: List[EvaluationResult],
        scores: List[Dict[str, Any]],
        charts_html: str,
        recommendations: List[str],
        single_result: bool,
    ) -> str:
        """生成学术模板内容"""
        result = results[0]
        m = result.metrics
        extra = m.extra or {}
        part2 = extra.get("df_lca_part2", {})
        
        return f"""
        {self._generate_summary_section(results, scores)}
        
        <section class="abstract-section">
            <h2>Abstract</h2>
            <p>This report presents a comprehensive evaluation of the AI model using the DF-LCA (Digital Footprint - Life Cycle Assessment) framework. 
            The evaluation covers performance metrics, energy consumption, and carbon footprint analysis.</p>
        </section>

        <section class="methodology-section">
            <h2>Methodology</h2>
            <h3>Evaluation Framework</h3>
            <p>The evaluation follows the DF-LCA framework as described in:</p>
            <ul>
                <li>Huang, Q. (2025). <em>How to assess the digitization and digital effort: A framework for Digitization Footprint (Part 1)</em>. 
                Computers and Electronics in Agriculture, 230, 109875. DOI: 10.1016/j.compag.2024.109875</li>
                <li>Huang, Q. (2024). <em>Indicators to Digitization Footprint and How to Get Digitization Footprint (Part 2)</em>. 
                Computers and Electronics in Agriculture, 224, 109206. DOI: 10.1016/j.compag.2024.109206</li>
            </ul>
            <h3>Functional Unit</h3>
            <p>The functional unit for this evaluation is <strong>unit data</strong> (per byte or per token), 
            enabling standardized comparison across different models and tasks.</p>
        </section>

        {self._generate_overall_score_section(results[0], scores[0]) if single_result else self._generate_comparison_scores_section(results, scores)}
        
        <section class="results-section">
            <h2>Results</h2>
            {charts_html}
            {self._generate_performance_section(results[0]) if single_result else self._generate_comparison_performance_section(results)}
            {self._generate_energy_section(results[0]) if single_result else self._generate_comparison_energy_section(results)}
            {self._generate_efficiency_analysis_section(results[0]) if single_result else ''}
        </section>

        {self._generate_df_lca_indicators_section(part2) if part2 else ''}

        <section class="discussion-section">
            <h2>Discussion</h2>
            {self._generate_recommendations_section(recommendations)}
        </section>

        <section class="references-section">
            <h2>References</h2>
            <ol>
                <li>Huang, Q. (2025). How to assess the digitization and digital effort: A framework for Digitization Footprint (Part 1). 
                <em>Computers and Electronics in Agriculture</em>, 230, 109875.</li>
                <li>Huang, Q. (2024). Indicators to Digitization Footprint and How to Get Digitization Footprint (Part 2). 
                <em>Computers and Electronics in Agriculture</em>, 224, 109206.</li>
            </ol>
        </section>

        {self._generate_details_section(results[0]) if single_result else ''}
        """

    def _generate_executive_content(
        self,
        results: List[EvaluationResult],
        scores: List[Dict[str, Any]],
        charts_html: str,
        recommendations: List[str],
        single_result: bool,
    ) -> str:
        """生成管理层模板内容"""
        result = results[0]
        score = scores[0]
        m = result.metrics
        
        return f"""
        {self._generate_summary_section(results, scores)}
        
        <section class="executive-summary">
            <h2>Executive Summary</h2>
            <div class="key-metrics-grid">
                <div class="key-metric-card">
                    <div class="key-metric-value">{score.get('total', 0):.0f}</div>
                    <div class="key-metric-label">Overall Score</div>
                </div>
                <div class="key-metric-card">
                    <div class="key-metric-value">{m.performance.latency_ms:.0f}ms</div>
                    <div class="key-metric-label">Response Time</div>
                </div>
                <div class="key-metric-card">
                    <div class="key-metric-value">${m.value.cost_usd:.4f if m.value.cost_usd else 0}</div>
                    <div class="key-metric-label">Cost per Request</div>
                </div>
                <div class="key-metric-card">
                    <div class="key-metric-value">{m.energy.carbon_gco2e:.4f}g</div>
                    <div class="key-metric-label">Carbon Footprint</div>
                </div>
            </div>
        </section>

        <section class="business-value">
            <h2>Business Value</h2>
            <div class="value-proposition">
                <h3>Performance</h3>
                <p>Model achieves {m.performance.accuracy*100:.1f}% accuracy with {m.performance.latency_ms:.0f}ms latency, 
                suitable for {'real-time' if m.performance.latency_ms < 500 else 'batch'} processing scenarios.</p>
                
                <h3>Cost Efficiency</h3>
                <p>Estimated cost per request: ${m.value.cost_usd:.4f if m.value.cost_usd else 'N/A'}. 
                {'ROI: ' + str(m.value.roi*100) + '%' if m.value.roi else 'ROI calculation pending'}.</p>
                
                <h3>Sustainability</h3>
                <p>Carbon footprint: {m.energy.carbon_gco2e:.6f} gCO2e per request. 
                {'Meets sustainability targets' if m.energy.carbon_gco2e < 0.01 else 'Requires optimization for sustainability goals'}.</p>
            </div>
        </section>

        {charts_html}

        <section class="recommendations-executive">
            <h2>Recommendations</h2>
            {self._generate_recommendations_section(recommendations)}
        </section>
        """

    def _generate_sustainability_content(
        self,
        results: List[EvaluationResult],
        scores: List[Dict[str, Any]],
        charts_html: str,
        recommendations: List[str],
        single_result: bool,
    ) -> str:
        """生成可持续性模板内容"""
        result = results[0]
        m = result.metrics
        
        return f"""
        {self._generate_summary_section(results, scores)}
        
        <section class="sustainability-overview">
            <h2>🌍 Sustainability Overview</h2>
            <div class="carbon-impact">
                <h3>Carbon Footprint</h3>
                <div class="carbon-metrics">
                    <div class="carbon-metric">
                        <span class="carbon-value">{m.energy.carbon_gco2e:.6f}</span>
                        <span class="carbon-unit">gCO2e</span>
                        <span class="carbon-label">per request</span>
                    </div>
                    <div class="carbon-context">
                        <p>Equivalent to {m.energy.carbon_gco2e * 1000 / 2000:.4f} km driven by an average car</p>
                        <p>Or {m.energy.carbon_gco2e * 1000 / 50:.2f} hours of smartphone usage</p>
                    </div>
                </div>
            </div>
        </section>

        <section class="energy-analysis">
            <h2>⚡ Energy Consumption Analysis</h2>
            {self._generate_energy_section(results[0]) if single_result else self._generate_comparison_energy_section(results)}
            {self._generate_efficiency_analysis_section(results[0]) if single_result else ''}
        </section>

        <section class="environmental-impact">
            <h2>🌱 Environmental Impact</h2>
            <div class="impact-assessment">
                <h3>Energy Efficiency</h3>
                <p>Energy consumption: {m.energy.energy_joules:.6f} J per request</p>
                <p>Power efficiency: {m.energy.average_power_watts:.2f} W average</p>
                
                <h3>Carbon Intensity</h3>
                <p>Based on global average carbon intensity: 0.5 kgCO2/kWh</p>
                <p>Using renewable energy could reduce carbon footprint by up to 90%</p>
            </div>
        </section>

        {charts_html}

        <section class="sustainability-recommendations">
            <h2>💚 Sustainability Recommendations</h2>
            {self._generate_recommendations_section(recommendations)}
            <div class="green-suggestions">
                <h3>Green Computing Practices</h3>
                <ul>
                    <li>Use renewable energy sources for model inference</li>
                    <li>Optimize model architecture to reduce computational requirements</li>
                    <li>Implement model quantization to reduce energy consumption</li>
                    <li>Schedule batch processing during off-peak hours</li>
                </ul>
            </div>
        </section>

        {self._generate_performance_section(results[0]) if single_result else self._generate_comparison_performance_section(results)}
        """

    def _generate_df_lca_indicators_section(self, part2: Dict[str, Any]) -> str:
        """生成DF-LCA Part 2指标部分"""
        indicators = part2.get("indicators", {})
        if not indicators:
            return ""
        
        html = """
        <section class="df-lca-indicators">
            <h2>DF-LCA Part 2 Standardized Indicators</h2>
            <p>The following indicators are calculated according to DF-LCA Part 2 methodology:</p>
            <table class="indicators-table">
                <thead>
                    <tr>
                        <th>Indicator</th>
                        <th>Symbol</th>
                        <th>Value</th>
                        <th>Unit</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        indicator_names = {
            "I_MI_mips_per_byte": ("MIPS per Byte", "I_MI", "MIPS/byte"),
            "I_FO_flop_per_byte": ("FLOPs per Byte", "I_FO", "FLOPs/byte"),
            "I_DS_bytes_per_s": ("Data Speed", "I_DS", "bytes/s"),
            "I_EC_j_per_byte": ("Energy Consumption", "I_EC", "J/byte"),
            "I_CE_gco2e_per_byte": ("Carbon Emission", "I_CE", "gCO2e/byte"),
            "I_EffortRate_per_byte": ("Effort Rate", "I_ER", "J/byte"),
        }
        
        for key, value in indicators.items():
            if value is not None:
                name, symbol, unit = indicator_names.get(key, (key.replace("_", " ").title(), key, ""))
                html += f"""
                    <tr>
                        <td>{name}</td>
                        <td><code>{symbol}</code></td>
                        <td>{value:.6f}</td>
                        <td>{unit}</td>
                    </tr>
                """
        
        html += """
                </tbody>
            </table>
        </section>
        """
        return html

    def _get_css(self, template: str = "engineering") -> str:
        """Get CSS styles for the report with template-specific styles."""
        base_css = """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        header {
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        header h1 {
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .timestamp {
            color: #7f8c8d;
            font-size: 0.9em;
        }
        section {
            margin-bottom: 40px;
        }
        h2 {
            color: #2c3e50;
            font-size: 1.8em;
            margin-bottom: 20px;
            border-left: 4px solid #4CAF50;
            padding-left: 15px;
        }
        h3 {
            color: #34495e;
            font-size: 1.3em;
            margin: 20px 0 10px 0;
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        .summary-item {
            display: flex;
            flex-direction: column;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 5px;
        }
        .summary-item .label {
            font-size: 0.9em;
            color: #7f8c8d;
            margin-bottom: 5px;
        }
        .summary-item .value {
            font-size: 1.2em;
            font-weight: bold;
            color: #2c3e50;
        }
        .score-value {
            color: #4CAF50;
            font-size: 1.5em;
        }
        .score-breakdown {
            margin: 20px 0;
        }
        .score-item {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
            gap: 15px;
        }
        .score-label {
            min-width: 150px;
            font-weight: 500;
        }
        .score-bar {
            flex: 1;
            height: 25px;
            background: #e0e0e0;
            border-radius: 12px;
            overflow: hidden;
        }
        .score-fill {
            height: 100%;
            background: linear-gradient(90deg, #4CAF50, #8BC34A);
            transition: width 0.3s;
        }
        .score-value {
            min-width: 60px;
            text-align: right;
            font-weight: bold;
        }
        .total-score {
            margin-top: 20px;
            padding: 20px;
            background: #e8f5e9;
            border-radius: 5px;
            text-align: center;
        }
        .total-label {
            font-size: 1.2em;
            margin-right: 10px;
        }
        .total-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #2e7d32;
        }
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
        }
        .chart-container {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        .metric-card {
            padding: 20px;
            background: #f8f9fa;
            border-radius: 5px;
            border-left: 4px solid #4CAF50;
        }
        .metric-label {
            font-size: 0.9em;
            color: #7f8c8d;
            margin-bottom: 10px;
        }
        .metric-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #2c3e50;
        }
        .comparison-table {
            overflow-x: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background: #4CAF50;
            color: white;
            font-weight: 600;
        }
        tr:hover {
            background: #f5f5f5;
        }
        .efficiency-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
        }
        .efficiency-item {
            padding: 15px;
            background: #e8f5e9;
            border-radius: 5px;
            display: flex;
            justify-content: space-between;
        }
        .efficiency-label {
            font-weight: 500;
        }
        .efficiency-value {
            font-weight: bold;
            color: #2e7d32;
        }
        .recommendations-list {
            list-style: none;
            padding: 0;
        }
        .recommendations-list li {
            padding: 15px;
            margin-bottom: 10px;
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            border-radius: 5px;
        }
        .details-content {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
        }
        .details-content pre {
            background: white;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            margin: 10px 0;
        }
        @media print {
            body {
                background: white;
                padding: 0;
            }
            .container {
                box-shadow: none;
            }
        }
        .template-badge {
            display: inline-block;
            padding: 4px 12px;
            background: #e3f2fd;
            border-radius: 12px;
            font-size: 0.85em;
            color: #1976d2;
            margin-left: 10px;
        }
        """
        
        # Template-specific styles
        template_styles = {
            "academic": """
        .template-academic {
            font-family: 'Times New Roman', Times, serif;
        }
        .template-academic header {
            border-bottom: 2px solid #1a237e;
        }
        .template-academic h2 {
            border-left: 4px solid #1a237e;
            color: #1a237e;
        }
        .abstract-section, .methodology-section, .results-section, .discussion-section, .references-section {
            margin: 30px 0;
        }
        .indicators-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        .indicators-table th {
            background: #1a237e;
            color: white;
            padding: 10px;
            text-align: left;
        }
        .indicators-table td {
            padding: 8px;
            border-bottom: 1px solid #ddd;
        }
        .indicators-table code {
            background: #f5f5f5;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }
            """,
            "executive": """
        .template-executive {
            font-family: 'Arial', sans-serif;
        }
        .template-executive header {
            border-bottom: 3px solid #1565c0;
        }
        .template-executive h2 {
            border-left: 4px solid #1565c0;
            color: #1565c0;
        }
        .key-metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .key-metric-card {
            background: linear-gradient(135deg, #1565c0 0%, #0d47a1 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .key-metric-value {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .key-metric-label {
            font-size: 1em;
            opacity: 0.9;
        }
        .value-proposition {
            background: #f5f5f5;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .value-proposition h3 {
            color: #1565c0;
            margin-top: 15px;
        }
            """,
            "sustainability": """
        .template-sustainability {
            font-family: 'Arial', sans-serif;
        }
        .template-sustainability header {
            border-bottom: 3px solid #2e7d32;
        }
        .template-sustainability h2 {
            border-left: 4px solid #2e7d32;
            color: #2e7d32;
        }
        .carbon-impact {
            background: linear-gradient(135deg, #c8e6c9 0%, #a5d6a7 100%);
            padding: 30px;
            border-radius: 10px;
            margin: 20px 0;
        }
        .carbon-metrics {
            display: flex;
            align-items: center;
            gap: 30px;
            flex-wrap: wrap;
        }
        .carbon-metric {
            text-align: center;
        }
        .carbon-value {
            font-size: 3em;
            font-weight: bold;
            color: #1b5e20;
            display: block;
        }
        .carbon-unit {
            font-size: 1.2em;
            color: #2e7d32;
            margin-left: 5px;
        }
        .carbon-label {
            display: block;
            margin-top: 10px;
            color: #4caf50;
            font-weight: 500;
        }
        .carbon-context {
            flex: 1;
            min-width: 200px;
        }
        .carbon-context p {
            margin: 5px 0;
            color: #2e7d32;
        }
        .impact-assessment {
            background: #e8f5e9;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .green-suggestions {
            background: #c8e6c9;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .green-suggestions ul {
            margin: 10px 0;
            padding-left: 20px;
        }
        .green-suggestions li {
            margin: 8px 0;
            color: #1b5e20;
        }
            """,
            "engineering": """
        .template-engineering {
            /* Default engineering style - already in base_css */
        }
            """,
        }
        
        return base_css + template_styles.get(template, "")

    def _get_plotly_js(self) -> str:
        """Get Plotly.js script tag."""
        return '<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>'


# Convenience function
def generate_report(
    evaluation_results: Union[EvaluationResult, List[EvaluationResult]],
    *,
    format: str = "html",
    output_path: Optional[str] = None,
) -> str:
    """
    Convenience function to generate a report.

    Args:
        evaluation_results: Single or list of EvaluationResult
        format: Output format ("html" or "pdf")
        output_path: Optional output file path

    Returns:
        Path to generated report
    """
    generator = ReportGenerator()
    return generator.generate_report(evaluation_results, format=format, output_path=output_path)
