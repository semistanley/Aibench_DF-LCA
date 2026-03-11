from __future__ import annotations

from pydantic import BaseModel, Field


class Settings(BaseModel):
    database_url: str = Field(default="sqlite+aiosqlite:///./ai_bench.sqlite3")


settings = Settings()

