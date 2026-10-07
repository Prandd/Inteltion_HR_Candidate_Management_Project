import os
import sys
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from ..auth import get_current_account
from ..config import settings
from ..database import get_db


LLM_SERVICE_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../../../llm-service/cv-parsing"
    )
)

if LLM_SERVICE_PATH not in sys.path:
    sys.path.insert(0, LLM_SERVICE_PATH)

from extractor import extract_candidate

from ..models_db import (
    Candidate,
    CandidateChangeLog,
    CommentLog,
    HRAccount,
    OwnershipHistory,
    PendingUpload,
    ResumeVersion,
    SqlTestScore,
    StatusHistory,
    utcnow,
)
from ..schemas import (
    DELETABLE_UPLOAD_STATUSES,
    STATUS_SET,
    STATUS_VALUES,
    CandidateBase,
    CandidateSummary,
    CandidateUpdate,
    ChangeLogOut,
    OwnershipHistoryOut,
    ResumeVersionOut,
    SqlTestScoreIn,
    SqlTestScoreOut,
    StatusChangeRequest,
    StatusHistoryOut,
    TransferOwnershipRequest,
)
from ..services import (
    apply_status_change,
    assign_initial_owner,
    candidate_out,
    find_duplicate_hints,
    merge_on_reupload,
    next_candidate_id,
    normalize_email,
    owner_names_for,
    pending_upload_preview,
    record_change,
    record_sql_test_score,
    store_resume,
    transfer_ownership,
)
from ..statuses import REJECTED_STATES
from ..storage import storage

# Every candidate endpoint requires a valid bearer token (see auth.py).
router = APIRouter(tags=["candidates"], dependencies=[Depends(get_current_account)])

ALLOWED_EXTENSIONS = {".pdf", ".docx"}


def _to_out(row: Candidate, db: Session):
    if row.updated_at is None:
        row.updated_at = row.created_at or datetime.now(timezone.utc)
    return candidate_out(db, row)


def _to_summary(row: Candidate, owner_names: dict[str, str] | None = None) -> dict:
    owner_names = owner_names or {}
    return CandidateSummary(
        candidate_id=row.candidate_id,
        full_name=row.full_name,
        applied_position=row.applied_position,
        location=row.location,
        email=row.email,
        phone=row.phone,
        experience_total=row.experience_total,
        status=row.status,
        before_rejected_status=row.before_rejected_status or "",
        upload_status=row.upload_status,
        top_skills=[s.get("skill", "") for s in (row.skills or [])][:5],
        extraction_confidence=row.extraction_confidence,
        created_at=row.created_at,
        owner_account_id=row.owner_account_id or "",
        owner_name=owner_names.get(row.owner_account_id or "", ""),
    ).model_dump(mode="json")


def _matches_keyword(row: Candidate, needle: str) -> bool:
    """`q` search across full_name, email, candidate_id, and skills (skill names
    + tools)."""
    hay = [row.full_name or "", row.email or "", row.candidate_id or ""]
    for s in row.skills or []:
        hay.append(s.get("skill", ""))
        hay.extend(s.get("tools", []) or [])
    return any(needle in h.lower() for h in hay)


