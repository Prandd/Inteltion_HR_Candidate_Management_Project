# backend/ - Inteltion HR Candidate API (MVP, Member 3)

FastAPI + SQLite + local disk. **Everything external is mocked** for this sprint:

| External thing | This week | Day 6 swap |
|---|---|---|
| LLM CV extraction (Member 4) | `app/extraction.py` returns varied schema-valid fake data, ignores file bytes | change one import in `app/routers/candidates.py` |
| File storage (Azure Blob) | `app/storage.py` `LocalDiskStorage` writes to `data/uploads/`, served at `/files/...` | add `AzureBlobStorage` with same `.save()` signature |
| Database (Postgres) | SQLite file at `data/dev.db` | point `DATABASE_URL` at Postgres (compose service is pre-written, commented) |

## Run it - Docker (what you hand to teammates)

From the repo root (where `docker-compose.yml` lives):

```bash
docker compose up --build
```

- API: http://localhost:8000  Swagger UI: http://localhost:8000/docs
- Seeded with the 9 mock candidates from `shared-contracts/mock-candidates.json`
- No `.env`, no Python install needed. `docker compose down -v` to reset.

## Run it - local Python (faster iteration)

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows.  macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Runs with built-in defaults; copy `.env.example` to `.env` only if you want to change ports/paths.

## Tests

```bash
cd backend
pytest
```

Smoke tests: health, list envelope, 404 shape, upload rejects non-pdf/docx, upload -> get -> edit roundtrip, bad-status rejection.

## API surface (frozen contract - see `shared-contracts/`)

| Method | Path | Success | Notes |
|---|---|---|---|
| `POST` | `/api/candidates/upload` | `201` | multipart `file` (.pdf/.docx) -> full candidate |
| `GET`  | `/api/candidates` | `200` | list of summary objects |
| `GET`  | `/api/candidates/{id}` | `200` / `404` | full candidate |
| `PUT`  | `/api/candidates/{id}` | `200` / `400` / `404` | accepts full editable schema, overwrites |
| `GET`  | `/api/candidates/{id}/resume-url` | `200` / `404` | `{ resume_url, filename }` |
| `GET`  | `/health` | `200` | |

Every response: `{ "data": ..., "error": null }` on success, `{ "data": null, "error": "message" }` on failure.
Errors: `400` bad file / validation, `404` unknown id, `500` unexpected.

## Layout

```
backend/
  app/
    main.py           FastAPI app, CORS, /files mount, uniform error envelope
    config.py         env-driven settings (+ safe defaults)
    database.py       SQLAlchemy engine / session
    models_db.py      Candidate ORM row (skills/experience/education = JSON columns)
    schemas.py        Pydantic models = THE CONTRACT (mirrors shared-contracts/schema.json)
    storage.py        LocalDiskStorage now; AzureBlobStorage later
    extraction.py     MOCK extract_candidate(bytes) -> dict
    seed.py           loads mock-candidates.json on first boot
    routers/
      candidates.py   all endpoints
  tests/test_smoke.py
  Dockerfile
  requirements.txt
  .env.example
```
