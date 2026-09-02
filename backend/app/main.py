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
from .database import Base, engine
from .routers import candidates
from .seed import seed_if_empty


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ensure_dirs()
    Base.metadata.create_all(bind=engine)
    seed_if_empty()
    yield


app = FastAPI(
    title="Inteltion HR Candidate API (MVP)",
    version="0.1.0",
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
app.mount("/files", StaticFiles(directory=settings.upload_dir), name="files")
app.include_router(candidates.router, prefix="/api")


@app.get("/health")
def health():
    return {"data": {"status": "ok"}, "error": None}


# ---- Every error response uses the same { "data": null, "error": "..." } shape ----


@app.exception_handler(StarletteHTTPException)
async def _http_exception_handler(_request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"data": None, "error": str(exc.detail)},
    )


@app.exception_handler(RequestValidationError)
async def _validation_exception_handler(_request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content=jsonable_encoder(
            {"data": None, "error": "Validation error", "detail": exc.errors()}
        ),
    )


@app.exception_handler(Exception)
async def _unhandled_exception_handler(_request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"data": None, "error": f"Internal server error: {exc}"},
    )
