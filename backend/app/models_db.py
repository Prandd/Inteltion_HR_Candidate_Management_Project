from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
)

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# Kept as a private alias so existing `default=_utcnow` references elsewhere
# (and anything importing it) keep working.
_utcnow = utcnow


class Candidate(Base):
    """One row per candidate. Nested skills / experience / education are stored
    as JSON columns - fine for the MVP, no child tables needed."""

    __tablename__ = "candidates"

    # 7-digit zero-padded running number ("0000001"), assigned by the backend in
    # creation order - see next_candidate_id() in services.py.
    candidate_id = Column(String, primary_key=True)
    full_name = Column(String, nullable=False, default="")
    email = Column(String, nullable=False, default="")
    # F4 - lowercased/trimmed `email`, kept in sync by normalize_email() at every
    # write. The duplicate-detection key. NULL (not "") when there is no email,
    # so two email-less candidates never collide on the unique constraint below.
    # UNIQUE as of migration 0003 - see that file for why it could not be added
    # in round 4 (existing DBs could already hold duplicate emails from before
    # F4 existed).
    email_normalized = Column(String, nullable=True, unique=True, index=True)
    phone = Column(String, nullable=False, default="")
    location = Column(String, nullable=False, default="")
    applied_position = Column(String, nullable=False, default="")
    summary = Column(Text, nullable=False, default="")
    skills = Column(JSON, nullable=False, default=list)
    experience = Column(JSON, nullable=False, default=list)
    experience_total = Column(Float, nullable=False, default=0)
    current_salary = Column(Float, nullable=False, default=0)
    expected_salary = Column(Float, nullable=False, default=0)
    education = Column(JSON, nullable=False, default=list)
    # DEPRECATED (F3 phase 1). Comments live in `comment_logs` now. These two
    # columns are no longer written by the API - the candidate payload computes
    # them from the newest live comment of each type so existing frontend code
    # keeps rendering something. Removed from the schema entirely in phase 2.
    hr_comment = Column(Text, nullable=False, default="")
    line_manager_comment = Column(Text, nullable=False, default="")
    extraction_confidence = Column(Float, nullable=False, default=0)
    raw_text_snippet = Column(Text, nullable=False, default="")
    status = Column(String, nullable=False, default="New")  # HR pipeline
    # F5 - the stage held immediately before entering a rejected state.
    # Server-managed, never accepted from a request body. "" when not rejected.
    before_rejected_status = Column(String, nullable=False, default="")
    upload_status = Column(String, nullable=False, default="Not Uploaded")  # file lifecycle
    resume_url = Column(String, nullable=False, default="")
    resume_filename = Column(String, nullable=False, default="")
    # F4 - candidate_ids this row *might* duplicate, when no email match was
    # possible. Read-only hint for HR; the backend never auto-merges on it.
    possible_duplicate_of = Column(JSON, nullable=False, default=list)
    # Round 5 - whoever imported this CV owns it. Set once at creation (the
    # uploader for a fresh candidate, or the original uploader for a pending
    # upload resolved as "create new" - see routers/pending_uploads.py) and
    # left untouched by every re-upload/merge path after that: ownership is a
    # fact about who brought the candidate in, not about who most recently
    # touched the record. Changed only via the dedicated transfer endpoint,
    # which writes an ownership_history row. Nullable only for rows migrated
    # in before this column existed and that could not be backfilled (no
    # status_history row to attribute to) - see migration 0005.
    owner_account_id = Column(
        String, ForeignKey("hr_accounts.account_id"), nullable=True
    )
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = Column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )


