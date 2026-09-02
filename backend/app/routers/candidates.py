import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..extraction import extract_candidate  # MOCK - swap for llm-service on Day 6
from ..models_db import Candidate
from ..schemas import (
    STATUS_VALUES,
    CandidateBase,
    CandidateOut,
    CandidateSummary,
    CandidateUpdate,
)
from ..storage import storage

router = APIRouter(tags=["candidates"])

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
_STATUS_SET = set(STATUS_VALUES)


def _to_out(row: Candidate) -> dict:
    return CandidateOut.model_validate(row).model_dump(mode="json")


def _to_summary(row: Candidate) -> dict:
    return CandidateSummary(
        candidate_id=row.candidate_id,
        full_name=row.full_name,
        applied_position=row.applied_position,
        location=row.location,
        email=row.email,
        phone=row.phone,
        experience_total=row.experience_total,
        status=row.status,
        top_skills=[s.get("skill", "") for s in (row.skills or [])][:5],
        extraction_confidence=row.extraction_confidence,
        created_at=row.created_at,
    ).model_dump(mode="json")


@router.get("/candidates")
def list_candidates(db: Session = Depends(get_db)):
    rows = db.query(Candidate).order_by(Candidate.created_at.desc()).all()
    return {"data": [_to_summary(r) for r in rows], "error": None}


@router.get("/candidates/{candidate_id}")
def get_candidate(candidate_id: str, db: Session = Depends(get_db)):
    row = db.get(Candidate, candidate_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Candidate '{candidate_id}' not found")
    return {"data": _to_out(row), "error": None}


@router.put("/candidates/{candidate_id}")
def update_candidate(
    candidate_id: str, payload: CandidateUpdate, db: Session = Depends(get_db)
):
    row = db.get(Candidate, candidate_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Candidate '{candidate_id}' not found")

    data = payload.model_dump(mode="json")
    if data["email"] and "@" not in data["email"]:
        raise HTTPException(status_code=400, detail="Invalid email format")
    if data["status"] not in _STATUS_SET:
        raise HTTPException(status_code=400, detail=f"Invalid status '{data['status']}'")

    for key, value in data.items():
        setattr(row, key, value)
    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return {"data": _to_out(row), "error": None}


@router.get("/candidates/{candidate_id}/resume-url")
def get_resume_url(candidate_id: str, db: Session = Depends(get_db)):
    row = db.get(Candidate, candidate_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Candidate '{candidate_id}' not found")
    return {
        "data": {"resume_url": row.resume_url, "filename": row.resume_filename},
        "error": None,
    }


@router.post("/candidates/upload", status_code=201)
async def upload_candidate(
    file: UploadFile = File(...), db: Session = Depends(get_db)
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext or '?'}'. Allowed: .pdf, .docx",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(
            status_code=400, detail=f"File too large (max {settings.max_upload_mb} MB)"
        )

    candidate_id = str(uuid.uuid4())
    stored = storage.save(candidate_id, file.filename or f"{candidate_id}{ext}", content)

    # ---------------- MOCK EXTRACTION BOUNDARY ----------------
    # Day 6: replace the `extract_candidate` import above with Member 4's
    # llm-service function. Frozen signature (matches extractor.py):
    #   extract_candidate(file_bytes: bytes, filename: str | None = None) -> dict
    raw = extract_candidate(content, filename=file.filename)
    # ---------------------------------------------------------
    fields = CandidateBase.model_validate(raw).model_dump(mode="json")

    row = Candidate(
        candidate_id=candidate_id,
        resume_url=stored["url"],
        resume_filename=stored["filename"],
        **fields,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"data": _to_out(row), "error": None}
