# backend/ - Inteltion HR Candidate API (MVP, Member 3)

> 📋 **Teammates:** see [`CHANGELOG.md`](CHANGELOG.md) (ภาษาไทย) for what's been built, what
> changed in the API contract, curl examples, and what each lane needs to update.
>
> ⚠️ **Nothing here has been run yet** — `pytest` still needs to pass before this merges to `main`.

FastAPI + SQLite + local disk. **Everything external is mocked** for this sprint:

| External thing | This week | Real deploy |
|---|---|---|
| LLM CV extraction (Member 4) | `app/extraction.py` returns varied schema-valid fake data, ignores file bytes | change one import in `app/routers/candidates.py` |
| File storage | `app/storage.py` `LocalDiskStorage` writes to `data/uploads/`, served at `/files/...` (default, zero setup) | **implemented** - set `AZURE_STORAGE_CONNECTION_STRING` and the app switches to `AzureBlobStorage` automatically, same interface, no code change |
| Database (Postgres) | SQLite file at `data/dev.db` | point `DATABASE_URL` at Postgres (compose service is pre-written, commented) |

## File storage: local disk vs Azure Blob

Picked automatically at startup, purely from env vars (`app/storage.py::build_storage()`):

- **`AZURE_STORAGE_CONNECTION_STRING` unset (default)** -> `LocalDiskStorage`. Files land in
  `UPLOAD_DIR`, served back at `/files/<candidate_id>/<filename>`. Nothing to configure.
- **`AZURE_STORAGE_CONNECTION_STRING` set** -> `AzureBlobStorage`. Uploads go to the container
  named by `AZURE_STORAGE_CONTAINER_NAME` (default `resumes`), created automatically if missing.
  The container is **not** made public - resumes are personal data. `GET /api/candidates/{id}/resume-url`
  returns a fresh, read-only **SAS link** valid for `RESUME_SAS_EXPIRY_MINUTES` (default 60);
  re-call it rather than caching the `resume_url` on the candidate record indefinitely.
  If Azure init fails (bad creds, no network) the app logs a warning and falls back to local
  disk instead of refusing to start.

No credential is ever hardcoded - only `.env` (git-ignored) or the server's real environment.
See `.env.example` for the two variables an admin needs to set.

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

Smoke tests: auth guard + login, list/filter/keyword search, running-id format,
multi-file upload, conditional delete, 404 shape, bad-status rejection.

## Auth

Single Admin/HR account (env-overridable, default `admin` / `password123`).

```bash
curl -s -X POST localhost:8000/api/auth/login \
  -H 'content-type: application/json' \
  -d '{"username":"admin","password":"password123"}'
# -> { "data": { "access_token": "<jwt>", "token_type": "bearer" }, "error": null }
```

Send `Authorization: Bearer <jwt>` on every `/api/candidates/*` call. Missing/expired -> `401`.

## API surface (see `shared-contracts/`)

| Method | Path | Success | Notes |
|---|---|---|---|
| `POST` | `/api/auth/login` | `200` / `401` | `{username, password}` -> `{access_token, token_type}` |
| `POST` | `/api/candidates/upload` | `201` / `400` | multipart **`files`** (repeatable, .pdf/.docx) -> `{created[], failed[], count}` |
| `GET`  | `/api/candidates` | `200` | summary list. Filters: `status`, `applied_position`, `min_experience`, `max_experience`, `q` |
| `GET`  | `/api/candidates/{id}` | `200` / `404` | full candidate |
| `PUT`  | `/api/candidates/{id}` | `200` / `400` / `404` | accepts full editable schema, overwrites |
| `DELETE` | `/api/candidates/{id}` | `200` / `400` / `404` | allowed unless `upload_status == "Processing"`, else `400` |
| `GET`  | `/api/candidates/{id}/resume-url` | `200` / `404` | `{ resume_url, filename }` |
| `GET`  | `/health` | `200` | open, no auth |

`candidate_id` is now a **7-digit running number** (`0000001`, `0000002`, ...) assigned in creation order - not a UUID.

`upload_status` (new, read-only, **separate from `status`**) tracks the file/extraction lifecycle:
`Not Uploaded` -> `Processing` -> `Done` (or `Failed`). Upload creates the row as `Processing`, then
flips it to `Done` once extraction returns. A candidate can be deleted in any state **except** `Processing`.
The HR pipeline `status` (`New`..`Archived`) is untouched by all of this.

Every response: `{ "data": ..., "error": null }` on success, `{ "data": null, "error": "message" }` on failure.
Errors: `400` bad file / validation / un-deletable status, `401` missing/bad token, `404` unknown id, `500` unexpected.

### `GET /api/candidates` query params

| Param | Effect |
|---|---|
| `status` | exact match on candidate `status` |
| `applied_position` | exact match on position name |
| `min_experience` | `experience_total >= value` |
| `max_experience` | `experience_total <= value` |
| `q` | case-insensitive substring over `full_name`, `email`, `candidate_id`, skill names + tools |

## Layout

```
backend/
  app/
    main.py           FastAPI app, CORS, /files mount, uniform error envelope
    config.py         env-driven settings (+ safe defaults, auth creds)
    auth.py           JWT create/verify + require_auth dependency
    database.py       SQLAlchemy engine / session
    models_db.py      Candidate ORM row (skills/experience/education = JSON columns)
    schemas.py        Pydantic models = THE CONTRACT (mirrors shared-contracts/schema.json)
    storage.py        LocalDiskStorage / AzureBlobStorage, picked from env at startup
    extraction.py     MOCK extract_candidate(bytes) -> dict
    seed.py           loads mock-candidates.json on first boot (7-digit running ids)
    routers/
      auth.py         POST /api/auth/login
      candidates.py   candidate CRUD + upload + filter/search
  tests/test_smoke.py
  Dockerfile
  requirements.txt
  .env.example
```