def _get_or_404(db: Session, candidate_id: str) -> Candidate:
    row = db.get(Candidate, candidate_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Candidate '{candidate_id}' not found")
    return row


@router.get("/candidates")
def list_candidates(
    db: Session = Depends(get_db),
    status: str | None = Query(None, description="exact match on candidate status"),
    applied_position: str | None = Query(None, description="exact match on position"),
    min_experience: float | None = Query(None, description="experience_total >= this"),
    max_experience: float | None = Query(None, description="experience_total <= this"),
    q: str | None = Query(None, description="keyword: full_name, email, skills, candidate_id"),
    owner_account_id: str | None = Query(
        None, description="exact match on owner - pass the caller's own account_id "
                          "for a 'my candidates' filter"
    ),
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
    if owner_account_id:
        query = query.filter(Candidate.owner_account_id == owner_account_id)

    rows = query.order_by(Candidate.created_at.desc()).all()

    if q and q.strip():
        needle = q.strip().lower()
        rows = [r for r in rows if _matches_keyword(r, needle)]

    owner_names = owner_names_for(db, [r.owner_account_id for r in rows])
    return {"data": [_to_summary(r, owner_names) for r in rows], "error": None}


@router.get("/candidates/{candidate_id}")
def get_candidate(candidate_id: str, db: Session = Depends(get_db)):
    return {"data": _to_out(_get_or_404(db, candidate_id), db), "error": None}


@router.put("/candidates/{candidate_id}")
def update_candidate(
    candidate_id: str,
    payload: CandidateUpdate,
    db: Session = Depends(get_db),
    account: HRAccount = Depends(get_current_account),
):
    row = _get_or_404(db, candidate_id)

    data = payload.model_dump(
        mode="json",
        exclude_unset=True,
    )
    if "email" in data and data["email"] and "@" not in data["email"]:
        raise HTTPException(status_code=400, detail="Invalid email format")

    new_status = data.pop("status", None)
    if new_status not in STATUS_SET:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{new_status}'. Allowed: {STATUS_VALUES}",
        )

    for key, value in data.items():
        old_value = getattr(row, key)
        if old_value != value:
            record_change(db, candidate_id, key, old_value, value,
                          account.account_id, source="manual_edit")
        setattr(row, key, value)

    if "email" in data:
        row.email_normalized = normalize_email(row.email)

    if new_status is not None and new_status != row.status:
        apply_status_change(
            db,
            row,
            new_status,
            account.account_id,
        )

    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return {"data": _to_out(row, db), "error": None}


@router.post("/candidates/{candidate_id}/restore")
def restore_candidate(
    candidate_id: str,
    payload: StatusChangeRequest | None = None,
    db: Session = Depends(get_db),
    account: HRAccount = Depends(get_current_account),
):
    """F5 - undo a rejection: move the candidate back to the stage they held
    before they were rejected. This is the reason before_rejected_status exists."""
    row = _get_or_404(db, candidate_id)
    if row.status not in REJECTED_STATES:
        raise HTTPException(
            status_code=400,
            detail=f"Candidate '{candidate_id}' is not in a rejected state",
        )
    target = row.before_rejected_status or "New"
    if target not in STATUS_SET:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot restore: '{target}' is not a valid status",
        )

    apply_status_change(db, row, target, account.account_id,
                        reason=(payload.reason if payload else "") or "restored from rejection")
    db.commit()
    db.refresh(row)
    return {"data": _to_out(row, db), "error": None}


@router.post("/candidates/{candidate_id}/transfer-ownership")
def transfer_candidate_ownership(
    candidate_id: str,
    payload: TransferOwnershipRequest,
    db: Session = Depends(get_db),
    account: HRAccount = Depends(get_current_account),
):
    """Round 5 - "Owner changes owner to give to another user, only their own."
    Allowed callers: the CURRENT owner (transferring their own candidate away).
    Anyone else -> 403, even if they are the new
    owner-to-be - a transfer is something done TO an account, never something
    an account does to grant itself ownership."""
    row = _get_or_404(db, candidate_id)

    if account.account_id != row.owner_account_id:
        raise HTTPException(
            status_code=403,
            detail="Only the current owner can transfer ownership",
        )

    new_owner = db.get(HRAccount, payload.new_owner_account_id)
    if new_owner is None:
        raise HTTPException(
            status_code=404,
            detail=f"HR account '{payload.new_owner_account_id}' not found",
        )
    if not new_owner.is_active:
        raise HTTPException(
            status_code=400,
            detail=f"HR account '{payload.new_owner_account_id}' is deactivated",
        )
    if new_owner.account_id == row.owner_account_id:
        raise HTTPException(
            status_code=400, detail="That account already owns this candidate"
        )

    transfer_ownership(db, row, new_owner.account_id, account.account_id,
                       reason=payload.reason)
    db.commit()
    db.refresh(row)
    return {"data": _to_out(row, db), "error": None}


