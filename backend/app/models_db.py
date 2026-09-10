from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Float, String, Text

from .database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Candidate(Base):
    """One row per candidate. Nested skills / experience / education are stored
    as JSON columns - fine for the MVP, no child tables needed."""

    __tablename__ = "candidates"

    # 7-digit zero-padded running number ("0000001"), assigned by the backend in
    # creation order - see next_candidate_id() in routers/candidates.py.
    candidate_id = Column(String, primary_key=True)
    full_name = Column(String, nullable=False, default="")
    email = Column(String, nullable=False, default="")
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
    hr_comment = Column(Text, nullable=False, default="")
    line_manager_comment = Column(Text, nullable=False, default="")
    extraction_confidence = Column(Float, nullable=False, default=0)
    raw_text_snippet = Column(Text, nullable=False, default="")
    status = Column(String, nullable=False, default="New")  # HR pipeline
    upload_status = Column(String, nullable=False, default="Not Uploaded")  # file lifecycle
    resume_url = Column(String, nullable=False, default="")
    resume_filename = Column(String, nullable=False, default="")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )
