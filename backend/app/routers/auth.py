from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import INVALID_CREDENTIALS, authenticate, create_access_token, get_current_account
from ..database import get_db
from ..models_db import HRAccount, utcnow
from ..schemas import AccountInfo, ChangePasswordRequest, LoginRequest
from ..security import hash_password, login_limiter, verify_password

router = APIRouter(tags=["auth"])


def _account_info(account: HRAccount) -> dict:
    return AccountInfo.model_validate(account).model_dump(mode="json")


@router.post("/auth/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """DB-backed login. Returns a bearer token plus the caller's account, so the
    frontend can render "commenting as ..." without a second round trip."""
    if login_limiter.is_blocked(payload.username):
        retry_after = login_limiter.retry_after_seconds(payload.username)
        # The header goes on the exception, not on an injected Response: raising
        # discards that object and the error handler builds a fresh response.
        raise HTTPException(
            status_code=429,
            detail=(
                "Too many failed login attempts. "
                f"Try again in {max(1, retry_after // 60)} minute(s)."
            ),
            headers={"Retry-After": str(retry_after)},
        )

    account = authenticate(db, payload.username, payload.password)
    if account is None:
        login_limiter.record_failure(payload.username)
        # Same message for unknown user, wrong password and deactivated account.
        raise HTTPException(status_code=401, detail=INVALID_CREDENTIALS)

    login_limiter.reset(payload.username)
    account.last_login_at = utcnow()
    db.commit()
    db.refresh(account)

    return {
        "data": {
            "access_token": create_access_token(account),
            "token_type": "bearer",
            "account": _account_info(account),
        },
        "error": None,
    }


@router.get("/auth/me")
def me(account: HRAccount = Depends(get_current_account)):
    """Who the caller is. The frontend needs this before rendering comment
    edit/delete controls - ownership is enforced server-side either way."""
    return {"data": _account_info(account), "error": None}


@router.post("/auth/change-password")
def change_password(
    payload: ChangePasswordRequest,
    account: HRAccount = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.old_password, account.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if payload.new_password == payload.old_password:
        raise HTTPException(
            status_code=400, detail="New password must differ from the current one"
        )

    account.password_hash = hash_password(payload.new_password)
    account.updated_at = utcnow()
    db.commit()
    return {"data": {"account_id": account.account_id, "changed": True}, "error": None}