@router.get("/candidates/{candidate_id}/ownership-options")
def get_ownership_options(
    candidate_id: str,
    db: Session = Depends(get_db),
    account: HRAccount = Depends(get_current_account),
):
    row = _get_or_404(db, candidate_id)
    if account.account_id != row.owner_account_id:
        raise HTTPException(status_code=403, detail="Only the current owner can transfer ownership")
    accounts = (
        db.query(HRAccount)
        .filter(HRAccount.is_active.is_(True), HRAccount.account_id != row.owner_account_id)
        .order_by(HRAccount.full_name.asc(), HRAccount.username.asc())
        .all()
    )
    return {"data": [
        {"account_id": a.account_id, "full_name": a.full_name, "username": a.username}
        for a in accounts
    ], "error": None}


@router.get("/candidates/{candidate_id}/ownership-history")
def get_ownership_history(candidate_id: str, db: Session = Depends(get_db)):
    _get_or_404(db, candidate_id)
    rows = (
        db.query(OwnershipHistory)
        .filter(OwnershipHistory.candidate_id == candidate_id)
        .order_by(OwnershipHistory.changed_at.desc())
        .all()
    )
    names = owner_names_for(db, [account_id for r in rows for account_id in
                                 (r.from_owner_account_id, r.to_owner_account_id, r.changed_by)])
    return {
        "data": [dict(
            OwnershipHistoryOut.model_validate(r).model_dump(mode="json"),
            from_owner_name=names.get(r.from_owner_account_id, ""),
            to_owner_name=names.get(r.to_owner_account_id, ""),
            changed_by_name=names.get(r.changed_by, ""),
        ) for r in rows],
        "error": None,
    }


@router.post("/candidates/{candidate_id}/sql-test-score", status_code=201)
def add_sql_test_score(
    candidate_id: str,
    payload: SqlTestScoreIn,
    db: Session = Depends(get_db),
    account: HRAccount = Depends(get_current_account),
):
    """Round 5 - record a score from the external SQL-test tool.

    NOTE: this tool's real request contract is not confirmed yet (round-5
    kickoff: "ระบบ/เครื่องมือภายนอกแยกออกมา"). Today this accepts a plain
    `{score, source?, raw_payload?}` body under the same HR-account auth as
    every other endpoint; `raw_payload` keeps whatever else the caller sent so
    nothing is lost once the real shape is known. If that tool turns out to be
    a service calling in on its own (not a logged-in HR user), this endpoint's
    auth will need a service-credential path added alongside the existing one,
    not instead of it.
    """
    _get_or_404(db, candidate_id)
    row = record_sql_test_score(
        db, candidate_id, payload.score, payload.source, payload.raw_payload,
        recorded_by=account.account_id,
    )
    db.commit()
    db.refresh(row)
    return {"data": SqlTestScoreOut.model_validate(row).model_dump(mode="json"), "error": None}


@router.get("/candidates/{candidate_id}/sql-test-scores")
def list_sql_test_scores(candidate_id: str, db: Session = Depends(get_db)):
    _get_or_404(db, candidate_id)
    rows = (
        db.query(SqlTestScore)
        .filter(SqlTestScore.candidate_id == candidate_id)
        .order_by(SqlTestScore.recorded_at.desc())
        .all()
    )
    return {
        "data": [SqlTestScoreOut.model_validate(r).model_dump(mode="json") for r in rows],
        "error": None,
    }


@router.get("/candidates/{candidate_id}/status-history")
def get_status_history(candidate_id: str, db: Session = Depends(get_db)):
    _get_or_404(db, candidate_id)
    rows = (
        db.query(StatusHistory)
        .filter(StatusHistory.candidate_id == candidate_id)
        .order_by(StatusHistory.changed_at.desc())
        .all()
    )
    names = owner_names_for(db, [r.changed_by for r in rows])
    return {
        "data": [dict(StatusHistoryOut.model_validate(r).model_dump(mode="json"),
                      changed_by_name=names.get(r.changed_by, "")) for r in rows],
        "error": None,
    }


@router.get("/candidates/{candidate_id}/changes")
def get_change_log(candidate_id: str, db: Session = Depends(get_db)):
    """F4 step 4 - field-level diff of everything that has changed on this
    record, including every field a re-upload overwrote."""
    _get_or_404(db, candidate_id)
    rows = (
        db.query(CandidateChangeLog)
        .filter(CandidateChangeLog.candidate_id == candidate_id)
        .order_by(CandidateChangeLog.changed_at.desc())
        .all()
    )
    return {
        "data": [ChangeLogOut.model_validate(r).model_dump(mode="json") for r in rows],
        "error": None,
    }


