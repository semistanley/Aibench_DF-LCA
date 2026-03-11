from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import require_jwt
from api.db import get_session
from api.jobs import create_job, enqueue_job, get_job
from api.repositories import get_run, list_runs, save_run
from core.schemas import EvaluationRequest, EvaluationResult
from tasks.engine import evaluate_dpu
from utils.reporting import report_markdown, standardized_report

router = APIRouter(prefix="/v1")
router_root = APIRouter()


async def _session_dep():
    async with get_session() as s:
        yield s


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/evaluate", response_model=EvaluationResult)
async def evaluate(req: EvaluationRequest, session: AsyncSession = Depends(_session_dep), _claims=Depends(require_jwt)):
    result = await evaluate_dpu(req)
    await save_run(session, result)
    return result


@router.post("/jobs/evaluate")
async def evaluate_async(req: EvaluationRequest, session: AsyncSession = Depends(_session_dep), _claims=Depends(require_jwt)):
    job_id = await create_job(session, req)
    enqueue_job(req, job_id=job_id)
    return {"job_id": job_id, "status": "queued"}


@router.get("/jobs/{job_id}")
async def read_job(job_id: str, session: AsyncSession = Depends(_session_dep), _claims=Depends(require_jwt)):
    job = await get_job(session, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return {
        "job_id": job.job_id,
        "created_at": job.created_at.isoformat(),
        "status": job.status,
        "run_id": job.run_id,
        "error": job.error,
    }


@router.get("/runs/{run_id}", response_model=EvaluationResult)
async def read_run(run_id: str, session: AsyncSession = Depends(_session_dep), _claims=Depends(require_jwt)):
    result = await get_run(session, run_id)
    if not result:
        raise HTTPException(status_code=404, detail="run not found")
    return result


@router.get("/runs/{run_id}/report")
async def read_run_report(run_id: str, session: AsyncSession = Depends(_session_dep), _claims=Depends(require_jwt)):
    result = await get_run(session, run_id)
    if not result:
        raise HTTPException(status_code=404, detail="run not found")
    return {"json": standardized_report(result), "markdown": report_markdown(result)}


# Root endpoints (no /v1 prefix) to match requested API shape
@router_root.get("/health")
async def health_root():
    return {"status": "ok"}


@router_root.post("/evaluate", response_model=EvaluationResult)
async def evaluate_root(req: EvaluationRequest, session: AsyncSession = Depends(_session_dep), _claims=Depends(require_jwt)):
    result = await evaluate_dpu(req)
    await save_run(session, result)
    return result


@router_root.get("/results/{run_id}", response_model=EvaluationResult)
async def results_root(run_id: str, session: AsyncSession = Depends(_session_dep), _claims=Depends(require_jwt)):
    result = await get_run(session, run_id)
    if not result:
        raise HTTPException(status_code=404, detail="result not found")
    return result


@router_root.get("/leaderboard")
async def leaderboard_root(
    limit: int = Query(default=20, ge=1, le=200),
    session: AsyncSession = Depends(_session_dep),
    _claims=Depends(require_jwt),
):
    runs = await list_runs(session, limit=limit)

    def score(r: EvaluationResult) -> float:
        # Prefer accuracy/quality_score if present; otherwise rank by lowest latency.
        if r.metrics.performance.accuracy is not None:
            return float(r.metrics.performance.accuracy)
        if r.metrics.value.quality_score is not None:
            return float(r.metrics.value.quality_score)
        if r.metrics.performance.latency_ms is not None:
            return -float(r.metrics.performance.latency_ms)
        return float("-inf")

    runs_sorted = sorted(runs, key=score, reverse=True)
    return {
        "items": [
            {
                "run_id": r.run_id,
                "created_at": r.created_at.isoformat(),
                "task_name": r.task_name,
                "provider": r.model.provider.value,
                "model": r.model.model,
                "accuracy": r.metrics.performance.accuracy,
                "quality_score": r.metrics.value.quality_score,
                "latency_ms": r.metrics.performance.latency_ms,
            }
            for r in runs_sorted
        ]
    }

