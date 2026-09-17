import os
import sys
import uuid

from datetime import datetime, timezone
from ..models_db import Candidate, CandidateStatusHistory

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)

from sqlalchemy.orm import Session


# ==================================================
# Import LLM CV Extractor
# ==================================================

LLM_SERVICE_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../../../llm-service/cv-parsing"
    )
)


if LLM_SERVICE_PATH not in sys.path:
    sys.path.append(LLM_SERVICE_PATH)


try:

    from extractor import extract_candidate


except Exception as e:

    raise ImportError(
        f"Cannot import CV extractor from {LLM_SERVICE_PATH}: {e}"
    )



# ==================================================
# Backend imports
# ==================================================

from ..config import settings
from ..database import get_db
from ..models_db import (
    Candidate,
    CandidateStatusHistory,
    CandidateComment
)

from ..schemas import (
    STATUS_VALUES,
    CandidateBase,
    CandidateOut,
    CandidateSummary,
    CandidateUpdate,
    CommentCreate,
    CommentOut
)

from ..storage import storage



router = APIRouter(
    tags=["candidates"]
)



ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx"
}


_STATUS_SET = set(
    STATUS_VALUES
)



# ==================================================
# FORMAT RESPONSE
# ==================================================


def _to_out(row: Candidate):

    data = (
        CandidateOut
        .model_validate(row)
        .model_dump(mode="json")
    )


    for key, value in data.items():

        if value is None:

            if key in [
                "skills",
                "experience",
                "education"
            ]:

                data[key] = []

            else:

                data[key] = "-"


    return data






def _to_summary(row: Candidate):

    return CandidateSummary(

        candidate_id=row.candidate_id,

        full_name=
            row.full_name
            or "Unknown Candidate",

        applied_position=
            row.applied_position
            or "-",


        location=
            row.location
            or "-",


        email=
            row.email
            or "-",


        phone=
            row.phone
            or "-",


        experience_total=
            row.experience_total
            or 0,


        status=
            row.status
            or "New",


        top_skills=[

            s.get("skill", "")

            for s in (row.skills or [])

        ][:5],


        extraction_confidence=
            row.extraction_confidence
            or 0,


        created_at=row.created_at

    ).model_dump(mode="json")





# ==================================================
# GET ALL
# ==================================================


@router.get("/candidates")
def list_candidates(

    db: Session = Depends(get_db)

):

    rows = (

        db.query(Candidate)

        .order_by(
            Candidate.created_at.desc()
        )

        .all()

    )


    return {

        "data": [

            _to_summary(row)

            for row in rows

        ],

        "error": None

    }





# ==================================================
# GET ONE
# ==================================================


@router.get("/candidates/{candidate_id}")
def get_candidate(

    candidate_id: str,

    db: Session = Depends(get_db)

):

    row = db.get(

        Candidate,

        candidate_id

    )


    if row is None:

        raise HTTPException(

            status_code=404,

            detail="Candidate not found"

        )
    
    history = (

        db.query(CandidateStatusHistory)

        .filter(
            CandidateStatusHistory.candidate_id
            ==
            row.candidate_id
        )

        .order_by(
            CandidateStatusHistory.changed_at.desc()
        )

        .all()

    )
    
    data = _to_out(row)

    data["status_history"] = [

        {
            "status": h.status,
            "previous_status": h.previous_status,
            "action": h.action,
            "changed_by": h.changed_by,
            "changed_at": h.changed_at
        }

        for h in history

    ]


    return {
        "data": data,
        "error": None
    }




# ==================================================
# COMMENTS
# ==================================================


@router.get("/candidates/{candidate_id}/comments")
def get_comments(

    candidate_id: str,

    db: Session = Depends(get_db)

):

    candidate = db.get(
        Candidate,
        candidate_id
    )


    if candidate is None:

        raise HTTPException(
            status_code=404,
            detail="Candidate not found"
        )


    comments = (

        db.query(CandidateComment)

        .filter(
            CandidateComment.candidate_id
            ==
            candidate_id
        )

        .order_by(
            CandidateComment.created_at.desc()
        )

        .all()

    )


    return {

        "data": comments,

        "error": None

    }
    
