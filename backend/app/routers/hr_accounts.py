"""F2 - HR account management. Admin only.

Note the DELETE: it deactivates. `comment_logs`, `status_history` and
`resume_versions` all reference account_id, so a hard delete would either orphan
or cascade away the history this project exists to keep.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..auth import require_role
from ..database import get_db
from ..models_db import HRAccount, utcnow
from ..schemas import HRAccountCreate, HRAccountOut, HRAccountUpdate, ResetPasswordRequest
from ..security import hash_password

router = APIRouter(
    tags=["hr-accounts"], dependencies=[Depends(require_role("admin"))]
)


def _out(row: HRAccount) -> dict:
    return HRAccountOut.model_validate(row).model_dump(mode="json")


def _get_or_404(db: Session, account_id: str) -> HRAccount:
    row = db.get(HRAccount, account_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Account '{account_id}' not found")
    return row


@router.get("/hr-accounts")
def list_accounts(
    db: Session = Depends(get_db),
    is_active: bool | None = Query(None, description="filter on active/deactivated"),
):
    # Filtered in Python, not SQL: comparing a Boolean column to the Python
    # True/False singleton compiles to `IS 1`/`IS 0` in SQLAlchemy, and SQL
    # Server's IS only accepts NULL - `== is_active` 500s there every time.
    rows = db.query(HRAccount).order_by(HRAccount.created_at.asc()).all()
    if is_active is not None:
        rows = [r for r in rows if r.is_active == is_active]
    return {"data": [_out(r) for r in rows], "error": None}


@router.post("/hr-accounts", status_code=201)
def create_account(payload: HRAccountCreate, db: Session = Depends(get_db)):
    username = payload.username.strip()
    if db.query(HRAccount).filter(HRAccount.username == username).first():
        raise HTTPException(status_code=409, detail=f"Username '{username}' already exists")
    if db.query(HRAccount).filter(HRAccount.email == payload.email).first():
        raise HTTPException(status_code=409, detail=f"Email '{payload.email}' already exists")

    now = utcnow()
    row = HRAccount(
        account_id=str(uuid.uuid4()),
        username=username,
        email=payload.email,
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"data": _out(row), "error": None}


@router.put("/hr-accounts/{account_id}")
def update_account(
    account_id: str, payload: HRAccountUpdate, db: Session = Depends(get_db)
):
    row = _get_or_404(db, account_id)
    data = payload.model_dump(exclude_unset=True)

    if "email" in data and data["email"]:
        clash = (
            db.query(HRAccount)
            .filter(HRAccount.email == data["email"], HRAccount.account_id != account_id)
            .first()
        )
        if clash:
            raise HTTPException(
                status_code=409, detail=f"Email '{data['email']}' already exists"
            )

    for key, value in data.items():
        if value is not None:
            setattr(row, key, value)
    row.updated_at = utcnow()
    db.commit()
    db.refresh(row)
    return {"data": _out(row), "error": None}


@router.post("/hr-accounts/{account_id}/reset-password")
def reset_password(
    account_id: str, payload: ResetPasswordRequest, db: Session = Depends(get_db)
):
    """Admin-set temporary password. The holder should change it immediately via
    POST /api/auth/change-password."""
    row = _get_or_404(db, account_id)
    row.password_hash = hash_password(payload.new_password)
    row.updated_at = utcnow()
    db.commit()
    return {"data": {"account_id": account_id, "reset": True}, "error": None}


@router.delete("/hr-accounts/{account_id}")
def deactivate_account(
    account_id: str,
    db: Session = Depends(get_db),
    caller: HRAccount = Depends(require_role("admin")),
):
    """Soft delete - sets is_active = false. See the module docstring."""
    row = _get_or_404(db, account_id)
    if row.account_id == caller.account_id:
        raise HTTPException(
            status_code=400,
            detail="You cannot deactivate the account you are logged in with",
        )
    # Filtered in Python: comparing is_active to a bool literal in SQL hits
    # the same `IS 1` problem noted in list_accounts() above.
    remaining_admins = sum(
        1
        for a in db.query(HRAccount).filter(
            HRAccount.role == "admin", HRAccount.account_id != account_id
        )
        if a.is_active
    )
    if row.role == "admin" and row.is_active and remaining_admins == 0:
        raise HTTPException(
            status_code=400, detail="Cannot deactivate the last active admin account"
        )

    row.is_active = False
    row.updated_at = utcnow()
    db.commit()
    return {"data": {"account_id": account_id, "is_active": False}, "error": None}
