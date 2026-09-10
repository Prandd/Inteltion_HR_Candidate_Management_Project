"""Minimal JWT auth for the single Admin/HR account.

One account, credentials from settings (env-overridable, default admin/password123).
`POST /api/auth/login` -> bearer token; `require_auth` guards /api/candidates/*.
No user table, no refresh tokens - this is an internal MVP.
"""
from __future__ import annotations

import time

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings

_bearer = HTTPBearer(auto_error=False)


def authenticate(username: str, password: str) -> bool:
    return username == settings.auth_username and password == settings.auth_password


def create_access_token(subject: str) -> str:
    now = int(time.time())
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + settings.jwt_expire_minutes * 60,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def require_auth(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    """FastAPI dependency - returns the token subject, or raises 401."""
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    try:
        payload = jwt.decode(
            creds.credentials, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return str(payload.get("sub", ""))
