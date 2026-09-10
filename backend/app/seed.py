import json
import os

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

        # candidate_id is a 7-digit running number in creation order - the JSON's
        # own candidate_id is ignored so seeded + uploaded rows share one format.
        for idx, item in enumerate(items, start=1):
            fields = CandidateBase.model_validate(item).model_dump(mode="json")
            db.add(Candidate(
                candidate_id=f"{idx:07d}",
                upload_status=item.get("upload_status", "Done"),
                resume_url=item.get("resume_url", ""),
                resume_filename=item.get("resume_filename", ""),
                **fields,
            ))
        db.commit()
        print(f"[seed] inserted {len(items)} mock candidates from {path}")
    finally:
        db.close()
