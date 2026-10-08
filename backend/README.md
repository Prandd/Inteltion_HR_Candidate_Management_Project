# backend/ - Inteltion HR Candidate API (MVP, Member 3)

> 📋 **Teammates:** see [`CHANGELOG.md`](CHANGELOG.md) (ภาษาไทย) for what's been built, what
> changed in the API contract, curl examples, and what each lane needs to update. See
> [`FRONTEND_CONTRACT_GAPS.md`](FRONTEND_CONTRACT_GAPS.md) for known mismatches against
> `feature/frontend-update` that still need a team decision.
>
> ✅ **Tested** — 127/127 `pytest` cases pass on Python 3.11.9 (Windows), plus a live `uvicorn`
> boot against a **real Azure Blob Storage account** (upload, SAS link, private-container check),
> and an Alembic run of all five migrations against a database built to the round-3 schema —
> covering the new tables and columns, the `CV rejected` → `Rejected` rename, the
> `email_normalized` backfill, the duplicate-email cleanup plus UNIQUE index, the round-5
> candidate-ownership backfill, and `downgrade base`.
>
> Still unverified: the Docker image build (no Docker on the author's machine).

FastAPI + SQLite + local disk. **Everything external is mocked** for this sprint:

| External thing | This week | Real deploy |
|---|---|---|
| LLM CV extraction (Member 4) | `app/extraction.py` returns schema-valid fake data, seeded from the file's content hash | change one import in `app/routers/candidates.py` |
| File storage | `app/storage.py` `LocalDiskStorage` writes to `data/uploads/`, served at `/files/...` (default, zero setup) | **implemented** - set `AZURE_STORAGE_CONNECTION_STRING` and the app switches to `AzureBlobStorage` automatically, same interface, no code change |
| Database (Postgres) | SQLite file at `data/dev.db` | point `DATABASE_URL` at Postgres (compose service is pre-written, commented) |

## File storage: local disk vs Azure Blob

Picked automatically at startup, purely from env vars (`app/storage.py::build_storage()`):

- **`AZURE_STORAGE_CONNECTION_STRING` unset (default)** -> `LocalDiskStorage`. Files land in
  `UPLOAD_DIR`, served back at `/files/<candidate_id>/v<n>/<filename>`. Nothing to configure.
- **`AZURE_STORAGE_CONNECTION_STRING` set** -> `AzureBlobStorage`. Uploads go to the container
  named by `AZURE_STORAGE_CONTAINER_NAME` (default `resumes`), created automatically if missing.
  The container is **not** made public - resumes are personal data. `GET /api/candidates/{id}/resume-url`
  returns a fresh, read-only **SAS link** valid for `RESUME_SAS_EXPIRY_MINUTES` (default 60);
  re-call it rather than caching the `resume_url` on the candidate record indefinitely.

### Which account am I writing to?

Uploading CVs into the wrong Azure subscription is the failure this section exists to prevent.

- Set **`AZURE_STORAGE_ACCOUNT_NAME`** to the account you expect. If the connection string names a
  different one, the app **refuses to start** rather than writing personal data somewhere unintended.
- **`ALLOW_COMPANY_STORAGE`** defaults to `false`. Inteltion's own account stays unusable until
  somebody opts in explicitly.
- Startup logs the active backend loudly: `STORAGE: AzureBlob account=… container=…` or
  `STORAGE: LocalDisk path=…`. A silent fall back to local disk now logs at `WARNING`.
- **`GET /health`** reports the live backend, account and container (names only, never the key),
  so anyone can confirm what they are hitting without reading someone's `.env`.

No credential is ever hardcoded - only `.env` (git-ignored) or the server's real environment.
`scripts/migrate_blobs.py` copies blobs between accounts and fixes the DB paths (`--dry-run` first).

## Run it - Docker (what you hand to teammates)

From the repo root (where `docker-compose.yml` lives):

```bash
docker compose up --build
```

- API: http://localhost:8000  Swagger UI: http://localhost:8000/docs
- Seeded with the 9 mock candidates from `shared-contracts/mock-candidates.json` plus one admin account
- No `.env`, no Python install needed. `docker compose down -v` to reset.

## Run it - local Python (faster iteration)

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows.  macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Database migrations

Round 4 added five tables, three columns on `candidates`, and renamed the status `CV rejected`
to `Rejected` (contract v2.1.0). Round 5 added two more tables (`ownership_history`,
`sql_test_scores`) and one more column (`candidates.owner_account_id`), and backfills that
column for every pre-existing candidate from its earliest `status_history` row. New **tables**
appear by themselves (`create_all` at startup); new **columns, the status rename, and the
ownership backfill do not**.

| Your situation | Command |
|---|---|
| You have a `dev.db` from round 3 with data worth keeping | `alembic upgrade head` |
| You deleted `dev.db` and restarted, so `create_all` already built every table | `alembic stamp head` — records the revision without re-running it. **Do not** use `upgrade`; it will fail because the tables already exist |
| You do not care about the dev data | delete `backend/data/dev.db` and restart - it re-seeds |

A row still holding `CV rejected` makes the app **refuse to start**, with an error naming the row
and pointing at this migration. That is the startup enum assertion doing its job - the alternative
is a Kanban column that silently renders empty.

SQLite remains the default. Postgres is a `DATABASE_URL` swap away (compose service is commented in).

## Tests

```bash
cd backend
pytest
```

| File | Covers |
|---|---|
| `tests/test_smoke.py` | the round-1..3 regression suite: auth guard, list/filter/search, running ids, multi-file upload, conditional delete |
| `tests/test_auth_accounts.py` | DB-backed login, `/me`, role gating, deactivation taking effect mid-token, username enumeration, rate limiting |
| `tests/test_comments.py` | ownership on edit/delete, forged `author_account_id` in the body, `created_at` immutability, soft delete, the deprecated computed fields |
| `tests/test_reupload.py` | update-not-duplicate, preserved HR fields, surviving comments, CV versioning, change log, two files/one email, failed extraction leaving the record untouched |
| `tests/test_pending_uploads.py` | the create-or-update decision: soft matches stop instead of guessing, both resolutions, the newest-match auto-pick, discard dropping the stored bytes, double-resolve and deleted-match races |
| `tests/test_status.py` | backend enum == contract enum, `before_rejected_status` surviving an unrelated PUT, restore, status history |
| `tests/test_storage_guardrail.py` | the account mismatch guard and versioned blob paths (no Azure account needed) |
| `tests/test_ownership.py` | owner set to the original uploader, the `?owner_account_id=` filter, transfer by owner/admin, rejecting bystanders and self-granting targets, ownership history, owner surviving re-upload and both pending-upload resolutions |
| `tests/test_sql_test_scores.py` | add/list, `raw_payload` preserved verbatim, multiple scores per candidate, auth required, non-finite score rejected with `400` (not `500`), unknown candidate `404` |

## Auth

HR accounts live in the `hr_accounts` table. The first admin is seeded from `SEED_ADMIN_*` in `.env`,
and **only while that table is empty** - it is a way in on a fresh database, not a login path.

```bash
curl -s -X POST localhost:8000/api/auth/login \
  -H 'content-type: application/json' \
  -d '{"username":"admin","password":"password123"}'
# -> { "data": { "access_token": "<jwt>", "token_type": "bearer",
#                "account": { "account_id": "...", "role": "admin", ... } }, "error": null }
```

Send `Authorization: Bearer <jwt>` on every `/api/*` call except `/health`. Missing/expired -> `401`.

- Passwords are bcrypt-hashed. The hash is never stored in a response model, logged, or returned.
- `get_current_account()` loads the account from the DB on every request, so **deactivating somebody
  takes effect on their next call**, not when their 8-hour token expires.
- Login is rate limited (5 failures per username per 15 minutes -> `429` + `Retry-After`), and
  "no such user", "wrong password" and "deactivated" return an identical message.

## API surface (see `shared-contracts/`)

| Method | Path | Success | Notes |
|---|---|---|---|
| `POST` | `/api/auth/login` | `200` / `401` / `429` | `{username, password}` -> `{access_token, token_type, account}` |
| `GET` | `/api/auth/me` | `200` / `401` | the caller's account |
| `POST` | `/api/auth/change-password` | `200` / `400` | `{old_password, new_password}` |
| `GET` `POST` | `/api/hr-accounts` | `200` / `201` / `403` | admin only. `?is_active=` filter |
| `PUT` `DELETE` | `/api/hr-accounts/{id}` | `200` / `403` / `404` | admin only. DELETE is a **soft** delete |
| `POST` | `/api/hr-accounts/{id}/reset-password` | `200` / `403` | admin-set temporary password |
| `POST` | `/api/candidates/upload` | `201` / `400` | multipart **`files`** (repeatable, .pdf/.docx) -> `{created[], updated[], needs_review[], failed[], count}` |
| `GET`  | `/api/candidates` | `200` | summary list. Filters: `status`, `applied_position`, `min_experience`, `max_experience`, `q` |
| `GET`  | `/api/candidates/{id}` | `200` / `404` | full candidate |
| `PUT`  | `/api/candidates/{id}` | `200` / `400` / `404` | accepts the editable schema, overwrites |
| `DELETE` | `/api/candidates/{id}` | `200` / `400` / `404` | allowed unless `upload_status == "Processing"` |
| `GET`  | `/api/candidates/{id}/resume-url` | `200` / `404` | `{resume_url, filename, version_no}`. `?version=` for an older CV |
| `GET`  | `/api/candidates/{id}/resume-versions` | `200` / `404` | every CV ever uploaded, newest first |
| `GET` `POST` | `/api/candidates/{id}/comments` | `200` / `201` / `404` | `?comment_type=` filter |
| `PUT` `DELETE` | `/api/comments/{comment_id}` | `200` / `403` / `404` | author only (admin may also delete) |
| `PUT` `DELETE` | `/api/candidates/comments/{comment_id}` | `200` / `403` / `404` | alias of the row above, for `feature/frontend-update`'s path |
| `POST` | `/api/candidates/{id}/restore` | `200` / `400` | undo a rejection |
| `GET`  | `/api/candidates/{id}/status-history` | `200` / `404` | every status transition, attributed |
| `GET`  | `/api/candidates/{id}/changes` | `200` / `404` | field-level diff, `source=reupload\|manual_edit` |
| `POST` | `/api/candidates/{id}/transfer-ownership` | `200` / `400` / `403` / `404` | current owner or admin only; `{new_owner_account_id, reason?}` |
| `GET`  | `/api/candidates/{id}/ownership-history` | `200` / `404` | every ownership assignment/transfer, newest first |
| `POST` | `/api/candidates/{id}/sql-test-score` | `201` / `400` / `404` | `{score, source?, raw_payload?}`; `score` must be finite |
| `GET`  | `/api/candidates/{id}/sql-test-scores` | `200` / `404` | every score for the candidate, newest first |
| `GET`  | `/api/pending-uploads` | `200` | CVs waiting on a create-or-update decision, oldest first |
| `POST` | `/api/pending-uploads/{id}/update` | `200` / `404` / `409` | merge into the existing candidate (newest match wins) |
| `POST` | `/api/pending-uploads/{id}/create-new` | `201` / `404` / `409` | create a separate candidate instead |
| `DELETE` | `/api/pending-uploads/{id}` | `200` / `404` / `409` | discard the file; keeps the decision, drops the bytes |
| `GET`  | `/health` | `200` | open, no auth. Reports the storage backend and the status enum |

Every response: `{ "data": ..., "error": null }` on success, `{ "data": null, "error": "message" }` on failure.
Errors: `400` validation, `401` token, `403` not the owner / wrong role, `404` unknown id,
`409` duplicate username or email, `429` login rate limit, `500` unexpected.

### Re-uploading a CV (round 4)

A file whose extracted email (lowercased, trimmed) matches an existing candidate **updates that
record** instead of creating a second one.

| Field group | On re-upload |
|---|---|
| `full_name` `email` `phone` `summary` `skills` `experience` `experience_total` `education` `current_salary` `expected_salary` `extraction_confidence` `raw_text_snippet` | **overwritten** from the new CV |
| `resume_url` `resume_filename` `upload_status` | **overwritten** (the old file is kept as a version) |
| `status` `before_rejected_status` `applied_position` `location` | **preserved** - never touched by an upload |
| `candidate_id` `created_at` | **preserved** |
| comments | **untouched by design** - they live in `comment_logs`, keyed on the preserved `candidate_id` |

Guard: a field the new CV extracted as empty does **not** wipe a value the old one had.

### Deciding whether two CVs are the same person

The match key is the normalized email, and there are three outcomes - not two:

| What the upload found | What happens |
|---|---|
| **Exact** normalized-email match | auto-update, as described above |
| No match at all | auto-create a new candidate |
| No email match, but same phone **or** same `full_name` + `applied_position` | **stops** - the file goes to `needs_review[]` and waits for a human |

Fuzzy matching never auto-merges and never auto-creates, because both mistakes are bad and only
one of them is reversible: a wrong merge overwrites a real person's record with no undo, a wrong
create leaves a duplicate. The third outcome exists so the backend never has to guess between them.

Resolving a pending item applies the *same* merge policy as a normal re-upload - it is not a way
around the table above. `update` does not take a candidate id: when several candidates matched, the
server picks the one with the newest `updated_at`, which is the record HR is actually working on.

`email_normalized` carries a UNIQUE constraint (migration 0003), with `NULL` - not `""` - for a CV
with no email, so any number of email-less candidates coexist while a real collision returns `409`.

### `GET /api/candidates` query params

| Param | Effect |
|---|---|
| `status` | exact match on candidate `status` |
| `applied_position` | exact match on position name |
| `min_experience` | `experience_total >= value` |
| `max_experience` | `experience_total <= value` |
| `q` | case-insensitive substring over `full_name`, `email`, `candidate_id`, skill names + tools |
| `owner_account_id` | exact match on `owner_account_id` — for a "my candidates" view |

### Candidate ownership (round 5)

Rule: whoever imports a CV owns it. `owner_account_id` is set exactly once, at creation, to the
account that uploaded the file — including the "create new" resolution of a pending upload, which
always attributes ownership to the **original uploader**, not whoever clicks the button later.
Re-uploading a CV, and resolving a pending upload as "update", never touch it.

The only way to change it is `POST /api/candidates/{id}/transfer-ownership`, and only two callers
may do so: the candidate's **current owner**, or any **admin**. Everyone else gets `403` -
including the account being made the new owner (a transfer is always done *to* an account, never
something an account grants itself). Every assignment and transfer is logged in
`ownership_history` (the very first row, at creation, has `from_owner_account_id = null`); see
`GET /api/candidates/{id}/ownership-history`.

Pre-round-5 candidates got a one-time backfill (migration `0005`) from each candidate's earliest
`status_history` row, falling back to the earliest active admin if none exists.

### SQL-test scores (round 5)

`sql_test_scores` holds scores reported by a separate external "SQL test" tool whose own request
contract isn't finalized yet. `score` is the one field that's certain (must be a finite number -
`Infinity`/`-Infinity`/`NaN` get `400`); `raw_payload` preserves anything else a caller sends,
verbatim, so nothing is lost once the real shape is known. A candidate can be scored more than
once - every submission is its own row, nothing is overwritten. See
`shared-contracts/sql-test-score-schema.json`.

## Layout

```
backend/
  app/
    main.py           FastAPI app, CORS, /files mount, error envelope, /health, startup status assertion
    config.py         env-driven settings (+ safe defaults)
    statuses.py       THE status enum - loaded from shared-contracts/schema.json
    auth.py           JWT + get_current_account() + require_role()
    security.py       bcrypt hashing + login rate limiter
    database.py       SQLAlchemy engine / session
    models_db.py      Candidate + hr_accounts, comment_logs, resume_versions,
                      status_history, candidate_change_log, pending_uploads,
                      ownership_history, sql_test_scores
    schemas.py        Pydantic models = THE CONTRACT (mirrors shared-contracts/schema.json)
    services.py       merge policy, status transitions, change log, duplicate
                      matching, ownership, sql-test scores - domain logic, no HTTP
    storage.py        LocalDiskStorage / AzureBlobStorage + the account guardrail
    extraction.py     MOCK extract_candidate(bytes) -> dict, seeded from the content hash
    seed.py           first admin + mock candidates + legacy comment backfill + owner backfill
    routers/
      auth.py             login / me / change-password
      hr_accounts.py      account management (admin)
      candidates.py       candidate CRUD + upload + versions + history + changes +
                           transfer-ownership + ownership-history + sql-test-score(s)
      comments.py         comment_logs CRUD + the `/candidates/comments/{id}` path alias
      pending_uploads.py  the create-or-update decision queue
  alembic/            migrations 0001 (new tables) .. 0005 (ownership + sql_test_scores)
  scripts/
    migrate_blobs.py        copy blobs between Azure accounts, fix DB paths
    gen_frontend_types.py   regenerate shared-contracts/status.ts
  tests/
  FRONTEND_CONTRACT_GAPS.md  known mismatches vs feature/frontend-update, pending a team decision
  Dockerfile
  requirements.txt
  .env.example
```

## Candidate ownership

The original CV uploader owns a newly created candidate. Re-uploading or merging
into an existing candidate keeps its current owner. A pending upload resolved as
create-new retains the original uploader and original import timestamp.

Only the current owner can call `POST /api/candidates/{id}/transfer-ownership`
with `{ "new_owner_account_id": "...", "reason": "optional" }`. Admin accounts
also follow this rule. The recipient must be active and different from the owner.
Owner changes and audit entries are committed together; concurrent transfers
cannot overwrite a completed transfer by the previous owner.

`GET /api/candidates/{id}/ownership-options` lets the current owner select another
active user and returns only account ID, display name, and username. Account
administration stays admin-only. Ownership history includes the original import
and every transfer, with actor, timestamp, optional reason, and owner names.
Status history also includes the actor's display name.

The candidate detail page displays the current owner and transfer form for that
owner. Its existing Status History & Audit Trail combines ownership and status
events, newest first, using the viewer's local time. Existing records without
ownership history do not receive invented import events.

### Replace a duplicate CV

Choosing **Replace & restart** in duplicate review updates the existing candidate's
CV details and stores a new resume version, then resets status to **New** for a new
application attempt. The status transition is recorded with the acting user and
reason `Application restarted by replacing CV`. Rejection state is cleared;
existing owner, position, HR notes, and audit history remain on the same record.
Creating a new candidate still creates a separate record.