class HRAccount(Base):
    """F2 - a real HR login. Replaces the single hardcoded admin.

    Accounts are DEACTIVATED, never deleted: `comment_logs`, `status_history`
    and `resume_versions` all point at an account_id, and a hard delete would
    orphan or cascade away that history.
    """

    __tablename__ = "hr_accounts"

    account_id = Column(String, primary_key=True)  # uuid4
    username = Column(String, nullable=False, unique=True, index=True)
    email = Column(String, nullable=False, unique=True)
    full_name = Column(String, nullable=False, default="")  # shown as the comment author
    # bcrypt hash. NEVER returned by the API - HRAccountOut does not declare the
    # field at all, so it cannot leak through a careless model_dump().
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="hr")  # see schemas.ROLE_VALUES
    is_active = Column(Boolean, nullable=False, default=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = Column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )


class CommentLog(Base):
    """F3 - one row per comment, isolated from the candidate record.

    Two timestamps on purpose: `commented_at` is what HR sees and may edit
    (backdating a phone call is legitimate); `created_at` / `updated_at` are
    server-owned audit truth and are never editable.
    """

    __tablename__ = "comment_logs"

    comment_id = Column(String, primary_key=True)  # uuid4
    # IMMUTABLE - taken from the URL path, never from the body.
    candidate_id = Column(
        String, ForeignKey("candidates.candidate_id"), nullable=False
    )
    # IMMUTABLE - taken from the JWT, never from the body.
    author_account_id = Column(
        String, ForeignKey("hr_accounts.account_id"), nullable=False
    )
    # Snapshot of the author at write time: a comment from 2024 should still read
    # as the name that wrote it, even after a rename or a deactivation.
    author_name = Column(String, nullable=False, default="")
    author_role = Column(String, nullable=False, default="hr")
    comment_type = Column(String, nullable=False, default="general")
    comment = Column(Text, nullable=False)  # the body - editable
    commented_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    is_edited = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # soft delete; NULL = live


Index(
    "ix_comment_logs_candidate",
    CommentLog.candidate_id,
    CommentLog.commented_at.desc(),
)


class ResumeVersion(Base):
    """F4 step 3 - every uploaded CV is kept, nothing is overwritten.

    `blob_path` is the storage key ("<candidate_id>/v<n>/<filename>") and is what
    GET /resume-url resolves; the candidate's own `resume_url` points at the
    newest version.
    """

    __tablename__ = "resume_versions"

    version_id = Column(String, primary_key=True)  # uuid4
    candidate_id = Column(
        String, ForeignKey("candidates.candidate_id"), nullable=False, index=True
    )
    version_no = Column(Integer, nullable=False)  # 1, 2, 3...
    blob_path = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    uploaded_by = Column(String, ForeignKey("hr_accounts.account_id"), nullable=False)


class StatusHistory(Base):
    """F5 - the source of truth for status changes (and the M3 audit log).

    `candidates.before_rejected_status` is a denormalised read-only convenience
    derived from the same transition, so Lane A's Kanban does not have to join
    this table to render a badge.
    """

    __tablename__ = "status_history"

    history_id = Column(String, primary_key=True)  # uuid4
    candidate_id = Column(
        String, ForeignKey("candidates.candidate_id"), nullable=False, index=True
    )
    from_status = Column(String, nullable=True)
    to_status = Column(String, nullable=False)
    changed_by = Column(String, ForeignKey("hr_accounts.account_id"), nullable=False)
    changed_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    reason = Column(Text, nullable=False, default="")


