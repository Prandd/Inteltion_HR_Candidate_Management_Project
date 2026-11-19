import logging
from contextlib import asynccontextmanager

import sqlalchemy as sa
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import models_db  # noqa: F401  - registers ORM models on Base
from .config import ensure_dirs, settings
from .database import Base, SessionLocal, engine
from .models_db import Candidate
from .routers import auth, candidates, comments, hr_accounts, pending_uploads, positions
from .schema_compat import (
    backfill_contacts_from_other,
    ensure_contacts_column,
    ensure_unicode_comment_column,
    ensure_unicode_text_columns,
)
from .seed import seed_if_empty
from .statuses import STATUS_VALUES, assert_valid_db_statuses
from .storage import LocalDiskStorage, log_active_storage, storage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
log = logging.getLogger("app.main")


def _drop_unique_email_index() -> None:
    """Same change as migration 0007, applied at boot. The Azure SQL database
    was built by create_all() (back when email_normalized was UNIQUE) and has
    never been stamped for Alembic, so the migration cannot run there - and
    while that unique index exists, "create new" on a duplicate upload 500s.
    No-op once no unique index is left on the column."""
    inspector = sa.inspect(engine)
    unique = [
        ix["name"] for ix in inspector.get_indexes("candidates")
        if ix.get("unique") and ix.get("column_names") == ["email_normalized"]
    ]
    if not unique:
        return
    with engine.begin() as conn:
        for name in unique:
            conn.execute(sa.schema.DropIndex(sa.Index(name, _table=Candidate.__table__)))
        sa.Index("ix_candidates_email_normalized",
                 Candidate.__table__.c.email_normalized).create(conn)
    log.info("Dropped unique index on candidates.email_normalized: %s", unique)


def _ensure_contact_other_column() -> None:
    """Support existing create_all databases as well as Alembic-managed ones."""
    if "contact_other" in {column["name"] for column in sa.inspect(engine).get_columns("candidates")}:
        return
    column = sa.schema.CreateColumn(Candidate.__table__.c.contact_other).compile(dialect=engine.dialect)
    with engine.begin() as connection:
        connection.execute(sa.text(f"ALTER TABLE candidates ADD {column}"))
    log.info("Added candidates.contact_other")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # First, so a misconfigured deploy says so before it does anything else.
    # It runs here rather than in build_storage() because `storage` is built at
    # import time, before basicConfig() above has installed a handler.
    log_active_storage()

    ensure_dirs()
    Base.metadata.create_all(bind=engine)
    _drop_unique_email_index()
    _ensure_contact_other_column()
    with engine.begin() as connection:
        if ensure_contacts_column(connection):
            log.info("Added candidates.contacts")
    try:
        with engine.begin() as connection:
            moved = backfill_contacts_from_other(connection)
        if moved:
            log.info("Moved the old 'other contact' text into contacts for %d candidate(s)", moved)
    except Exception:
        # Retried on the next start; nothing is lost in the meantime (the old
        # text stays in contact_other until it has been copied across).
        log.exception("Could not move contact_other into contacts; will retry on next start")
    with engine.begin() as connection:
        if ensure_unicode_comment_column(connection):
            log.info("Upgraded comment_logs.comment to Unicode NVARCHAR(MAX)")
    try:
        with engine.begin() as connection:
            upgraded = ensure_unicode_text_columns(connection, Base.metadata)
        if upgraded:
            log.info("Upgraded %d text column(s) to Unicode NVARCHAR: %s",
                     len(upgraded), ", ".join(upgraded))
    except Exception:
        # Until this succeeds non-Latin text is stored as '?', but that is no
        # reason to refuse to boot. The upgrade is one transaction, so a
        # failure leaves the schema untouched, and it retries on the next start.
        log.exception("Could not upgrade text columns to Unicode; will retry on next start")
    seed_if_empty()

    # F6 step 4 - catch status drift at boot, not when the Kanban silently drops
    # a candidate into a column the frontend does not render.
    db = SessionLocal()
    try:
        assert_valid_db_statuses(db)
    finally:
        db.close()

    log.info("STATUS: %d canonical values -> %s", len(STATUS_VALUES), STATUS_VALUES)
    yield


app = FastAPI(
    title="Inteltion HR Candidate API (MVP)",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ensure_dirs()
if isinstance(storage, LocalDiskStorage):
    # Only meaningful for local-disk storage - Azure Blob resumes are served via
    # resolve_path_url() (a signed URL straight to blob storage), not through the API.
    app.mount("/files", StaticFiles(directory=settings.upload_dir), name="files")
app.include_router(auth.router, prefix="/api")
app.include_router(hr_accounts.router, prefix="/api")
app.include_router(hr_accounts.options_router, prefix="/api")
app.include_router(candidates.router, prefix="/api")
app.include_router(comments.router, prefix="/api")
app.include_router(pending_uploads.router, prefix="/api")
app.include_router(positions.router, prefix="/api")


@app.get("/health")
def health():
    """Open (no token). `storage` reports the ACTIVE backend - account and
    container name only, never the key - so the team can confirm which storage
    account they are hitting without reading anyone's .env."""
    return {
        "data": {
            "status": "ok",
            "storage": storage.describe(),
            "statuses": STATUS_VALUES,
        },
        "error": None,
    }


# ---- Every error response uses the same { "data": null, "error": "..." } shape ----


@app.exception_handler(StarletteHTTPException)
async def _http_exception_handler(_request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"data": None, "error": str(exc.detail)},
        headers=getattr(exc, "headers", None),
    )


def _json_safe(value):
    """Recursively replace a non-finite float (inf/-inf/nan) with its string
    form. Starlette's JSONResponse calls json.dumps(..., allow_nan=False), so
    a validation error whose *cause* was a non-finite float - e.g. a client
    sending {"score": Infinity} against a field that rejects it - would
    otherwise crash while trying to report that very error: Pydantic's
    ValidationError.errors() embeds the offending value verbatim, and
    encoding the 400 response then raises its own ValueError, surfacing as an
    opaque 500 instead of the clean 400 the client should see."""
    if isinstance(value, float):
        if value != value:  # NaN is the only float that is not equal to itself
            return "NaN"
        if value == float("inf"):
            return "Infinity"
        if value == float("-inf"):
            return "-Infinity"
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return value


@app.exception_handler(RequestValidationError)
async def _validation_exception_handler(_request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content=jsonable_encoder(
            {"data": None, "error": "Validation error", "detail": _json_safe(exc.errors())}
        ),
    )


@app.exception_handler(Exception)
async def _unhandled_exception_handler(_request, exc: Exception):
    # Logged in full, returned generic: a DB driver error's text carries the
    # server name, SQL and parameter values, none of which belong in a browser.
    log.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"data": None, "error": "Internal server error"},
    )
