import json
import os
import uuid

from .config import settings
from .database import SessionLocal
from .models_db import Candidate
from .schemas import CandidateBase


def seed_if_empty() -> None:
    """On first run, load shared-contracts/mock-candidates.json into the DB so
    both frontend lanes see realistic data immediately."""
    db = SessionLocal()
    try:
        if db.query(Candidate).count() > 0:
            return

        path = settings.seed_file
        if not os.path.exists(path):
            print(f"[seed] seed file not found at '{path}' - starting with an empty DB")
            return

        with open(path, "r", encoding="utf-8") as fh:
            items = json.load(fh)

        for item in items:
            fields = CandidateBase.model_validate(item).model_dump(mode="json")
            db.add(Candidate(
                candidate_id=str(item.get("candidate_id") or uuid.uuid4()),
                resume_url=item.get("resume_url", ""),
                resume_filename=item.get("resume_filename", ""),
                **fields,
            ))
        db.commit()
        print(f"[seed] inserted {len(items)} mock candidates from {path}")
    finally:
        db.close()
