from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_sessionmaker
from api.models import EvaluationJob
from api.repositories import save_run
from core.schemas import EvaluationRequest
from tasks.engine import evaluate_dpu


async def create_job(session: AsyncSession, req: EvaluationRequest) -> str:
    job_id = uuid.uuid4().hex
    job = EvaluationJob(
        job_id=job_id,
        created_at=datetime.now(timezone.utc),
        status="queued",
        request_json=req.model_dump_json(),
        run_id=None,
        error=None,
    )
    session.add(job)
    await session.commit()
    return job_id


async def get_job(session: AsyncSession, job_id: str) -> EvaluationJob | None:
    from sqlalchemy import select

    res = await session.execute(select(EvaluationJob).where(EvaluationJob.job_id == job_id))
    return res.scalar_one_or_none()


async def _set_job_status(
    session: AsyncSession, *, job_id: str, status: str, run_id: str | None = None, error: str | None = None
) -> None:
    from sqlalchemy import update

    stmt = (
        update(EvaluationJob)
        .where(EvaluationJob.job_id == job_id)
        .values(status=status, run_id=run_id, error=error)
    )
    await session.execute(stmt)
    await session.commit()


def enqueue_job(req: EvaluationRequest, *, job_id: str) -> None:
    """
    Run evaluation in background (in-process).
    """

    async def _runner():
        sessionmaker = get_sessionmaker()
        async with sessionmaker() as session:
            await _set_job_status(session, job_id=job_id, status="running")

        try:
            result = await evaluate_dpu(req)
            async with sessionmaker() as session:
                await save_run(session, result)
                await _set_job_status(session, job_id=job_id, status="succeeded", run_id=result.run_id)
        except Exception as e:
            async with sessionmaker() as session:
                await _set_job_status(session, job_id=job_id, status="failed", error=str(e))

    asyncio.create_task(_runner())

