from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# The frozen status list (from CapstoneMeeting.md). Default on upload = "New".
STATUS_VALUES = [
    "New",
    "Review",
    "Needs information",
    "CV passed",
    "Assessment",
    "Interview",
    "Hired",
    "CV rejected",
    "Archived",
]

# Upload lifecycle - SEPARATE from the HR pipeline `status` above.
#   Not Uploaded : draft candidate, no CV yet (reserved - no create-draft endpoint yet)
#   Processing   : CV received, extraction running
#   Done         : extraction finished, candidate ready
#   Failed       : extraction/storage error - row kept so HR can delete/retry
UPLOAD_STATUS_VALUES = ["Not Uploaded", "Processing", "Done", "Failed"]

# Task-extension req #4: a candidate/upload may be deleted or cancelled only when
# it is NOT in progress. "Processing" -> DELETE returns 400.
DELETABLE_UPLOAD_STATUSES = {"Not Uploaded", "Done", "Failed"}


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


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
    defaults to "", every number to 0, every array to []."""

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
    hr_comment: str = ""
    line_manager_comment: str = ""
    extraction_confidence: float = 0
    raw_text_snippet: str = ""
    status: str = "New"


class CandidateUpdate(CandidateBase):
    """Body accepted by PUT /api/candidates/{id} - the full editable schema.
    candidate_id / timestamps / resume_url in the body are ignored."""


class CandidateOut(CandidateBase):
    """Full candidate as returned by GET/PUT/upload."""

    model_config = ConfigDict(from_attributes=True)

    candidate_id: str
    upload_status: str = "Not Uploaded"  # read-only, backend-managed
    resume_url: str = ""
    resume_filename: str = ""
    created_at: datetime
    updated_at: datetime


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
    upload_status: str
    top_skills: list[str] = Field(default_factory=list)
    extraction_confidence: float
    created_at: datetime