@router.get("/candidates/{candidate_id}/resume-versions")
def list_resume_versions(candidate_id: str, db: Session = Depends(get_db)):
    """Every CV ever uploaded for this candidate, newest first. "What did their
    CV look like when we first screened them" has an answer now."""
    _get_or_404(db, candidate_id)
    rows = (
        db.query(ResumeVersion)
        .filter(ResumeVersion.candidate_id == candidate_id)
        .order_by(ResumeVersion.version_no.desc())
        .all()
    )
    return {
        "data": [ResumeVersionOut.model_validate(r).model_dump(mode="json") for r in rows],
        "error": None,
    }


@router.get("/candidates/{candidate_id}/resume-url")
def get_resume_url(
    candidate_id: str,
    db: Session = Depends(get_db),
    version: int | None = Query(None, description="defaults to the newest version"),
):
    """Resolves a fresh, working link every call - for Azure Blob this is a
    short-lived SAS URL, so don't rely on the `resume_url` stored on the
    candidate record staying valid forever; call this endpoint instead."""
    row = _get_or_404(db, candidate_id)

    query = db.query(ResumeVersion).filter(ResumeVersion.candidate_id == candidate_id)
    if version is not None:
        query = query.filter(ResumeVersion.version_no == version)
    target = query.order_by(ResumeVersion.version_no.desc()).first()

    if target is not None:
        url = storage.resolve_path_url(target.blob_path)
        filename, version_no = target.filename, target.version_no
    elif version is not None:
        raise HTTPException(
            status_code=404,
            detail=f"Candidate '{candidate_id}' has no resume version {version}",
        )
    else:
        # Rows written before F4 (seed data, pre-versioning uploads).
        url = (
            storage.resolve_url(candidate_id, row.resume_filename)
            if row.resume_filename
            else row.resume_url
        )
        filename, version_no = row.resume_filename, 0

    return {
        "data": {"resume_url": url, "filename": filename, "version_no": version_no},
        "error": None,
    }


@router.delete("/candidates/{candidate_id}")
def delete_candidate(candidate_id: str, db: Session = Depends(get_db)):
    """Cancel upload / delete a candidate - allowed only when the upload is not
    in progress (upload_status in DELETABLE_UPLOAD_STATUSES). Processing -> 400."""
    row = _get_or_404(db, candidate_id)
    if row.upload_status not in DELETABLE_UPLOAD_STATUSES:
        raise HTTPException(
            status_code=400, detail="Cannot cancel/delete file in current status"
        )

    # Delete the dependent rows explicitly. SQLite does not enforce foreign keys
    # unless PRAGMA foreign_keys is on, so leaving them would look fine today and
    # fail with an FK violation the day we move to Postgres. A candidate deletion
    # is also the one case where comment history is meant to go: it is how a PDPA
    # data-deletion request cascades.
    for model in (ResumeVersion, CommentLog, StatusHistory, CandidateChangeLog,
                 OwnershipHistory, SqlTestScore):
        db.query(model).filter(model.candidate_id == candidate_id).delete(
            synchronize_session=False
        )
    db.delete(row)
    db.commit()
    storage.delete(candidate_id)  # local folder or Azure blobs - whichever is active

    return {"data": {"candidate_id": candidate_id, "deleted": True}, "error": None}


# ------------------------------------------------------------------ F4 upload


def _find_by_email(db: Session, extracted: dict) -> list[Candidate]:
    """Return every exact normalized-email match for a human create-or-update decision."""
    key = normalize_email(extracted.get("email"))
    if not key:
        return []

    rows = (
        db.query(Candidate)
        .filter(Candidate.email_normalized == key)
        .order_by(Candidate.updated_at.desc(), Candidate.candidate_id.desc())
        .all()
    )

    for legacy in db.query(Candidate).filter(Candidate.email_normalized.is_(None)).all():
        if normalize_email(legacy.email) == key:
            legacy.email_normalized = key
            rows.append(legacy)
    return rows


