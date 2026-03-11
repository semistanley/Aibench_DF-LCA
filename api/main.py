from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from api.db import init_engine
from api.migrations import init_db
from api.routes import router, router_root


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = init_engine()
    await init_db(engine)
    yield


app = FastAPI(title="AI Bench DF-LCA Platform", version="0.1.0", lifespan=lifespan)
app.include_router(router_root)
app.include_router(router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": "validation_error", "errors": exc.errors()},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": "internal_error", "error": str(exc)})

