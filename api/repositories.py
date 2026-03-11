from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import EvaluationRun
from core.schemas import EvaluationResult
from utils.jsonutil import dumps, loads


async def save_run(session: AsyncSession, result: EvaluationResult) -> None:
    row = EvaluationRun(
        run_id=result.run_id,
        created_at=result.created_at,
        task_name=result.task_name,
        provider=result.model.provider.value,
        model=result.model.model,
        input_json=dumps(result.input),
        output_json=dumps(result.output),
        metrics_json=result.metrics.model_dump_json(),
        tags_json=dumps(result.tags),
        latency_ms=result.metrics.performance.latency_ms,
        energy_joules=result.metrics.energy.energy_joules,
        cost_usd=result.metrics.value.cost_usd,
    )
    session.add(row)
    await session.commit()


async def get_run(session: AsyncSession, run_id: str) -> EvaluationResult | None:
    res = await session.execute(select(EvaluationRun).where(EvaluationRun.run_id == run_id))
    row = res.scalar_one_or_none()
    if not row:
        return None

    # Rehydrate into EvaluationResult (lossy for ModelConfig fields not stored in table)
    from core.schemas import ModelConfig, ModelProvider, RunMetrics

    metrics = RunMetrics.model_validate_json(row.metrics_json)
    model = ModelConfig(provider=ModelProvider(row.provider), model=row.model)
    return EvaluationResult(
        run_id=row.run_id,
        created_at=row.created_at,
        task_name=row.task_name,
        model=model,
        input=loads(row.input_json),
        output=loads(row.output_json),
        metrics=metrics,
        artifacts=[],
        tags=loads(row.tags_json or "{}"),
    )


async def list_runs(session: AsyncSession, *, limit: int = 50) -> list[EvaluationResult]:
    res = await session.execute(select(EvaluationRun).order_by(EvaluationRun.created_at.desc()).limit(limit))
    rows = res.scalars().all()
    out: list[EvaluationResult] = []
    for row in rows:
        r = await get_run(session, row.run_id)
        if r:
            out.append(r)
    return out

