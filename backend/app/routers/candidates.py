import os
import shutil
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from ..auth import require_auth
from ..config import settings
from ..database import get_db
from ..extraction import extract_candidate  # MOCK - swap for llm-service on Day 6
from ..models_db import Candidate
from ..schemas import (
    DELETABLE_UPLOAD_STATUSES,
    STATUS_VALUES,
    CandidateBase,
    CandidateOut,
    CandidateSummary,
    CandidateUpdate,
)
from ..storage import storage

# Every candidate endpoint requires a valid bearer token (see auth.py).
router = APIRouter(tags=["candidates"], dependencies=[Depends(require_auth)])

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
_STATUS_SET = set(STATUS_VALUES)


def next_candidate_id(db: Session) -> str:
    """7-digit zero-padded running number, one past the highest numeric id in the
    table ('0000001', '0000002', ...). Good enough for a single-writer MVP."""
    ids = db.query(Candidate.candidate_id).all()
    nums = [int(cid) for (cid,) in ids if cid and cid.isdigit()]
    return f"{(max(nums) + 1) if nums else 1:07d}"


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
        upload_status=row.upload_status,
        top_skills=[s.get("skill", "") for s in (row.skills or [])][:5],
        extraction_confidence=row.extraction_confidence,
        created_at=row.created_at,
    ).model_dump(mode="json")


def _matches_keyword(row: Candidate, needle: str) -> bool:
    """`q` search across full_name, email, candidate_id, and skills (skill names
    + tools)."""
    hay = [row.full_name or "", row.email or "", row.candidate_id or ""]
    for s in row.skills or []:
        hay.append(s.get("skill", ""))
        hay.extend(s.get("tools", []) or [])
    return any(needle in h.lower() for h in hay)


@router.get("/candidates")
def list_candidates(
    db: Session = Depends(get_db),
    status: str | None = Query(None, description="exact match on candidate status"),
    applied_position: str | None = Query(None, description="exact match on position"),
    min_experience: float | None = Query(None, description="experience_total >= this"),
    max_experience: float | None = Query(None, description="experience_total <= this"),
    q: str | None = Query(None, description="keyword: full_name, email, skills, candidate_id"),
):
    query = db.query(Candidate)
    if status:
        query = query.filter(Candidate.status == status)
    if applied_position:
        query = query.filter(Candidate.applied_position == applied_position)
    if min_experience is not None:
        query = query.filter(Candidate.experience_total >= min_experience)
    if max_experience is not None:
        query = query.filter(Candidate.experience_total <= max_experience)

    rows = query.order_by(Candidate.created_at.desc()).all()

    if q and q.strip():
        needle = q.strip().lower()
        rows = [r for r in rows if _matches_keyword(r, needle)]

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


@router.delete("/candidates/{candidate_id}")
def delete_candidate(candidate_id: str, db: Session = Depends(get_db)):
    """Cancel upload / delete a candidate - allowed only when the upload is not
    in progress (upload_status in DELETABLE_UPLOAD_STATUSES). Processing -> 400."""
    row = db.get(Candidate, candidate_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Candidate '{candidate_id}' not found")
    if row.upload_status not in DELETABLE_UPLOAD_STATUSES:
        raise HTTPException(
            status_code=400, detail="Cannot cancel/delete file in current status"
        )

    db.delete(row)
    db.commit()

    folder = os.path.join(settings.upload_dir, candidate_id)
    if os.path.isdir(folder):
        shutil.rmtree(folder, ignore_errors=True)

    return {"data": {"candidate_id": candidate_id, "deleted": True}, "error": None}


@router.post("/candidates/upload", status_code=201)
async def upload_candidates(
    files: list[UploadFile] = File(...), db: Session = Depends(get_db)
):
    """Batch upload. Each .pdf/.docx file -> stored + running id + extraction +
    persisted. Returns a per-file summary; a bad file fails only its own entry."""
    created: list[dict] = []
    failed: list[dict] = []

    for file in files:
        name = file.filename or ""
        ext = os.path.splitext(name)[1].lower()

        # --- cheap validation first: no row is created for a rejected file ---
        try:
            if ext not in ALLOWED_EXTENSIONS:
                raise ValueError(
                    f"Unsupported file type '{ext or '?'}'. Allowed: .pdf, .docx"
                )
            content = await file.read()
            if not content:
                raise ValueError("Uploaded file is empty")
            if len(content) > settings.max_upload_mb * 1024 * 1024:
                raise ValueError(f"File too large (max {settings.max_upload_mb} MB)")
        except ValueError as exc:
            failed.append({"filename": name, "error": str(exc)})
            continue

        # --- row lands as Processing, then flips to Done (or Failed) ---
        candidate_id = next_candidate_id(db)
        row = Candidate(candidate_id=candidate_id, upload_status="Processing")
        db.add(row)
        db.commit()

        try:
            stored = storage.save(candidate_id, name or f"{candidate_id}{ext}", content)

            # ---------------- MOCK EXTRACTION BOUNDARY ----------------
            # Day 6: swap the `extract_candidate` import above for Member 4's
            # llm-service function. Frozen signature:
            #   extract_candidate(file_bytes: bytes, filename: str | None = None) -> dict
            raw = extract_candidate(content, filename=name)
            # ---------------------------------------------------------
            fields = CandidateBase.model_validate(raw).model_dump(mode="json")

            for key, value in fields.items():
                setattr(row, key, value)
            row.resume_url = stored["url"]
            row.resume_filename = stored["filename"]
            row.upload_status = "Done"
            row.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(row)
            created.append(_to_out(row))
        except Exception as exc:  # extraction / storage failure - keep the row as Failed
            db.rollback()
            row = db.get(Candidate, candidate_id)
            if row is not None:
                row.upload_status = "Failed"
                row.raw_text_snippet = f"[upload failed] {exc}"[:500]
                db.commit()
            failed.append(
                {"filename": name, "candidate_id": candidate_id,
                 "error": f"Processing failed: {exc}"}
            )

    if not created and failed:
        # nothing succeeded -> surface as a 400 with the collected errors
        raise HTTPException(status_code=400, detail=failed[0]["error"])

    return {
        "data": {"created": created, "failed": failed, "count": len(created)},
        "error": None,
    }
