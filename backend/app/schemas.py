from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .config import settings
from .statuses import (  # noqa: F401  - re-exported; routers import from here
    DEFAULT_STATUS,
    REJECTED_STATES,
    STATUS_SET,
    STATUS_VALUES,
)

# Upload lifecycle - SEPARATE from the HR pipeline `status` above.
#   Not Uploaded : draft candidate, no CV yet (reserved - no create-draft endpoint yet)
#   Processing   : CV received, extraction running
#   Done         : extraction finished, candidate ready
#   Failed       : extraction/storage error - row kept so HR can delete/retry
UPLOAD_STATUS_VALUES = ["Not Uploaded", "Processing", "Done", "Failed"]

# Task-extension req #4: a candidate/upload may be deleted or cancelled only when
# it is NOT in progress. "Processing" -> DELETE returns 400.
DELETABLE_UPLOAD_STATUSES = {"Not Uploaded", "Done", "Failed"}

# F2 - account roles. Plain string column + this list rather than a DB enum:
# SQLite would not enforce a DB enum anyway, and we expect to add roles.
ROLE_VALUES = ["admin", "hr", "line_manager", "viewer"]
ROLE_SET = set(ROLE_VALUES)

# F3 - comment types. `hr` and `line_manager` replace the two old candidate
# fields; `interview` and `general` are here from the start because adding a
# type after the frontend ships is the awkward direction.
COMMENT_TYPE_VALUES = ["hr", "line_manager", "interview", "general"]
COMMENT_TYPE_SET = set(COMMENT_TYPE_VALUES)

# Which comment_type a role writes by default when the client does not say.
DEFAULT_COMMENT_TYPE_FOR_ROLE = {
    "hr": "hr",
    "admin": "hr",
    "line_manager": "line_manager",
    "viewer": "general",
}

# bcrypt silently truncates at 72 bytes - reject longer instead of accepting a
# password whose tail does not matter.
MAX_PASSWORD_LENGTH = 72


def _validate_password(value: str) -> str:
    if len(value) < settings.min_password_length:
        raise ValueError(
            f"Password must be at least {settings.min_password_length} characters"
        )
    if len(value.encode("utf-8")) > MAX_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at most {MAX_PASSWORD_LENGTH} bytes")
    return value


# ---------------------------------------------------------------- auth (F2)


class LoginRequest(BaseModel):
    username: str
    password: str


class AccountInfo(BaseModel):
    """The caller's identity, embedded in the login response and returned by
    GET /api/auth/me. Never carries the password hash."""

    model_config = ConfigDict(from_attributes=True)

    account_id: str
    username: str
    email: str = ""
    full_name: str = ""
    role: str = "hr"
    is_active: bool = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    account: AccountInfo


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def _check(cls, v: str) -> str:
        return _validate_password(v)


class ResetPasswordRequest(BaseModel):
    new_password: str

    @field_validator("new_password")
    @classmethod
    def _check(cls, v: str) -> str:
        return _validate_password(v)


class HRAccountCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: str
    full_name: str = Field(min_length=1, max_length=200)
    password: str
    role: str = "hr"

    @field_validator("password")
    @classmethod
    def _check_password(cls, v: str) -> str:
        return _validate_password(v)

    @field_validator("email")
    @classmethod
    def _check_email(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("Invalid email format")
        return v.strip().lower()

    @field_validator("role")
    @classmethod
    def _check_role(cls, v: str) -> str:
        if v not in ROLE_SET:
            raise ValueError(f"Invalid role '{v}'. Allowed: {ROLE_VALUES}")
        return v


class HRAccountUpdate(BaseModel):
    """Admin edit. Username is not editable - it is the login handle and the
    comment history is attributed by account_id anyway. Password is not here
    either; it goes through /change-password or /reset-password."""

    email: str | None = None
    full_name: str | None = None
    role: str | None = None
    is_active: bool | None = None

    @field_validator("email")
    @classmethod
    def _check_email(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if "@" not in v:
            raise ValueError("Invalid email format")
        return v.strip().lower()

    @field_validator("role")
    @classmethod
    def _check_role(cls, v: str | None) -> str | None:
        if v is not None and v not in ROLE_SET:
            raise ValueError(f"Invalid role '{v}'. Allowed: {ROLE_VALUES}")
        return v


class HRAccountOut(BaseModel):
    """Deliberately does NOT declare password_hash, so it cannot leak through a
    careless model_dump()."""

    model_config = ConfigDict(from_attributes=True)

    account_id: str
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    last_login_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


# ------------------------------------------------------------ comments (F3)


class CommentCreate(BaseModel):
    """POST body. `candidate_id`, `author_account_id`, `author_name`,
    `author_role`, `created_at` and `updated_at` are server-set and are ignored
    if the client sends them (extra fields are dropped by Pydantic)."""

    comment: str
    comment_type: str | None = None  # defaults from the caller's role
    commented_at: datetime | None = None  # defaults to now; backdating is allowed

    @field_validator("comment")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Comment must not be empty")
        return v.strip()

    @field_validator("comment_type")
    @classmethod
    def _check_type(cls, v: str | None) -> str | None:
        if v is not None and v not in COMMENT_TYPE_SET:
            raise ValueError(
                f"Invalid comment_type '{v}'. Allowed: {COMMENT_TYPE_VALUES}"
            )
        return v


class CommentUpdate(BaseModel):
    comment: str | None = None
    comment_type: str | None = None
    commented_at: datetime | None = None

    @field_validator("comment")
    @classmethod
    def _non_empty(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if not v.strip():
            raise ValueError("Comment must not be empty")
        return v.strip()

    @field_validator("comment_type")
    @classmethod
    def _check_type(cls, v: str | None) -> str | None:
        if v is not None and v not in COMMENT_TYPE_SET:
            raise ValueError(
                f"Invalid comment_type '{v}'. Allowed: {COMMENT_TYPE_VALUES}"
            )
        return v


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    comment_id: str
    candidate_id: str
    author_account_id: str
    author_name: str
    author_role: str
    comment_type: str
    comment: str
    commented_at: datetime  # display timestamp - the author may edit this
    created_at: datetime  # audit truth - never editable
    updated_at: datetime
    is_edited: bool


# ---------------------------------------------------------------- candidates


class SkillItem(BaseModel):
    skill: str = ""
    tools: list[str] = Field(default_factory=list)


class ExperienceItem(BaseModel):
    company: str = ""
    position: str = ""
    start_date: str = ""  # "YYYY-MM" | "Present" | ""
    end_date: str = ""  # "YYYY-MM" | "Present" | ""
    description: str = ""


class EducationItem(BaseModel):
    institution: str = ""
    degree: str = ""
    field: str = ""
    year: str = ""


class CandidateBase(BaseModel):
    """The editable body of a candidate. NULL RULE: no nulls - every string
    defaults to "", every number to 0, every array to [].

    `hr_comment` / `line_manager_comment` are NOT here any more (F3 phase 1):
    they are computed read-only on the way out and ignored on the way in.
    """

    full_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    applied_position: str = ""
    summary: str = ""
    skills: list[SkillItem] = Field(default_factory=list)
    experience: list[ExperienceItem] = Field(default_factory=list)
    experience_total: float = 0
    current_salary: float = 0
    expected_salary: float = 0
    education: list[EducationItem] = Field(default_factory=list)
    extraction_confidence: float = 0
    raw_text_snippet: str = ""
    status: str = DEFAULT_STATUS


class CandidateUpdate(CandidateBase):
    """Body accepted by PUT /api/candidates/{id} - the full editable schema.
    candidate_id / timestamps / resume_url / before_rejected_status /
    possible_duplicate_of / the two deprecated comment fields are all ignored
    if present in the body."""


class CandidateOut(CandidateBase):
    """Full candidate as returned by GET/PUT/upload."""

    model_config = ConfigDict(from_attributes=True)

    candidate_id: str
    # F5. Read-only, server-managed. "" when the candidate is not rejected.
    before_rejected_status: str = ""
    upload_status: str = "Not Uploaded"  # read-only, backend-managed
    resume_url: str = ""
    resume_filename: str = ""
    # F4. Read-only hint - candidate_ids this row might duplicate. Never merged
    # automatically; HR decides.
    possible_duplicate_of: list[str] = Field(default_factory=list)
    # Round 5. Read-only here - set at creation, changed only via
    # POST /api/candidates/{id}/transfer-ownership. "" for the rare row that
    # could not be backfilled a real owner (see migration 0005).
    owner_account_id: str = ""
    # Live lookup, not a snapshot (unlike comment author_name) - ownership is a
    # current assignment, so showing a renamed owner's new name is correct here.
    owner_name: str = ""
    # DEPRECATED (F3 phase 1) - the text of the newest live comment of each
    # type, computed at read time. Writes are ignored. Removed in phase 2; read
    # GET /api/candidates/{id}/comments instead.
    hr_comment: str = ""
    line_manager_comment: str = ""
    created_at: datetime
    updated_at: datetime

    # Rows that predate these two columns (an ALTER without a backfill) read
    # back as NULL. The NULL RULE says the payload never contains one.
    @field_validator("before_rejected_status", mode="before")
    @classmethod
    def _no_null_string(cls, v):
        return v or ""

    @field_validator("possible_duplicate_of", mode="before")
    @classmethod
    def _no_null_list(cls, v):
        return v or []

    @field_validator("owner_account_id", mode="before")
    @classmethod
    def _no_null_owner(cls, v):
        return v or ""


class CandidateSummary(BaseModel):
    """Trimmed shape for GET /api/candidates (list view)."""

    model_config = ConfigDict(from_attributes=True)

    candidate_id: str
    full_name: str
    applied_position: str
    location: str
    email: str
    phone: str
    experience_total: float
    status: str
    before_rejected_status: str = ""
    upload_status: str
    top_skills: list[str] = Field(default_factory=list)
    extraction_confidence: float
    created_at: datetime
    owner_account_id: str = ""
    owner_name: str = ""


# -------------------------------------------------- pending uploads (F4, round 4)


class DuplicateCandidateHint(BaseModel):
    """One candidate a pending upload might belong to - enough for HR to
    recognise them without a second API call."""

    candidate_id: str
    full_name: str
    applied_position: str
    email: str
    phone: str
    status: str
    updated_at: datetime


class PendingUploadOut(BaseModel):
    """A CV that stopped for a human decision instead of guessing.
    `extracted_preview` is intentionally a small subset of the extraction - just
    enough to tell candidates apart - not the full record."""

    model_config = ConfigDict(from_attributes=True)

    pending_upload_id: str
    filename: str
    extracted_preview: dict
    duplicate_candidates: list[DuplicateCandidateHint]
    uploaded_by: str
    created_at: datetime


class PendingUploadResolved(BaseModel):
    """Response of the two resolution endpoints - which candidate ended up
    holding the file, and how."""

    pending_upload_id: str
    resolution: str  # 'updated' | 'created_new'
    candidate: dict  # the full CandidateOut payload, same shape as everywhere else


# ----------------------------------------------------- history / audit (F4/F5)


class StatusHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    history_id: str
    candidate_id: str
    from_status: str | None = None
    to_status: str
    changed_by: str
    changed_at: datetime
    reason: str = ""


class ResumeVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    version_id: str
    candidate_id: str
    version_no: int
    filename: str
    uploaded_at: datetime
    uploaded_by: str


class ChangeLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    change_id: str
    candidate_id: str
    field: str
    old_value: str
    new_value: str
    changed_at: datetime
    changed_by: str
    source: str


class StatusChangeRequest(BaseModel):
    """Optional body for POST /api/candidates/{id}/restore."""

    reason: str = ""


# --------------------------------------------------------------- ownership (round 5)


class TransferOwnershipRequest(BaseModel):
    """Body for POST /api/candidates/{id}/transfer-ownership.

    `new_owner_account_id` must belong to an active HR account. Who is allowed
    to call this at all (the current owner, or an admin) is enforced server-side
    in the router, per the round-5 decision - not by which fields this body
    happens to declare.
    """

    new_owner_account_id: str
    reason: str = ""


class OwnershipHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ownership_history_id: str
    candidate_id: str
    from_owner_account_id: str | None = None
    to_owner_account_id: str
    changed_by: str
    changed_at: datetime
    reason: str = ""


class OwnershipOptionOut(BaseModel):
    """GET /api/candidates/{id}/ownership-options - active accounts the
    current owner (or an admin) could transfer this candidate to. Excludes
    the current owner; deactivated accounts never qualify as a target
    either (transfer-ownership itself rejects those at write time)."""

    model_config = ConfigDict(from_attributes=True)

    account_id: str
    full_name: str
    username: str


# ---------------------------------------------------- sql test score (round 5)
#
# The external tool's own contract is not confirmed yet - see the model
# docstring in models_db.py. `score` is required and validated; everything
# else the caller sends is kept verbatim in `raw_payload` rather than
# discarded, so today's guess at the shape does not lose data if it is wrong.


class SqlTestScoreIn(BaseModel):
    score: float
    source: str = "sql_test"
    raw_payload: dict | None = None

    @field_validator("score")
    @classmethod
    def _finite(cls, v: float) -> float:
        if v != v or v in (float("inf"), float("-inf")):  # NaN / inf
            raise ValueError("score must be a finite number")
        return v


class SqlTestScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    score_id: str
    candidate_id: str
    score: float
    source: str
    raw_payload: dict | None = None
    recorded_at: datetime
    recorded_by: str | None = None
