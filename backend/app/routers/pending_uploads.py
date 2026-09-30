"""Round 4 - resolving a CV that stopped for a human decision.

A file lands here when the upload found NO exact email match but DID find a
plausible soft match (same phone, or same name + position). The team's rule:
never guess in that situation. Creating a second record for someone already in
the pipeline and silently overwriting the wrong person's record are both bad,
and only a human can tell which case this is.

Two ways out, both one call:
  * update     - the CV belongs to somebody we already have
  * create-new - it really is a different person with a similar-looking CV

`update` does NOT ask which candidate to write to. When several candidates
matched, it takes the one touched most recently (`updated_at`) - that is the
record HR is actually working on. Asking "which of these three?" for every file
in a 20-file batch is the kind of prompt people click through without reading.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..auth import get_current_account
from ..database import get_db
from ..models_db import Candidate, HRAccount, PendingUpload, StatusHistory, utcnow
from ..schemas import PendingUploadResolved
from ..services import (
    assign_initial_owner,
    candidate_out,
    merge_on_reupload,
    next_candidate_id,
    normalize_email,
    pending_upload_preview,
    pick_newest_duplicate,
    record_change,
    store_resume,
)

router = APIRouter(tags=["pending-uploads"],
                   dependencies=[Depends(get_current_account)])


def _open_or_404(db: Session, pending_upload_id: str) -> PendingUpload:
    """An already-resolved item is a 409, not a 404: the caller is most likely a
    second browser tab acting on a stale list, and "someone already handled
    this" is more useful than "no such thing"."""
    row = db.get(PendingUpload, pending_upload_id)
    if row is None:
        raise HTTPException(
            status_code=404, detail=f"Pending upload '{pending_upload_id}' not found"
        )
    if row.resolved_at is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Pending upload '{pending_upload_id}' was already resolved "
                f"({row.resolution}) onto candidate "
                f"'{row.resolved_candidate_id or '-'}'"
            ),
        )
    return row


def _resolved(db: Session, pending: PendingUpload, resolution: str,
              candidate: Candidate) -> dict:
    return {
        "data": PendingUploadResolved(
            pending_upload_id=pending.pending_upload_id,
            resolution=resolution,
            candidate=candidate_out(db, candidate),
        ).model_dump(mode="json"),
        "error": None,
    }


@router.get("/pending-uploads")
def list_pending_uploads(db: Session = Depends(get_db)):
    """Everything still waiting on a decision, oldest first - a work queue, so
    the file that has been waiting longest is at the top."""
    rows = (
        db.query(PendingUpload)
        .filter(PendingUpload.resolved_at.is_(None))
        .order_by(PendingUpload.created_at.asc())
        .all()
    )
    return {"data": [pending_upload_preview(db, p) for p in rows], "error": None}


@router.post("/pending-uploads/{pending_upload_id}/update")
def resolve_as_update(
    pending_upload_id: str,
    db: Session = Depends(get_db),
    account: HRAccount = Depends(get_current_account),
):
    """"This CV belongs to somebody we already have." Applies the same merge
    policy as a normal re-upload: extraction-owned fields are overwritten,
    HR-owned fields (`status`, `applied_position`, `location`,
    `before_rejected_status`) and comment history are left alone. Ownership is
    left alone too (round 5) - the candidate already has an owner, and merging
    a re-upload into them does not change who brought them in."""
    pending = _open_or_404(db, pending_upload_id)

    target = pick_newest_duplicate(db, pending.duplicate_candidate_ids)
    if target is None:
        # Every suggested candidate has been deleted since the upload. There is
        # nothing left to merge onto, so the only sensible resolution is
        # create-new - say so rather than failing with something cryptic.
        raise HTTPException(
            status_code=409,
            detail=(
                "None of the suggested candidates still exist. "
                f"Use POST /api/pending-uploads/{pending_upload_id}/create-new instead."
            ),
        )

    stored = store_resume(db, target.candidate_id, pending.filename,
                          pending.file_bytes or b"", account.account_id)

    merge_on_reupload(db, target, pending.extracted_fields, account.account_id)
    for field, value in (("resume_url", stored["url"]),
                         ("resume_filename", stored["filename"]),
                         ("upload_status", "Done")):
        old = getattr(target, field)
        if old != value:
            record_change(db, target.candidate_id, field, old, value,
                          account.account_id, source="reupload")
        setattr(target, field, value)
    target.updated_at = utcnow()

    pending.resolved_at = utcnow()
    pending.resolution = "updated"
    pending.resolved_candidate_id = target.candidate_id
    pending.file_bytes = None  # the real copy now lives in resume_versions

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Merging this CV would collide with another candidate's email",
        )
    db.refresh(target)
    return _resolved(db, pending, "updated", target)