@router.post("/candidates/upload", status_code=201)
async def upload_candidates(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    account: HRAccount = Depends(get_current_account),
):
    """Batch upload. Each .pdf/.docx file -> stored + extraction + persisted.

    Exact-email and plausible soft matches stop in `needs_review[]`; HR chooses
    whether to update the existing record or create a separate application cycle.
    A file with no match still creates a candidate automatically.

    Returns `{created[], updated[], needs_review[], failed[], count}`; a bad
    file fails only its own entry. `count` = created + updated (what actually
    landed on a candidate record). NOTE for Member 2: `updated[]` is new in
    round 4 - HR must be able to tell "3 new candidates" from "1 added, 2
    records overwritten", and `needs_review[]` needs its own prompt in the UI.
    """
    created: list[dict] = []
    updated: list[dict] = []
    needs_review: list[dict] = []
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

        # --- extract BEFORE deciding create-vs-update: the email in the CV is
        # what decides which record this file belongs to. A failure here means we
        # never learned the email, so no existing record can have been touched.
        try:
            # ---------------- MOCK EXTRACTION BOUNDARY ----------------
            # Day 6: swap the `extract_candidate` import above for Member 4's
            # llm-service function. Frozen signature:
            #   extract_candidate(file_bytes: bytes, filename: str | None = None) -> dict
            raw = extract_candidate(content, filename=name)
            # ---------------------------------------------------------
            fields = CandidateBase.model_validate(raw).model_dump(mode="json")
        except Exception as exc:
            # Keep a Failed row so HR can see the file arrived and delete/retry.
            candidate_id = next_candidate_id(db)
            failed_row = Candidate(
                candidate_id=candidate_id,
                upload_status="Failed",
                raw_text_snippet=f"[extraction failed] {exc}"[:500],
            )
            db.add(failed_row)
            assign_initial_owner(db, failed_row, account.account_id)
            db.commit()
            failed.append({
                "filename": name, "candidate_id": candidate_id,
                "error": f"Extraction failed: {exc}",
            })
            continue

        exact_matches = _find_by_email(db, fields)
        duplicate_ids = [row.candidate_id for row in exact_matches]
        if not duplicate_ids:
            duplicate_ids = find_duplicate_hints(db, fields)

        if duplicate_ids:
            pending = PendingUpload(
                pending_upload_id=str(uuid.uuid4()),
                filename=name,
                file_bytes=content,
                extracted_fields=fields,
                duplicate_candidate_ids=duplicate_ids,
                uploaded_by=account.account_id,
                created_at=utcnow(),
            )
            db.add(pending)
            db.commit()
            needs_review.append(pending_upload_preview(db, pending))
            continue

        # ---------------- new candidate path (no match, no hint at all) ----------------
        candidate_id = next_candidate_id(db)
        row = Candidate(candidate_id=candidate_id, upload_status="Processing")
        db.add(row)
        # Ownership is set at creation, before the try/except below - even a
        # row that ends up "Failed" (storage error) is still owned by whoever
        # attempted the import, and a rollback inside the try block must not
        # be able to erase that.
        assign_initial_owner(db, row, account.account_id)
        db.commit()

        try:
            stored = store_resume(db, candidate_id, name, content, account.account_id)

            for key, value in fields.items():
                setattr(row, key, value)
            row.email_normalized = normalize_email(row.email)
            row.possible_duplicate_of = []  # no hint - see the branch above
            row.resume_url = stored["url"]
            row.resume_filename = stored["filename"]
            row.upload_status = "Done"
            row.updated_at = utcnow()
            db.add(StatusHistory(
                history_id=str(uuid.uuid4()),
                candidate_id=candidate_id,
                from_status=None,
                to_status=row.status,
                changed_by=account.account_id,
                changed_at=utcnow(),
                reason="created by upload",
            ))
            db.commit()
            db.refresh(row)
            created.append(_to_out(row, db))
        except Exception as exc:  # storage failure - keep the row as Failed
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

    if not created and not updated and not needs_review and failed:
        # nothing succeeded and nothing is pending review -> surface as a 400
        # with the collected errors
        raise HTTPException(status_code=400, detail=failed[0]["error"])

    return {
        "data": {
            "created": created,
            "updated": updated,
            "needs_review": needs_review,
            "failed": failed,
            "count": len(created) + len(updated),
        },
        "error": None,
    }