@router.post("/candidates/{candidate_id}/comments")
def create_comment(

    candidate_id: str,

    payload: CommentCreate,

    db: Session = Depends(get_db)

):


    candidate = db.get(
        Candidate,
        candidate_id
    )


    if candidate is None:

        raise HTTPException(
            status_code=404,
            detail="Candidate not found"
        )



    comment = CandidateComment(

        candidate_id=candidate_id,

        author=payload.author,

        role=payload.role,

        comment=payload.comment

    )


    db.add(comment)

    db.commit()

    db.refresh(comment)



    return {

        "data": comment,

        "error": None

    }

# ==================================================
# UPDATE
# ==================================================


@router.put("/candidates/{candidate_id}")
def update_candidate(

    candidate_id: str,

    payload: CandidateUpdate,

    db: Session = Depends(get_db)

):

    row = db.get(

        Candidate,

        candidate_id

    )


    if row is None:

        raise HTTPException(

            status_code=404,

            detail="Candidate not found"

        )


    data = payload.model_dump(

        mode="json",

        exclude_unset=True

    )


    if "email" in data:

        if data["email"] and "@" not in data["email"]:

            raise HTTPException(

                status_code=400,

                detail="Invalid email"

            )



    if "status" in data:

        if data["status"] not in _STATUS_SET:

            raise HTTPException(

                status_code=400,

                detail="Invalid status"

            )

    old_status = row.status


    status_changed = (
        "status" in data
        and data["status"] != old_status
    )



    if status_changed:


        history = CandidateStatusHistory(

            candidate_id=row.candidate_id,

            status=data["status"],

            previous_status=old_status,

            action="Changed status",

            changed_by="HR Admin"

        )


        db.add(history)





    for key, value in data.items():

        if value is not None:

            setattr(
                row,
                key,
                value
            )


    row.updated_at = datetime.now(
        timezone.utc
    )


    db.commit()

    db.refresh(row)


    return {

        "data":

            _to_out(row),

        "error": None

    }
    
# ==================================================
# RESUME URL
# ==================================================


@router.get("/candidates/{candidate_id}/resume-url")
def get_resume_url(

    candidate_id: str,

    db: Session = Depends(get_db)

):

    row = db.get(

        Candidate,

        candidate_id

    )


    if row is None:

        raise HTTPException(

            status_code=404,

            detail="Candidate not found"

        )


    return {

        "data": {

            "resume_url":

                row.resume_url,


            "filename":

                row.resume_filename

        },

        "error": None

    }





# ==================================================
# UPLOAD
# ==================================================