@router.post("/pending-uploads/{pending_upload_id}/create-new", status_code=201)
def resolve_as_create_new(
    pending_upload_id: str,
    db: Session = Depends(get_db),
    account: HRAccount = Depends(get_current_account),
):
    """"It really is a different person." Creates the candidate the upload
    would have created if it had not stopped to ask, and keeps the hint that
    made it stop in `possible_duplicate_of` so the near-match stays visible.

    Owner is the file's ORIGINAL uploader (`pending.uploaded_by`), not
    whichever account resolves the queue item later (round 5) - "whoever
    imports the CV owns it" means the import that actually happened, which was
    the original upload. If a different account clicks "create new" days
    later, that account can be given ownership afterwards through the
    transfer endpoint, same as any other reassignment.
    """
    pending = _open_or_404(db, pending_upload_id)

    candidate_id = next_candidate_id(db)
    row = Candidate(candidate_id=candidate_id, upload_status="Processing")
    db.add(row)
    db.commit()

    try:
        stored = store_resume(db, candidate_id, pending.filename,
                              pending.file_bytes or b"", account.account_id)

        for key, value in pending.extracted_fields.items():
            setattr(row, key, value)
        row.email_normalized = normalize_email(row.email)
        # Kept, not cleared: HR decided these are different people, but the
        # near-match is still worth showing on the record.
        row.possible_duplicate_of = pending.duplicate_candidate_ids
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
            reason="created by upload (duplicate hint reviewed and overridden)",
        ))
        assign_initial_owner(db, row, pending.uploaded_by)

        pending.resolved_at = utcnow()
        pending.resolution = "created_new"
        pending.resolved_candidate_id = candidate_id
        pending.file_bytes = None

        db.commit()
        db.refresh(row)
    except IntegrityError:
        db.rollback()
        db.query(Candidate).filter(Candidate.candidate_id == candidate_id).delete()
        db.commit()
        raise HTTPException(
            status_code=409,
            detail="A candidate with this email already exists",
        )
    except Exception as exc:
        db.rollback()
        db.query(Candidate).filter(Candidate.candidate_id == candidate_id).delete()
        db.commit()
        raise HTTPException(status_code=500, detail=f"Could not store the CV: {exc}")

    return _resolved(db, pending, "created_new", row)


@router.delete("/pending-uploads/{pending_upload_id}")
def discard_pending_upload(
    pending_upload_id: str,
    db: Session = Depends(get_db),
    _account: HRAccount = Depends(get_current_account),
):
    """"Neither - this file should not be in the system at all." The row stays
    as an audit record of the decision; only the CV bytes are dropped, because
    holding somebody's resume we explicitly decided not to keep is exactly what
    PDPA asks us not to do."""
    pending = _open_or_404(db, pending_upload_id)

    pending.resolved_at = utcnow()
    pending.resolution = "discarded"
    pending.file_bytes = None
    db.commit()

    return {
        "data": {"pending_upload_id": pending_upload_id, "discarded": True},
        "error": None,
    }