class PendingUpload(Base):
    """A CV that could not be auto-resolved on upload: no exact email match, but
    `find_duplicate_hints()` found a plausible existing candidate (phone, or
    name + position). Team decision (round 4): stop and ask instead of guessing
    - the file is held here, not silently turned into a new candidate.

    `file_bytes` holds the raw upload until a human resolves it. CVs are capped
    at `settings.max_upload_mb` (10 MB), so keeping the bytes in SQLite for what
    is meant to be a short wait is simpler than inventing a "move this blob
    later" operation on the Storage protocol. Cleared (set to None) once
    resolved, whichever way - the real copy then lives under the candidate's
    normal resume_versions, or nowhere if discarded.
    """

    __tablename__ = "pending_uploads"

    pending_upload_id = Column(String, primary_key=True)  # uuid4
    filename = Column(String, nullable=False)
    file_bytes = Column(LargeBinary, nullable=True)
    extracted_fields = Column(JSON, nullable=False)  # full CandidateBase dict
    # candidate_ids find_duplicate_hints() suggested. Never empty - an upload
    # with no hints is auto-created immediately and never reaches this table.
    duplicate_candidate_ids = Column(JSON, nullable=False, default=list)
    uploaded_by = Column(String, ForeignKey("hr_accounts.account_id"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    resolved_at = Column(DateTime(timezone=True), nullable=True)  # NULL = still open
    resolution = Column(String, nullable=True)  # 'updated' | 'created_new' | 'discarded'
    resolved_candidate_id = Column(String, nullable=True)


class OwnershipHistory(Base):
    """Round 5 - every ownership assignment and transfer, in order.

    The very first row for a candidate (written at creation, alongside the
    StatusHistory "created by upload" row) has `from_owner_account_id = NULL`
    and records who originally imported the CV. Every later row is a transfer:
    `changed_by` is whoever performed the transfer (the outgoing owner, or an
    admin overriding it - see the round-5 decision in CHANGELOG.md), which can
    differ from `from_owner_account_id` when an admin does the moving.
    """

    __tablename__ = "ownership_history"

    ownership_history_id = Column(String, primary_key=True)  # uuid4
    candidate_id = Column(
        String, ForeignKey("candidates.candidate_id"), nullable=False, index=True
    )
    from_owner_account_id = Column(
        String, ForeignKey("hr_accounts.account_id"), nullable=True
    )
    to_owner_account_id = Column(
        String, ForeignKey("hr_accounts.account_id"), nullable=False
    )
    changed_by = Column(String, ForeignKey("hr_accounts.account_id"), nullable=False)
    changed_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    reason = Column(Text, nullable=False, default="")


class SqlTestScore(Base):
    """Round 5 - a score reported by the external SQL-test tool for a candidate.

    The tool's own request/response contract is not confirmed yet (round-5
    kickoff note: "ระบบ/เครื่องมือภายนอกแยกออกมา" - a separate external system,
    no shape agreed). `raw_payload` keeps whatever it actually sent verbatim,
    so nothing is lost if today's guess at the shape (a plain numeric `score`)
    turns out to be wrong once the real contract is known - the stored row can
    be re-interpreted without a migration. `score` itself stays a plain float
    rather than jamming a full rubric into a column now.
    """

    __tablename__ = "sql_test_scores"

    score_id = Column(String, primary_key=True)  # uuid4
    candidate_id = Column(
        String, ForeignKey("candidates.candidate_id"), nullable=False, index=True
    )
    score = Column(Float, nullable=False)
    source = Column(String, nullable=False, default="sql_test")
    raw_payload = Column(JSON, nullable=True)
    recorded_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    # Nullable: a machine-to-machine call from the external tool may not carry
    # an HR account at all once that integration is real (see the open question
    # in CHANGELOG.md about its auth). Whichever HR account was logged in when
    # the call was made, if any.
    recorded_by = Column(String, ForeignKey("hr_accounts.account_id"), nullable=True)


class CandidateChangeLog(Base):
    """F4 step 4 - field-level diff of every change to a candidate record.

    Re-upload is the single largest source of silent change, so each overwritten
    field gets its own row with `source='reupload'`.
    """

    __tablename__ = "candidate_change_log"

    change_id = Column(String, primary_key=True)  # uuid4
    candidate_id = Column(
        String, ForeignKey("candidates.candidate_id"), nullable=False, index=True
    )
    field = Column(String, nullable=False)
    old_value = Column(Text, nullable=False, default="")  # JSON-encoded, truncated
    new_value = Column(Text, nullable=False, default="")
    changed_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    changed_by = Column(String, nullable=False, default="")  # hr_accounts.account_id
    source = Column(String, nullable=False, default="manual_edit")  # reupload | manual_edit