@router.post(
    "/candidates/upload",
    status_code=201
)
async def upload_candidate(

    file: UploadFile,

    force: bool = False,

    candidate_id: str | None = None,

    db: Session = Depends(get_db)

):


    print(
        "========== UPLOAD DEBUG =========="
    )

    print(
        "force =",
        force
    )

    print(
        "candidate_id =",
        candidate_id
    )

    print(
        "filename =",
        file.filename
    )

    print(
        "=================================="
    )


    # -------------------------------
    # Validate extension
    # -------------------------------

    ext = os.path.splitext(

        file.filename or ""

    )[1].lower()



    if ext not in ALLOWED_EXTENSIONS:

        raise HTTPException(

            status_code=400,

            detail="Only PDF and DOCX allowed"

        )



    # -------------------------------
    # Read file
    # -------------------------------

    content = await file.read()



    if not content:

        raise HTTPException(

            status_code=400,

            detail="Empty file"

        )



    if len(content) > settings.max_upload_mb * 1024 * 1024:

        raise HTTPException(

            status_code=400,

            detail="File too large"

        )





    # -------------------------------
    # Create candidate id
    # -------------------------------

    if not force:

        candidate_id = str(
            uuid.uuid4()
        )
    # -------------------------------
    # Save resume
    # -------------------------------

    stored = storage.save(

        candidate_id,

        file.filename,

        content

    )





    # -------------------------------
    # Extract CV
    # -------------------------------

    raw = extract_candidate(

        content,

        filename=file.filename

    )
    
    # -------------------------------
    # Duplicate Check
    # -------------------------------

    if not force:

        existing = None


        if raw.get("email"):

            existing = (
                db.query(Candidate)
                .filter(
                    Candidate.email == raw["email"]
                )
                .first()
            )


        if existing:

            return {
                "duplicate": True,

                "candidate": {
                    "candidate_id":
                        existing.candidate_id,

                    "full_name":
                        existing.full_name,

                    "email":
                        existing.email,

                    "phone":
                        existing.phone,

                    "applied_position":
                        existing.applied_position,

                    "status":
                        existing.status
                },

                "data": None,

                "error": None
            }





    print("==============================")

    print("EXTRACT RESULT")

    print(raw)

    print("==============================")





    # -------------------------------
    # Normalize extractor output
    # -------------------------------

    if not isinstance(raw, dict):

        raw = {}



    # name -> full_name

    if not raw.get("full_name"):


        if raw.get("name"):

            raw["full_name"] = raw["name"]



        elif raw.get("candidate_name"):

            raw["full_name"] = raw["candidate_name"]





    # default values

    raw.setdefault(
        "full_name",
        ""
    )


    raw.setdefault(
        "email",
        ""
    )


    raw.setdefault(
        "phone",
        ""
    )


    raw.setdefault(
        "location",
        ""
    )


    raw.setdefault(
        "applied_position",
        ""
    )


    raw.setdefault(
        "summary",
        ""
    )


    raw.setdefault(
        "skills",
        []
    )


    raw.setdefault(
        "experience",
        []
    )


    raw.setdefault(
        "education",
        []
    )





    # -------------------------------
    # Validate schema
    # -------------------------------

    fields = (

        CandidateBase

        .model_validate(raw)

        .model_dump(mode="json")

    )





    # -------------------------------
    # Save database
    # -------------------------------

    # -------------------------------
    # Save database
    # -------------------------------

    if force and candidate_id:


        row = db.get(
            Candidate,
            candidate_id
        )


        if row is None:

            raise HTTPException(
                status_code=404,
                detail="Candidate not found"
            )


        # Update existing candidate

        for key, value in fields.items():

            setattr(
                row,
                key,
                value
            )


        row.resume_url = stored["url"]

        row.resume_filename = stored["filename"]
        
        history = CandidateStatusHistory(

            candidate_id=row.candidate_id,

            status=row.status,

            previous_status=row.status,

            action="Resume replaced",

            changed_by="HR Admin"

        )


        db.add(history)

        row.updated_at = datetime.now(
            timezone.utc
        )



    else:

        row = Candidate(

            candidate_id=candidate_id,

            resume_url=stored["url"],

            resume_filename=stored["filename"],

            **fields

        )


        db.add(row)


    db.commit()

    db.refresh(row)





    return {

        "duplicate": False,

        "data":
            _to_out(row),

        "error": None

    }
    
    # =========================
# DELETE
# =========================

@router.delete("/candidates/{candidate_id}")
def delete_candidate(

    candidate_id: str,

    db: Session = Depends(get_db)

):


    row = db.get(

        Candidate,

        candidate_id

    )



    if row is None:

        raise HTTPException(

            status_code=404,

            detail="Candidate not found"

        )




    db.delete(row)

    db.commit()



    return {

        "data": {

            "candidate_id": candidate_id,

            "message": "Candidate deleted successfully"

        },

        "error": None

    }