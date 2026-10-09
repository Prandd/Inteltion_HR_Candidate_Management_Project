"""Job openings/requisitions.

Reverse-engineered from frontend/dashboard's Positions.tsx,
PositionDetail.tsx and PositionRequirements.tsx pages - there was no
prior contract, schema, or backend route for this resource at all on
this branch. Scope is deliberately limited to exactly what those three
pages call: list, get-one, create. No PUT/DELETE/status-change endpoint
exists because nothing in the frontend calls one yet.

Any logged-in account may list, read, or create a position - none of
the three pages show role-specific UI, so there is nothing to gate here
beyond "must be authenticated", same as the rest of the API.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_account
from ..database import get_db
from ..models_db import Candidate, HRAccount, Position, utcnow
from ..schemas import PositionCreate, PositionOut, PositionSummaryOut

router = APIRouter(tags=["positions"])


def _candidate_count(db: Session, title: str) -> int:
    # Best-effort match by name: candidates carry `applied_position` as free
    # text (HR-assigned after upload), not a foreign key to a position, so
    # there is no stronger join available here.
    return db.query(Candidate).filter(Candidate.applied_position == title).count()


def _get_or_404(db: Session, position_id: str) -> Position:
    row = db.get(Position, position_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Position '{position_id}' not found")
    return row


def _to_summary(db: Session, row: Position) -> dict:
    return PositionSummaryOut(
        id=row.position_id,
        title=row.title,
        department=row.department,
        location=row.location,
        status=row.status,
        candidate_count=_candidate_count(db, row.title),
    ).model_dump(mode="json")


def _to_out(db: Session, row: Position) -> dict:
    return PositionOut(
        id=row.position_id,
        title=row.title,
        department=row.department,
        description=row.description,
        location=row.location,
        skills=row.skills or [],
        status=row.status,
        candidate_count=_candidate_count(db, row.title),
    ).model_dump(mode="json")


@router.get("/positions")
def list_positions(
    db: Session = Depends(get_db),
    _account: HRAccount = Depends(get_current_account),
):
    rows = db.query(Position).order_by(Position.created_at.desc()).all()
    return {"data": [_to_summary(db, r) for r in rows], "error": None}


@router.get("/positions/{position_id}")
def get_position(
    position_id: str,
    db: Session = Depends(get_db),
    _account: HRAccount = Depends(get_current_account),
):
    row = _get_or_404(db, position_id)
    return {"data": _to_out(db, row), "error": None}


@router.post("/positions", status_code=201)
def create_position(
    payload: PositionCreate,
    db: Session = Depends(get_db),
    _account: HRAccount = Depends(get_current_account),
):
    now = utcnow()
    row = Position(
        position_id=str(uuid.uuid4()),
        title=payload.title.strip(),
        department=payload.department.strip(),
        description=payload.description,
        location=payload.location.strip(),
        skills=payload.skills,
        status="Open",
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"data": _to_out(db, row), "error": None}
