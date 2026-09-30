import logging
from contextlib import asynccontextmanager

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
from .routers import auth, candidates, comments, hr_accounts, pending_uploads
from .seed import seed_if_empty
from .statuses import STATUS_VALUES, assert_valid_db_statuses
from .storage import LocalDiskStorage, log_active_storage, storage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
log = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # First, so a misconfigured deploy says so before it does anything else.
    # It runs here rather than in build_storage() because `storage` is built at
    # import time, before basicConfig() above has installed a handler.
    log_active_storage()

    ensure_dirs()
    Base.metadata.create_all(bind=engine)
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
app.include_router(candidates.router, prefix="/api")
app.include_router(comments.router, prefix="/api")
app.include_router(pending_uploads.router, prefix="/api")


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
    return JSONResponse(
        status_code=500,
        content={"data": None, "error": f"Internal server error: {exc}"},
    )
