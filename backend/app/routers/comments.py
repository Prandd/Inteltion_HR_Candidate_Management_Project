"""F3 - comment_logs CRUD.

Server rules that are NOT negotiable, and are all enforced here rather than in
the frontend:

1. `author_account_id` / `author_name` / `author_role` come only from the JWT.
   Anything the client sends for them is dropped (the Pydantic bodies simply do
   not declare the fields).
2. `candidate_id` comes from the URL path and is never updatable.
3. Ownership on PUT/DELETE is checked server-side. A hidden button is a
   convenience, not a control.
4. `created_at` is untouchable. A PUT that includes it is ignored.
5. `comment` must be non-empty after trimming (enforced in schemas.py).

Admin override, per the round-4 decision: an admin may DELETE anyone's comment
(moderation) but may not EDIT one (attribution integrity - an edited comment
still carries the original author's name).

Round 5: PUT/DELETE are also mounted at `/candidates/comments/{id}` (in
addition to the canonical `/comments/{id}`) purely as a compatibility alias -
`feature/frontend-update` was built calling the `/candidates`-prefixed path.
Both point at the exact same handler and enforce the exact same rules above;
nothing about ownership or immutability changes based on which path was used.
This is additive and safe regardless of how the wider contract mismatch with
the frontend gets resolved - see FRONTEND_CONTRACT_GAPS.md.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..auth import get_current_account
from ..database import get_db
from ..models_db import Candidate, CommentLog, HRAccount, utcnow
from ..schemas import (
    COMMENT_TYPE_VALUES,
    DEFAULT_COMMENT_TYPE_FOR_ROLE,
    CommentCreate,
    CommentOut,
    CommentUpdate,
)

router = APIRouter(tags=["comments"])


def _out(row: CommentLog) -> dict:
    return CommentOut.model_validate(row).model_dump(mode="json")


def _live_comment_or_404(db: Session, comment_id: str) -> CommentLog:
    row = db.get(CommentLog, comment_id)
    if row is None or row.deleted_at is not None:
        raise HTTPException(status_code=404, detail=f"Comment '{comment_id}' not found")
    return row


def _candidate_or_404(db: Session, candidate_id: str) -> Candidate:
    row = db.get(Candidate, candidate_id)
    if row is None:
        raise HTTPException(
            status_code=404, detail=f"Candidate '{candidate_id}' not found"
        )
    return row


@router.get("/candidates/{candidate_id}/comments")
def list_comments(
    candidate_id: str,
    db: Session = Depends(get_db),
    _account: HRAccount = Depends(get_current_account),
    comment_type: str | None = Query(None, description=f"one of {COMMENT_TYPE_VALUES}"),
):
    _candidate_or_404(db, candidate_id)
    query = db.query(CommentLog).filter(
        CommentLog.candidate_id == candidate_id,
        CommentLog.deleted_at.is_(None),  # soft-deleted comments never reach the UI
    )
    if comment_type:
        query = query.filter(CommentLog.comment_type == comment_type)
    rows = query.order_by(CommentLog.commented_at.desc()).all()
    return {"data": [_out(r) for r in rows], "error": None}


@router.post("/candidates/{candidate_id}/comments", status_code=201)
def create_comment(
    candidate_id: str,
    payload: CommentCreate,
    db: Session = Depends(get_db),
    account: HRAccount = Depends(get_current_account),
):
    _candidate_or_404(db, candidate_id)

    now = utcnow()
    row = CommentLog(
        comment_id=str(uuid.uuid4()),
        candidate_id=candidate_id,                      # from the path, rule 2
        author_account_id=account.account_id,           # from the JWT, rule 1
        author_name=account.full_name or account.username,
        author_role=account.role,
        comment_type=(
            payload.comment_type
            or DEFAULT_COMMENT_TYPE_FOR_ROLE.get(account.role, "general")
        ),
        comment=payload.comment,
        commented_at=payload.commented_at or now,       # backdating is allowed
        created_at=now,                                 # audit truth, rule 4
        updated_at=now,
        is_edited=False,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"data": _out(row), "error": None}


@router.put("/comments/{comment_id}")
@router.put("/candidates/comments/{comment_id}")  # compatibility alias - see below
def update_comment(
    comment_id: str,
    payload: CommentUpdate,
    db: Session = Depends(get_db),
    account: HRAccount = Depends(get_current_account),
):
    row = _live_comment_or_404(db, comment_id)
    if row.author_account_id != account.account_id:
        # Admins are not exempt here - see the module docstring.
        raise HTTPException(
            status_code=403, detail="Only the author can edit this comment"
        )

    data = payload.model_dump(exclude_unset=True)
    touched = False
    for field in ("comment", "comment_type", "commented_at"):
        if data.get(field) is not None:
            setattr(row, field, data[field])
            touched = True

    if touched:
        row.is_edited = True
        row.updated_at = utcnow()  # created_at deliberately untouched
        db.commit()
        db.refresh(row)
    return {"data": _out(row), "error": None}


@router.delete("/comments/{comment_id}")
@router.delete("/candidates/comments/{comment_id}")  # compatibility alias - see below
def delete_comment(
    comment_id: str,
    db: Session = Depends(get_db),
    account: HRAccount = Depends(get_current_account),
):
    """Soft delete. PDPA and the M3 audit-log requirement point the same way: a
    deleted comment should leave the UI, not the record."""
    row = _live_comment_or_404(db, comment_id)
    if row.author_account_id != account.account_id and account.role != "admin":
        raise HTTPException(
            status_code=403, detail="Only the author or an admin can delete this comment"
        )

    row.deleted_at = utcnow()
    row.updated_at = row.deleted_at
    db.commit()
    return {"data": {"comment_id": comment_id, "deleted": True}, "error": None}
