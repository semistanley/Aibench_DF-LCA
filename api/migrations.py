from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine

from api.models import Base, SchemaVersion


SCHEMA_VERSION = "0001_initial"


async def init_db(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # record schema version (best-effort)
        await conn.execute(
            SchemaVersion.__table__.insert().values(version=SCHEMA_VERSION).prefix_with("OR IGNORE")
        )

