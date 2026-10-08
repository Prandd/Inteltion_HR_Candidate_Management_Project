"""Domain logic that is not HTTP: status transitions (F5), the re-upload merge
policy (F4), the field-level change log, and the comment helpers the deprecated
candidate fields are computed from (F3).

Kept out of the routers so each rule is one testable function instead of an `if`
scattered across an endpoint.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime

from fastapi import HTTPException

from sqlalchemy.orm import Session

from .models_db import (
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
from .statuses import REJECTED_STATES
from .storage import storage

# --------------------------------------------------------------- F4 merge policy
#
# Written as three explicit sets rather than scattered `if`s so the policy can be
# read - and tested - in one place.

EXTRACTION_OWNED = {
    "full_name", "email", "phone", "summary", "skills", "experience",
    "experience_total", "education", "current_salary", "expected_salary",
    "extraction_confidence", "raw_text_snippet",
}
# Never touched by an upload. A CV does not know which stage of our pipeline the
# person is at, nor which role HR is considering them for.
HR_OWNED = {"status", "before_rejected_status", "applied_position", "location"}
IMMUTABLE = {"candidate_id", "created_at"}

# Comments are absent from all three sets on purpose: they live in comment_logs
# keyed on candidate_id, and candidate_id is preserved across a re-upload, so
# comment history survives with no merge logic at all.

_MAX_LOGGED_VALUE = 500


def normalize_email(email: str | None) -> str | None:
    """The F4 duplicate key. Returns None (not "") for a blank email so a unique
    index can be added later without every blank row colliding."""
    cleaned = (email or "").strip().lower()
    return cleaned or None


def _stringify(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value[:_MAX_LOGGED_VALUE]
    try:
        return json.dumps(value, ensure_ascii=False, default=str)[:_MAX_LOGGED_VALUE]
    except (TypeError, ValueError):
        return str(value)[:_MAX_LOGGED_VALUE]


def record_change(
    db: Session,
    candidate_id: str,
    field: str,
    old_value,
    new_value,
    changed_by: str,
    source: str = "manual_edit",
) -> None:
    """One row per changed field. Added to the session, NOT committed - the
    caller commits it in the same transaction as the change itself."""
    db.add(CandidateChangeLog(
        change_id=str(uuid.uuid4()),
        candidate_id=candidate_id,
        field=field,
        old_value=_stringify(old_value),
        new_value=_stringify(new_value),
        changed_at=utcnow(),
        changed_by=changed_by,
        source=source,
    ))


def _is_empty(value) -> bool:
    return value is None or value == "" or value == [] or value == {}


def merge_on_reupload(
    db: Session,
    existing: Candidate,
    extracted: dict,
    changed_by: str,
) -> list[str]:
    """F4 step 2. Overwrite the extraction-owned fields from the new CV, leave
    everything HR or the server owns alone. Returns the list of fields actually
    changed (also written to candidate_change_log).

    Guard: a field the new CV failed to extract (empty) does NOT wipe a value the
    old CV had - extraction failing on a scanned PDF should not delete good data.
    Low `extraction_confidence` still writes through (team decision, round 4);
    the change log is what lets HR spot a bad overwrite afterwards.
    """
    changed: list[str] = []

    for field in sorted(EXTRACTION_OWNED):
        if field not in extracted:
            continue
        new_value = extracted[field]
        old_value = getattr(existing, field)

        if _is_empty(new_value) and not _is_empty(old_value):
            record_change(
                db, existing.candidate_id, field, old_value, old_value,
                changed_by, source="reupload_skipped_empty",
            )
            continue
        if old_value == new_value:
            continue

        setattr(existing, field, new_value)
        record_change(db, existing.candidate_id, field, old_value, new_value,
                      changed_by, source="reupload")
        changed.append(field)

    if "email" in changed:
        existing.email_normalized = normalize_email(existing.email)

    # HR_OWNED and IMMUTABLE are intentionally not iterated.
    existing.updated_at = utcnow()
    return changed


def find_duplicate_hints(db: Session, extracted: dict, exclude_id: str = "") -> list[str]:
    """F4 step 1, branch 2: no email match, so offer HR a soft hint instead of
    merging. Exact normalized phone, or normalized full_name + applied_position.
    Never acted on automatically - a false merge is irreversible, a false hint
    costs a click."""
    phone = (extracted.get("phone") or "").strip()
    name = (extracted.get("full_name") or "").strip().lower()
    position = (extracted.get("applied_position") or "").strip().lower()

    hints: list[str] = []
    if phone:
        rows = db.query(Candidate.candidate_id).filter(Candidate.phone == phone).all()
        hints.extend(cid for (cid,) in rows)
    if name:
        rows = db.query(Candidate.candidate_id, Candidate.full_name,
                        Candidate.applied_position).all()
        for cid, full_name, applied in rows:
            if (full_name or "").strip().lower() != name:
                continue
            if position and (applied or "").strip().lower() != position:
                continue
            hints.append(cid)

    return sorted({cid for cid in hints if cid and cid != exclude_id})


def pick_newest_duplicate(db: Session, candidate_ids: list[str]) -> Candidate | None:
    """Round-4 decision on the pending-upload 'Update' resolution: when a CV
    matched more than one existing candidate by hint, don't ask HR to pick which
    one - apply the update to whichever was touched most recently
    (`updated_at`). Ties break on `candidate_id` so the choice is deterministic,
    not on insertion order.
    """
    if not candidate_ids:
        return None
    return (
        db.query(Candidate)
        .filter(Candidate.candidate_id.in_(candidate_ids))
        .order_by(Candidate.updated_at.desc(), Candidate.candidate_id.desc())
        .first()
    )


# ------------------------------------------------------------- F5 status change


def apply_status_change(
    db: Session,
    candidate: Candidate,
    new_status: str,
    changed_by: str,
    reason: str = "",
) -> bool:
    """Set `status`, maintain `before_rejected_status`, and write the history row
    in the same transaction. Returns True if anything changed.

    The rule keys on the TRANSITION, not on the current value. A plain mirror
    ("before_rejected_status follows status unless status is rejected") looks
    equivalent but is not: once the candidate is rejected, the next PUT touching
    an unrelated field re-runs the mirror and stamps
    before_rejected_status = "Rejected", destroying the value it exists to
    keep. Returning early on `new_status == old_status` is what prevents that.
    """
    old_status = candidate.status
    if new_status == old_status:
        return False

    now_rejected = new_status in REJECTED_STATES
    was_rejected = old_status in REJECTED_STATES

    if now_rejected and not was_rejected:
        candidate.before_rejected_status = old_status or ""
    elif not now_rejected:
        # Un-rejected (or moved between two non-rejected stages) - the field only
        # ever describes a candidate who is currently rejected.
        candidate.before_rejected_status = ""

    candidate.status = new_status
    candidate.updated_at = utcnow()

    db.add(StatusHistory(
        history_id=str(uuid.uuid4()),
        candidate_id=candidate.candidate_id,
        from_status=old_status,
        to_status=new_status,
        changed_by=changed_by,
        changed_at=utcnow(),
        reason=reason or "",
    ))
    record_change(db, candidate.candidate_id, "status", old_status, new_status,
                  changed_by, source="manual_edit")
    return True


# ------------------------------------------------------ F3 deprecated-field reads


def latest_comment_texts(db: Session, candidate_id: str) -> dict[str, str]:
    """Text of the newest live comment of each type, for the two DEPRECATED
    candidate fields. Phase 2 removes both fields and this function with them."""
    rows = (
        db.query(CommentLog.comment_type, CommentLog.comment)
        .filter(
            CommentLog.candidate_id == candidate_id,
            CommentLog.deleted_at.is_(None),
            CommentLog.comment_type.in_(["hr", "line_manager"]),
        )
        .order_by(CommentLog.commented_at.desc(), CommentLog.created_at.desc())
        .all()
    )
    out = {"hr_comment": "", "line_manager_comment": ""}
    for comment_type, comment in rows:
        key = "hr_comment" if comment_type == "hr" else "line_manager_comment"
        if not out[key]:
            out[key] = comment or ""
    return out


# ------------------------------------------------------------- F4 CV versioning


def next_resume_version(db: Session, candidate_id: str) -> int:
    highest = (
        db.query(ResumeVersion.version_no)
        .filter(ResumeVersion.candidate_id == candidate_id)
        .order_by(ResumeVersion.version_no.desc())
        .first()
    )
    return (highest[0] + 1) if highest else 1


def store_resume(db: Session, candidate_id: str, filename: str, content: bytes,
                 uploaded_by: str) -> dict:
    """Save a file as the next resume_versions row for a candidate. The old
    blob is never overwritten - versions live at <candidate_id>/v<n>/<filename>.
    Shared by the direct upload path and both pending-upload resolutions, so a
    CV lands in exactly one place regardless of which path it took to get
    there."""
    version_no = next_resume_version(db, candidate_id)
    stored = storage.save(candidate_id, filename, content, version_no=version_no)
    db.add(ResumeVersion(
        version_id=str(uuid.uuid4()),
        candidate_id=candidate_id,
        version_no=version_no,
        blob_path=stored["path"],
        filename=stored["filename"],
        uploaded_at=utcnow(),
        uploaded_by=uploaded_by,
    ))
    return stored


def next_candidate_id(db: Session) -> str:
    """7-digit zero-padded running number, one past the highest numeric id in
    the table ('0000001', '0000002', ...). Good enough for a single-writer
    MVP - see the round-3 note in CHANGELOG.md about moving this behind a
    proper sequence if concurrent writers ever show up."""
    ids = db.query(Candidate.candidate_id).all()
    nums = [int(cid) for (cid,) in ids if cid and cid.isdigit()]
    return f"{(max(nums) + 1) if nums else 1:07d}"


def owner_name_for(db: Session, owner_account_id: str | None) -> str:
    """Live lookup, not a snapshot - if the owner is later renamed, every
    candidate they own should show the new name immediately. Empty string for
    no owner or a since-deleted account, matching the NULL RULE."""
    if not owner_account_id:
        return ""
    account = db.get(HRAccount, owner_account_id)
    if account is None:
        return ""
    return account.full_name or account.username


def owner_names_for(db: Session, owner_account_ids: list[str]) -> dict[str, str]:
    """Batch form of owner_name_for(), for list endpoints - one query instead of
    one per row."""
    ids = {i for i in owner_account_ids if i}
    if not ids:
        return {}
    rows = db.query(HRAccount).filter(HRAccount.account_id.in_(ids)).all()
    return {a.account_id: (a.full_name or a.username) for a in rows}


def record_ownership_change(
    db: Session,
    candidate_id: str,
    from_owner_account_id: str | None,
    to_owner_account_id: str,
    changed_by: str,
    reason: str = "",
    changed_at: datetime | None = None,
) -> None:
    """One row per assignment/transfer. The very first call for a candidate (at
    creation) passes `from_owner_account_id=None`. Added to the session, NOT
    committed - the caller commits it in the same transaction as the change."""
    db.add(OwnershipHistory(
        ownership_history_id=str(uuid.uuid4()),
        candidate_id=candidate_id,
        from_owner_account_id=from_owner_account_id,
        to_owner_account_id=to_owner_account_id,
        changed_by=changed_by,
        changed_at=changed_at or utcnow(),
        reason=reason or "",
    ))


def assign_initial_owner(db: Session, candidate: Candidate, owner_account_id: str) -> None:
    """Round 5 - "whoever imports a CV owns it." Called once, at the moment a
    candidate row is created (a fresh upload, or a pending-upload resolved as
    create-new). Re-upload and the pending-upload 'update' resolution do NOT
    call this - ownership is a fact about who brought the candidate in, not
    about who most recently touched the record (round-5 decision)."""
    candidate.owner_account_id = owner_account_id
    if candidate.created_at is None:
        candidate.created_at = utcnow()
    record_ownership_change(db, candidate.candidate_id, None, owner_account_id,
                            changed_by=owner_account_id, reason="created by upload",
                            changed_at=candidate.created_at)


def transfer_ownership(
    db: Session,
    candidate: Candidate,
    new_owner_account_id: str,
    changed_by: str,
    reason: str = "",
) -> None:
    """Round 5 - move ownership to someone else. Caller (router) has already
    checked that `changed_by` is the current owner and that
    `new_owner_account_id` is a real, active account."""
    old_owner = candidate.owner_account_id
    # Compare-and-set prevents simultaneous requests from the outgoing owner
    # from both succeeding and producing an inaccurate ownership chain.
    updated = db.query(Candidate).filter(
        Candidate.candidate_id == candidate.candidate_id,
        Candidate.owner_account_id == changed_by,
    ).update({"owner_account_id": new_owner_account_id, "updated_at": utcnow()},
             synchronize_session=False)
    if updated != 1:
        raise HTTPException(status_code=409, detail="Ownership has changed. Refresh and try again.")
    db.refresh(candidate)
    record_ownership_change(db, candidate.candidate_id, old_owner,
                            new_owner_account_id, changed_by, reason=reason)


def candidate_out(db: Session, row: Candidate) -> dict:
    """Full candidate payload, everywhere a candidate is serialised. The two
    deprecated comment fields are computed from comment_logs here (F3 phase 1)
    so existing frontend code keeps rendering something until phase 2 removes
    them."""
    from .schemas import CandidateOut  # local import - schemas.py has no reason
    # to import this module back, but keeping the edge one-directional avoids
    # ever having to think about it.

    payload = CandidateOut.model_validate(row).model_dump(mode="json")
    payload.update(latest_comment_texts(db, row.candidate_id))
    payload["owner_name"] = owner_name_for(db, row.owner_account_id)
    return payload


def record_sql_test_score(
    db: Session,
    candidate_id: str,
    score: float,
    source: str,
    raw_payload: dict | None,
    recorded_by: str | None,
) -> SqlTestScore:
    """Store one score row verbatim (plus the raw payload) from the external
    SQL-test tool. Not committed - the caller commits."""
    row = SqlTestScore(
        score_id=str(uuid.uuid4()),
        candidate_id=candidate_id,
        score=score,
        source=source,
        raw_payload=raw_payload,
        recorded_at=utcnow(),
        recorded_by=recorded_by,
    )
    db.add(row)
    return row


_PENDING_PREVIEW_FIELDS = (
    "full_name", "email", "phone", "applied_position",
    "experience_total", "extraction_confidence",
)


def pending_upload_preview(db: Session, pending: PendingUpload) -> dict:
    """The PendingUploadOut shape - shared by the upload response's
    `needs_review[]` and GET /api/pending-uploads, so a file HR sees flagged at
    upload time looks identical if they come back to it later from the list."""
    from .schemas import DuplicateCandidateHint, PendingUploadOut

    candidates = {
        c.candidate_id: c
        for c in db.query(Candidate)
        .filter(Candidate.candidate_id.in_(pending.duplicate_candidate_ids))
        .all()
    }
    candidate_ids = list(candidates)
    rejected_by_candidate = {}
    for history in (
        db.query(StatusHistory)
        .filter(
            StatusHistory.candidate_id.in_(candidate_ids),
            StatusHistory.to_status.in_(REJECTED_STATES),
        )
        .order_by(StatusHistory.changed_at.desc())
        .all()
    ):
        rejected_by_candidate.setdefault(history.candidate_id, history)

    comments_by_candidate = {}
    for comment in (
        db.query(CommentLog)
        .filter(
            CommentLog.candidate_id.in_(candidate_ids),
            CommentLog.deleted_at.is_(None),
        )
        .order_by(CommentLog.commented_at.desc(), CommentLog.created_at.desc())
        .all()
    ):
        comments_by_candidate.setdefault(comment.candidate_id, comment)

    ordered_candidates = sorted(
        candidates.values(),
        key=lambda candidate: (candidate.updated_at, candidate.candidate_id),
        reverse=True,
    )
    hints = [
        DuplicateCandidateHint(
            candidate_id=c.candidate_id,
            full_name=c.full_name,
            applied_position=c.applied_position,
            email=c.email,
            phone=c.phone,
            status=c.status,
            created_at=c.created_at,
            updated_at=c.updated_at,
            rejected_at=(
                rejected_by_candidate[c.candidate_id].changed_at
                if c.candidate_id in rejected_by_candidate else None
            ),
            rejected_from_status=(
                rejected_by_candidate[c.candidate_id].from_status
                if c.candidate_id in rejected_by_candidate else None
            ),
            rejection_reason=(
                rejected_by_candidate[c.candidate_id].reason
                if c.candidate_id in rejected_by_candidate else ""
            ),
            latest_comment=(
                comments_by_candidate[c.candidate_id].comment
                if c.candidate_id in comments_by_candidate
                else c.line_manager_comment or c.hr_comment or ""
            ),
            latest_comment_by=(
                comments_by_candidate[c.candidate_id].author_name
                if c.candidate_id in comments_by_candidate else ""
            ),
        )
        # Show the candidate update resolution will target first. Deleted
        # candidates disappear from the review summary.
        for c in ordered_candidates
    ]
    preview = {f: pending.extracted_fields.get(f, "") for f in _PENDING_PREVIEW_FIELDS}
    return PendingUploadOut(
        pending_upload_id=pending.pending_upload_id,
        filename=pending.filename,
        extracted_preview=preview,
        duplicate_candidates=hints,
        uploaded_by=pending.uploaded_by,
        created_at=pending.created_at,
    ).model_dump(mode="json")
