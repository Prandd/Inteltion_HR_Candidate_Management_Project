import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    Float
)

from .database import Base



def _uuid() -> str:
    return str(uuid.uuid4())



def _utcnow() -> datetime:
    return datetime.now(timezone.utc)





class Candidate(Base):

    __tablename__ = "candidates"


    candidate_id = Column(
        String,
        primary_key=True,
        default=_uuid
    )


    full_name = Column(
        String,
        nullable=False,
        default=""
    )


    email = Column(
        String,
        nullable=False,
        default=""
    )


    phone = Column(
        String,
        nullable=False,
        default=""
    )


    location = Column(
        String,
        nullable=False,
        default=""
    )


    applied_position = Column(
        String,
        nullable=False,
        default=""
    )


    summary = Column(
        Text,
        nullable=False,
        default=""
    )


    skills = Column(
        JSON,
        nullable=False,
        default=list
    )


    experience = Column(
        JSON,
        nullable=False,
        default=list
    )


    experience_total = Column(
        Float,
        nullable=False,
        default=0
    )


    current_salary = Column(
        Float,
        nullable=False,
        default=0
    )


    expected_salary = Column(
        Float,
        nullable=False,
        default=0
    )


    education = Column(
        JSON,
        nullable=False,
        default=list
    )


    hr_comment = Column(
        Text,
        nullable=False,
        default=""
    )


    line_manager_comment = Column(
        Text,
        nullable=False,
        default=""
    )


    extraction_confidence = Column(
        Float,
        nullable=False,
        default=0
    )


    raw_text_snippet = Column(
        Text,
        nullable=False,
        default=""
    )


    status = Column(
        String,
        nullable=False,
        default="New"
    )


    resume_url = Column(
        String,
        nullable=False,
        default=""
    )


    resume_filename = Column(
        String,
        nullable=False,
        default=""
    )


    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow
    )


    updated_at = Column(
        DateTime,
        nullable=True,
        default=None,
        onupdate=lambda: datetime.now(timezone.utc)
    )







class CandidateStatusHistory(Base):

    __tablename__ = "candidate_status_history"



    id = Column(
        Integer,
        primary_key=True,
        index=True
    )



    candidate_id = Column(
        String,
        ForeignKey("candidates.candidate_id"),
        nullable=False
    )



    # New status after transition
    status = Column(
        String,
        nullable=False
    )



    # Status before transition
    # Example:
    # Assessment -> CV rejected
    # previous_status = "Assessment"
    previous_status = Column(
        String,
        nullable=True
    )



    action = Column(
        String,
        nullable=False,
        default="Changed status"
    )



    changed_by = Column(
        String,
        nullable=False,
        default="HR Admin"
    )



    changed_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )



class CandidateComment(Base):

    __tablename__ = "candidate_comments"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    candidate_id = Column(
        String,
        ForeignKey("candidates.candidate_id"),
        nullable=False
    )


    author = Column(
        String,
        nullable=False,
        default="HR Admin"
    )


    role = Column(
        String,
        nullable=False,
        default="HR"
    )


    comment = Column(
        Text,
        nullable=False
    )


    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )


    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )



class Position(Base):

    __tablename__ = "positions"



    id = Column(
        String,
        primary_key=True,
        default=_uuid
    )



    title = Column(
        String,
        nullable=False,
        default=""
    )



    department = Column(
        String,
        nullable=False,
        default=""
    )



    location = Column(
        String,
        nullable=False,
        default=""
    )



    description = Column(
        Text,
        nullable=False,
        default=""
    )



    status = Column(
        String,
        nullable=False,
        default="Open"
    )



    requirements = Column(
        JSON,
        nullable=False,
        default=list
    )



    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow
    )



    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow
    )