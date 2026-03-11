from __future__ import annotations

from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from api.settings import settings

engine: AsyncEngine | None = None
SessionLocal: async_sessionmaker[AsyncSession] | None = None


def init_engine() -> AsyncEngine:
    """
    Lazy-init the async engine so importing the app doesn't fail before deps are installed.
    """
    global engine, SessionLocal
    if engine is None:
        try:
            engine = create_async_engine(settings.database_url, echo=False, future=True)
        except ModuleNotFoundError as e:
            raise ModuleNotFoundError(
                "Missing DB dependency. Run: pip install -r requirements.txt"
            ) from e
        SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    return engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    if SessionLocal is None:
        init_engine()
    assert SessionLocal is not None
    return SessionLocal


@asynccontextmanager
async def get_session():
    if SessionLocal is None:
        init_engine()
    assert SessionLocal is not None
    async with SessionLocal() as session:
        yield session

