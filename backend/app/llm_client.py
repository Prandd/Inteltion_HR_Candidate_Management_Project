"""Single entry point for CV extraction.

1. LLM_SERVICE_URL set (Vercel binding, or manual for local) -> call the
   llm-service over HTTP: POST {LLM_SERVICE_URL}/extract
2. Otherwise -> in-process import from ../llm-service/cv-parsing (local dev)
3. Otherwise -> the deterministic mock in app/extraction.py
"""
from __future__ import annotations

import os
import sys

import httpx

_URL_ENV = "LLM_SERVICE_URL"
_TIMEOUT_SECONDS = 120.0  # LLM calls are slow


def _http_extract(base_url: str, file_bytes: bytes, filename: str | None) -> dict:
    url = base_url.rstrip("/") + "/extract"
    resp = httpx.post(
        url,
        files={"file": (filename or "cv", file_bytes, "application/octet-stream")},
        timeout=_TIMEOUT_SECONDS,
    )
    resp.raise_for_status()
    return resp.json()


def _local_extract():
    path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../llm-service/cv-parsing")
    )
    if os.path.isdir(path):
        if path not in sys.path:
            sys.path.insert(0, path)
        try:
            from extractor import extract_candidate as real  # type: ignore
            return real
        except ImportError:
            pass
    from .extraction import extract_candidate as mock
    return mock


def extract_candidate(file_bytes: bytes, filename: str | None = None) -> dict:
    base_url = os.environ.get(_URL_ENV, "").strip()
    if base_url:
        return _http_extract(base_url, file_bytes, filename)
    return _local_extract()(file_bytes, filename=filename)
