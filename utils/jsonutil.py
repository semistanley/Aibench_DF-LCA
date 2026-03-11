from __future__ import annotations

import json
from datetime import datetime
from typing import Any


def dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, default=_default, separators=(",", ":"))


def loads(s: str) -> Any:
    return json.loads(s)


def _default(o: Any) -> Any:
    if isinstance(o, datetime):
        return o.isoformat()
    raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")

