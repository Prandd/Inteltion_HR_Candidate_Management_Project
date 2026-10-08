"""HTTP wrapper around the CV extraction engine in cv-parsing/.

Internal-only Vercel service: no public rewrite points here. The backend
reaches it through the LLM_SERVICE_URL binding declared in vercel.json.
"""
import os
import sys

from fastapi import FastAPI, File, HTTPException, UploadFile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cv-parsing"))

from extractor import extract_candidate  # noqa: E402

app = FastAPI(title="Inteltion LLM Service", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    # extract_candidate never raises for expected failures; it returns a
    # schema-valid fallback dict with extraction_confidence 0.0 instead.
    return extract_candidate(content, filename=file.filename)
