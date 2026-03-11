from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
try:
    from jose import JWTError, jwt  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    JWTError = Exception  # type: ignore
    jwt = None  # type: ignore


ALGORITHM = "HS256"
_bearer = HTTPBearer(auto_error=False)


def _secret() -> str:
    # For production, set JWT_SECRET explicitly.
    return os.getenv("JWT_SECRET", "dev-secret-change-me")


def create_access_token(payload: Dict[str, Any], *, expires_s: int = 3600) -> str:
    if jwt is None:
        raise ModuleNotFoundError("Missing JWT dependency. Run: pip install -r requirements.txt")
    now = datetime.now(timezone.utc)
    claims = dict(payload)
    claims.setdefault("iat", int(now.timestamp()))
    claims.setdefault("exp", int(now.timestamp()) + int(expires_s))
    return jwt.encode(claims, _secret(), algorithm=ALGORITHM)


def require_jwt(
    cred: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> Dict[str, Any]:
    """
    Dependency for protected endpoints.
    Expects: Authorization: Bearer <jwt>
    """
    if cred is None or not cred.credentials:
        raise HTTPException(status_code=401, detail="missing bearer token")
    if jwt is None:
        raise HTTPException(status_code=500, detail="jwt dependency missing: pip install -r requirements.txt")
    token = cred.credentials
    try:
        return jwt.decode(token, _secret(), algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="invalid token")

