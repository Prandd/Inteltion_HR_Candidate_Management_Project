from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field
)


# The frozen status list
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



class SkillItem(BaseModel):

    skill: str = ""

    tools: list[str] = Field(
        default_factory=list
    )



class ExperienceItem(BaseModel):

    company: str = ""

    position: str = ""

    start_date: str = ""

    end_date: str = ""

    description: str = ""



class EducationItem(BaseModel):

    institution: str = ""

    degree: str = ""

    field: str = ""

    year: str = ""



class CandidateBase(BaseModel):

    full_name: str = ""

    email: str = ""

    phone: str = ""

    location: str = ""

    applied_position: str = ""

    summary: str = ""

    skills: list[SkillItem] = Field(
        default_factory=list
    )

    experience: list[ExperienceItem] = Field(
        default_factory=list
    )

    experience_total: float = 0

    current_salary: float = 0

    expected_salary: float = 0

    education: list[EducationItem] = Field(
        default_factory=list
    )

    hr_comment: str = ""

    line_manager_comment: str = ""

    extraction_confidence: float = 0

    raw_text_snippet: str = ""

    status: str = "New"




class CandidateUpdate(CandidateBase):
    pass






class StatusHistoryOut(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )


    status: str

    previous_status: str | None = None

    action: str

    changed_by: str

    changed_at: datetime







class CommentCreate(BaseModel):

    comment: str

    role: str = "HR"

    author: str = "HR Admin"







class CommentOut(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )


    id: int

    author: str

    role: str

    comment: str

    created_at: datetime







class CandidateOut(CandidateBase):

    model_config = ConfigDict(
        from_attributes=True
    )


    candidate_id: str

    resume_url: str = ""

    resume_filename: str = ""

    created_at: datetime

    updated_at: datetime

    status_history: list[StatusHistoryOut] = Field(
        default_factory=list
    )







class CandidateSummary(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )


    candidate_id: str

    full_name: str

    applied_position: str

    location: str

    email: str

    phone: str

    experience_total: float

    status: str

    top_skills: list[str] = Field(
        default_factory=list
    )

    extraction_confidence: float

    created_at: datetime