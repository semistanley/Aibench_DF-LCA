from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict, Optional

import click

from api.db import get_sessionmaker, init_engine
from api.migrations import init_db
from api.repositories import get_run, list_runs, save_run
from core.schemas import EnergyCollectionMethod, EvaluationOptions, EvaluationRequest, ModelProvider
from tasks.engine import evaluate_dpu
from utils.reporting import report_markdown, standardized_report
from models import registry


@click.group()
def benchmark() -> None:
    """Benchmark commands (DF-LCA)."""


@benchmark.group("model")
def model_group() -> None:
    """Model-related commands."""


@model_group.command("list")
def model_list() -> None:
    """List available adapter providers and example model identifiers."""
    click.echo("Registered models:")
    for m in registry.list_all():
        click.echo(
            f"- {m.get('name')} "
            f"(type={m.get('type')}, endpoint={m.get('endpoint')}, "
            f"parameters={m.get('parameters')})"
        )


@benchmark.command("evaluate")
@click.option("--model", "model_name", required=True, help="Model id/name (e.g., gpt-4.1, echo)")
@click.option("--provider", type=click.Choice(["openai", "huggingface", "local"]), default="local", show_default=True)
@click.option("--task", "task_name", required=True, help="Task name (e.g., mmlu)")
@click.option("--prompt", default="hello", show_default=True, help="Prompt for demo evaluation")
@click.option(
    "--energy-method",
    type=click.Choice(["cpu_estimate", "external_meter", "sensors"]),
    default="cpu_estimate",
    show_default=True,
)
def evaluate_cmd(model_name: str, provider: str, task_name: str, prompt: str, energy_method: str) -> None:
    """Run a single evaluation locally and persist to SQLite."""

    async def _run() -> str:
        engine = init_engine()
        await init_db(engine)
        sessionmaker = get_sessionmaker()
        # Prefer registry if available
        try:
            model_cfg = registry.to_model_config(model_name)
        except KeyError:
            from core.schemas import ModelConfig  # local import

            model_cfg = ModelConfig(provider=ModelProvider(provider), model=model_name)
        req = EvaluationRequest(
            task_name=task_name,
            input={"prompt": prompt},
            model=model_cfg,
            options=EvaluationOptions(energy_method=EnergyCollectionMethod(energy_method)),
        )
        result = await evaluate_dpu(req)
        async with sessionmaker() as session:
            await save_run(session, result)
        return result.run_id

    try:
        run_id = asyncio.run(_run())
    except ModuleNotFoundError as e:
        raise click.ClickException(str(e))
    click.echo(f"run_id={run_id}")


@benchmark.group("report")
def report_group() -> None:
    """Report commands."""


@report_group.command("generate")
@click.option("--id", "run_id", required=True, help="Run id")
@click.option("--format", "fmt", type=click.Choice(["json", "md", "html"]), default="html", show_default=True)
@click.option("--out", "out_path", default=None, help="Output file path (optional)")
def report_generate(run_id: str, fmt: str, out_path: str | None) -> None:
    """Generate a standardized report for a run."""

    async def _load():
        engine = init_engine()
        await init_db(engine)
        sessionmaker = get_sessionmaker()
        async with sessionmaker() as session:
            return await get_run(session, run_id)

    try:
        result = asyncio.run(_load())
    except ModuleNotFoundError as e:
        raise click.ClickException(str(e))
    if result is None:
        raise click.ClickException("run not found")

    if fmt == "json":
        content = __import__("json").dumps(standardized_report(result), ensure_ascii=False, indent=2)
        suffix = ".json"
    elif fmt == "md":
        content = report_markdown(result)
        suffix = ".md"
    else:
        md = report_markdown(result)
        content = (
            "<!doctype html><html><head><meta charset='utf-8'>"
            "<title>DF-LCA Report</title></head><body><pre>"
            + __import__("html").escape(md)
            + "</pre></body></html>"
        )
        suffix = ".html"

    if out_path is None:
        out_path = f"report_{run_id}{suffix}"
    Path(out_path).write_text(content, encoding="utf-8")
    click.echo(out_path)


@benchmark.command("leaderboard")
@click.option(
    "--dimension",
    type=click.Choice(["performance", "energy", "value"]),
    default="performance",
    show_default=True,
)
@click.option("--limit", default=20, show_default=True, type=int)
def leaderboard_cmd(dimension: str, limit: int) -> None:
    """Print a simple leaderboard sorted by dimension."""

    async def _load():
        engine = init_engine()
        await init_db(engine)
        sessionmaker = get_sessionmaker()
        async with sessionmaker() as session:
            return await list_runs(session, limit=limit)

    try:
        runs = asyncio.run(_load())
    except ModuleNotFoundError as e:
        raise click.ClickException(str(e))

    def key_fn(r):
        if dimension == "energy":
            v = r.metrics.energy.energy_joules
            return float(v) if v is not None else float("inf")  # lower is better
        if dimension == "value":
            v = r.metrics.value.quality_score
            return -(float(v) if v is not None else float("-inf"))  # higher is better
        # performance: lower latency is better
        v = r.metrics.performance.latency_ms
        return float(v) if v is not None else float("inf")

    runs_sorted = sorted(runs, key=key_fn)
    click.echo(f"Leaderboard ({dimension})")
    for i, r in enumerate(runs_sorted, start=1):
        click.echo(
            f"{i:>2}. {r.run_id} task={r.task_name} model={r.model.provider.value}:{r.model.model} "
            f"latency_ms={r.metrics.performance.latency_ms} energy_j={r.metrics.energy.energy_joules} "
            f"quality={r.metrics.value.quality_score}"
        )

