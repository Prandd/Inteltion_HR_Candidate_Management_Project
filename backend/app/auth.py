"""JWT auth over the `hr_accounts` table (F2).

Replaces the single hardcoded admin. The token carries an identity
(`sub` = account_id, plus username / name / role), but `get_current_account()`
still loads the account from the DB on every request rather than trusting the
token body - otherwise a deactivated employee keeps full access for up to 8
hours until their token expires.
"""
from __future__ import annotations

import time

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models_db import HRAccount
from .security import dummy_verify, verify_password

_bearer = HTTPBearer(auto_error=False)

# Identical for "no such user" and "wrong password" - the caller must not be
# able to tell which one it was.
INVALID_CREDENTIALS = "Invalid username or password"


def authenticate(db: Session, username: str, password: str) -> HRAccount | None:
    """Returns the account, or None. Runs a throwaway hash when the username is
    unknown so both branches cost about the same wall time."""
    account = (
        db.query(HRAccount)
        .filter(HRAccount.username == (username or "").strip())
        .one_or_none()
    )
    if account is None:
        dummy_verify()
        return None
    if not verify_password(password or "", account.password_hash):
        return None
    if not account.is_active:
        return None
    return account


def create_access_token(account: HRAccount) -> str:
    now = int(time.time())
    payload = {
        "sub": account.account_id,
        "username": account.username,
        "name": account.full_name,
        "role": account.role,
        "iat": now,
        "exp": now + settings.jwt_expire_minutes * 60,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_account(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> HRAccount:
    """FastAPI dependency - the authenticated HR account, or 401."""
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401, detail="Missing or invalid Authorization header"
        )
    payload = decode_token(creds.credentials)
    account_id = str(payload.get("sub", ""))
    account = db.get(HRAccount, account_id) if account_id else None
    if account is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    if not account.is_active:
        # Deactivation takes effect on the next request, not on token expiry.
        raise HTTPException(status_code=401, detail="Account is deactivated")
    return account


def require_role(*roles: str):
    """Dependency factory - `Depends(require_role("admin"))`."""
    allowed = set(roles)

    def _guard(account: HRAccount = Depends(get_current_account)) -> HRAccount:
        if account.role not in allowed:
            raise HTTPException(
                status_code=403,
                detail=f"Requires role: {', '.join(sorted(allowed))}",
            )
        return account

    return _guard


# Back-compat shim for anything still importing the old name. Returns the
# account_id (what the old `require_auth` returned as the token subject).
def require_auth(account: HRAccount = Depends(get_current_account)) -> str:
    return account.account_id
