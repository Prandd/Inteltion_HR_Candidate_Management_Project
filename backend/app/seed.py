import json
import logging
import os
import uuid

from sqlalchemy.orm import Session

from .config import settings
from .database import SessionLocal
from .models_db import Candidate, CommentLog, HRAccount, OwnershipHistory, StatusHistory, utcnow
from .schemas import CandidateBase
from .security import hash_password
from .services import normalize_email

log = logging.getLogger("app.seed")


def seed_admin_if_empty(db: Session) -> HRAccount | None:
    """F2 - bootstrap the FIRST admin from .env, and only while hr_accounts is
    empty. Every other account is created through POST /api/hr-accounts; the
    env vars are not a login path, just a way in on a fresh database."""
    existing = db.query(HRAccount).order_by(HRAccount.created_at.asc()).first()
    if existing is not None:
        return existing

    if settings.seed_admin_password == "password123":
        log.warning(
            "AUTH: seeding the first admin with the DEFAULT password. "
            "Set SEED_ADMIN_PASSWORD in .env before this touches real data."
        )

    now = utcnow()
    admin = HRAccount(
        account_id=str(uuid.uuid4()),
        username=settings.seed_admin_username,
        email=settings.seed_admin_email,
        full_name=settings.seed_admin_full_name,
        password_hash=hash_password(settings.seed_admin_password),
        role="admin",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    log.info("AUTH: seeded first admin account username=%s", admin.username)
    return admin


def _backfill_comments(db: Session, author: HRAccount) -> int:
    """F3 phase 1 - move any non-empty hr_comment / line_manager_comment into
    comment_logs, one row each, attributed to the seed admin with
    commented_at = the candidate's updated_at. Runs once, while the table is
    empty; after that comment_logs is the only writer."""
    if db.query(CommentLog).count() > 0:
        return 0

    made = 0
    now = utcnow()
    for row in db.query(Candidate).all():
        for column, comment_type in (
            ("hr_comment", "hr"),
            ("line_manager_comment", "line_manager"),
        ):
            text = (getattr(row, column) or "").strip()
            if not text:
                continue
            db.add(CommentLog(
                comment_id=str(uuid.uuid4()),
                candidate_id=row.candidate_id,
                author_account_id=author.account_id,
                author_name=author.full_name or author.username,
                author_role="hr" if comment_type == "hr" else "line_manager",
                comment_type=comment_type,
                comment=text,
                commented_at=row.updated_at or now,
                created_at=now,
                updated_at=now,
                is_edited=False,
            ))
            made += 1
    if made:
        db.commit()
        log.info("[seed] backfilled %d legacy comment(s) into comment_logs", made)
    return made


def seed_candidates_if_empty(db: Session, author: HRAccount) -> None:
    """On first run, load shared-contracts/mock-candidates.json into the DB so
    both frontend lanes see realistic data immediately."""
    if db.query(Candidate).count() > 0:
        return

    path = settings.seed_file
    if not os.path.exists(path):
        log.warning("[seed] seed file not found at '%s' - starting with an empty DB", path)
        return

    # utf-8-sig tolerates a BOM; a Windows editor re-saving the fixture would
    # otherwise break seeding with "Expecting value: line 1 column 1".
    with open(path, "r", encoding="utf-8-sig") as fh:
        items = json.load(fh)

    # candidate_id is a 7-digit running number in creation order - the JSON's
    # own candidate_id is ignored so seeded + uploaded rows share one format.
    now = utcnow()
    for idx, item in enumerate(items, start=1):
        candidate_id = f"{idx:07d}"
        fields = CandidateBase.model_validate(item).model_dump(mode="json")
        row = Candidate(
            candidate_id=candidate_id,
            email_normalized=normalize_email(fields.get("email")),
            upload_status=item.get("upload_status", "Done"),
            resume_url=item.get("resume_url", ""),
            resume_filename=item.get("resume_filename", ""),
            before_rejected_status=item.get("before_rejected_status", ""),
            # Round 5 - seeded rows are attributed to the seed admin, same as
            # the status/comment backfills below.
            owner_account_id=author.account_id,
            # Legacy columns: written once here so _backfill_comments() can turn
            # them into comment_logs rows. The API never writes them again.
            hr_comment=item.get("hr_comment", ""),
            line_manager_comment=item.get("line_manager_comment", ""),
            **fields,
        )
        db.add(row)
        db.add(StatusHistory(
            history_id=str(uuid.uuid4()),
            candidate_id=candidate_id,
            from_status=None,
            to_status=fields.get("status", "New"),
            changed_by=author.account_id,
            changed_at=now,
            reason="seeded",
        ))
        db.add(OwnershipHistory(
            ownership_history_id=str(uuid.uuid4()),
            candidate_id=candidate_id,
            from_owner_account_id=None,
            to_owner_account_id=author.account_id,
            changed_by=author.account_id,
            changed_at=now,
            reason="seeded",
        ))
    db.commit()
    log.info("[seed] inserted %d mock candidates from %s", len(items), path)


def seed_if_empty() -> None:
    db = SessionLocal()
    try:
        admin = seed_admin_if_empty(db)
        if admin is None:
            return
        seed_candidates_if_empty(db, admin)
        _backfill_comments(db, admin)
    finally:
        db.close()
