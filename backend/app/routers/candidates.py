import os
import sys
import uuid

from datetime import datetime, timezone

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
from ..models_db import Candidate

from ..schemas import (
    STATUS_VALUES,
    CandidateBase,
    CandidateOut,
    CandidateSummary,
    CandidateUpdate,
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


    return {

        "data":

            _to_out(row),

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

    file: UploadFile = File(...),

    db: Session = Depends(get_db)

):


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

        "data":

            _to_out(row),


        "error": None

    }