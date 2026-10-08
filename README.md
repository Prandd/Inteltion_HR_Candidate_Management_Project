# Inteltion HR Candidate Management --- 7-Day MVP

A web-based system that uploads a CV, extracts structured candidate data
via an LLM, and displays it on an HR dashboard with inline editing and
candidate pipeline management.

This README is the single setup guide for all team members. Follow it to
run the full stack locally and understand the current system workflow.

------------------------------------------------------------------------

## 0. Current Status (updated 14 Sep 2026)

| Lane | Branch | State |
|---|---|---|
| 🟥 Backend (Member 3) | `feature/backend` | API complete and **tested** — 15/15 `pytest` + a full live run (auth, CRUD, batch upload, filter/search, Azure Blob ready) |
| 🟦 Dashboard (Member 1) | `feature/dashboard-frontend` | in progress |
| 🟨 LLM extraction (Member 4) | `feature/llm-service-cv-parsing` | in progress |
| 🟩 Upload/Edit (Member 2) | — | not started |

### ⚠️ Backend API changed — Members 1 & 2 must update their fetch code

1. Every `/api/candidates/*` request now needs `Authorization: Bearer <jwt>` (get one from `POST /api/auth/login`, `admin` / `password123`)
2. `candidate_id` is now a 7-digit string (`"0000001"`), not a UUID
3. New read-only field `upload_status` on every candidate
4. `POST /api/candidates/upload` takes `files` (a repeatable list), and returns `{created[], failed[], count}`

`shared-contracts/` is already updated to match — **re-pull it**.

👉 **Full details, curl examples, and per-person to-do: [`backend/CHANGELOG.md`](backend/CHANGELOG.md)** (ภาษาไทย)

---

## 1. Project Structure

    Inteltion_HR_Candidate_Management_Project/

    ├── frontend/
    │   ├── dashboard/        # HR Dashboard, login, candidate list/detail views
    │   ├── upload-edit/      # Upload flow + edit forms
    │   └── components/       # Shared frontend components
    │
    ├── backend/              # FastAPI app, DB, file handling, candidate APIs
    ├── llm-service/          # CV extraction engine (LLM + parsing)
    ├── shared-contracts/     # Shared schema and API contracts
    ├── docker-compose.yml
    ├── .env.example
    └── README.md

------------------------------------------------------------------------

# 2. Authentication

The system requires authentication before accessing the HR dashboard.

## Current Implementation

-   Frontend MVP authentication
-   Login page
-   Logout through user profile dropdown
-   Authentication state stored using localStorage

Flow:

    Login
      |
      v
    Authentication Check
      |
      v
    Dashboard

Logout:

    Profile Dropdown
            |
            v
    Remove Authentication State
            |
            v
    Redirect to Login

------------------------------------------------------------------------

Inteltion has provided the team with:
- **Azure OpenAI** access: `CV_SCORING_PROVIDER`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_DEPLOYMENT`, `AZURE_STORAGE_CONNECTION_STRING`
- An `azure-storage-connection-string.txt` file containing `DefaultEndpointsProtocol`, `EndpointSuffix`, `AccountName`, `AccountKey`

## Candidate Search

Users can search candidates by:

-   Candidate name
-   Email
-   Skills

## Candidate Filtering

Available filters:

-   Minimum experience years
-   Position

# --- Azure Blob Storage (Member 3, used inside backend for file uploads) ---
AZURE_STORAGE_CONNECTION_STRING=<paste-full-connection-string-here>

Candidates can be sorted by:

-   Latest Import
-   Oldest Import
-   Name A-Z
-   Name Z-A

### 4.2 Building the Azure Storage connection string
The `azure-storage-connection-string.txt` file Inteltion provided contains four separate fields. Combine them into a **single connection string** for `AZURE_STORAGE_CONNECTION_STRING` in this exact format:

    Candidates
        |
        v
    Search / Filter
        |
        v
    Sorting
        |
        v
    Dashboard Board / Table

------------------------------------------------------------------------

Paste the fully-assembled string as the value of `AZURE_STORAGE_CONNECTION_STRING` in your `.env`. Only Member 3 (backend) and Member 4 (if testing upload-to-blob directly) need this value locally — the two frontend lanes never touch Azure credentials at all.

The CV upload process consists of multiple stages:

| Variable | Needed by | Where it's used |
|---|---|---|
| `CV_SCORING_PROVIDER` | Member 4 | `llm-service/` — selects the LLM provider path |
| `AZURE_OPENAI_ENDPOINT` | Member 4 | `llm-service/` — API base URL |
| `AZURE_OPENAI_API_KEY` | Member 4 | `llm-service/` — auth |
| `AZURE_OPENAI_DEPLOYMENT` | Member 4 | `llm-service/` — model deployment name |
| `AZURE_STORAGE_CONNECTION_STRING` | Member 3 | `backend/` — stores uploaded CV files in Blob |
| `DATABASE_URL` | Member 3 | `backend/` — Postgres connection |
| `VITE_API_BASE_URL` / `VITE_USE_MOCK_DATA` | Members 1 & 2 | frontend `.env` — points at real API or mock data |

        |
        v

    Uploading resume

        |
        v

    Extracting CV information

        |
        v

    AI analyzing candidate profile

        |
        v

    Saving candidate profile

        |
        v

    Completed

The progress bar represents the complete CV processing pipeline, not
only file transfer progress.

------------------------------------------------------------------------

# 5. Candidate Detail Management

Candidate detail page supports:

-   View extracted candidate information
-   View skills and experience
-   Update candidate status
-   Download resume
-   Delete candidate

------------------------------------------------------------------------

# 6. AI Extraction Confidence

The candidate score shown in the system represents:

    extraction_confidence

Meaning:

-   Confidence level of LLM CV information extraction

Example:

    0.85 = 85% extraction confidence

Important:

This value is NOT a candidate-job matching score.

It does not represent candidate suitability for a position.

------------------------------------------------------------------------

# 7. Candidate Delete API

## Delete Candidate

Method:

    DELETE /candidates/{candidate_id}

Purpose:

Remove a candidate record from the system.

------------------------------------------------------------------------

# 8. Running the Full Stack

## Docker Compose

Start all services:

``` bash
docker compose up --build
```

**What actually runs today:**
- **Backend (FastAPI)** on `localhost:8000` — interactive API docs at `localhost:8000/docs`, seeded with the 9 mock candidates automatically

**No `.env` needed** — the backend ships working defaults (SQLite + local disk + `admin`/`password123`). The frontend services aren't in `docker-compose.yml` yet; run those with `npm run dev` per Section 6.

Postgres is pre-written but commented out in `docker-compose.yml` — uncomment it and repoint `DATABASE_URL` when the team decides to switch.

Stop:

``` bash
docker compose down
```

Reset database:

``` bash
docker compose down -v
```

------------------------------------------------------------------------

# 9. Local Development

## Dashboard Frontend

``` bash
cd frontend/dashboard

npm install

npm run dev
```
- Runs on `http://localhost:5173`.
- Set `VITE_USE_MOCK_DATA=true` in `frontend/dashboard/.env` to build against the static fake-candidate JSON (`shared-contracts/mock-candidates.json`) instead of a live backend.
- No Azure secrets needed.
- **Hitting the real API?** Log in first (`POST /api/auth/login`) and send `Authorization: Bearer <jwt>` on every `/api/candidates/*` call. Server-side filtering and search are available — see [`backend/CHANGELOG.md`](backend/CHANGELOG.md).

### 🟩 Member 2 — Upload/Edit Frontend
```bash
cd frontend/upload-edit
npm install
npm run dev
```
- Runs on `http://localhost:5174`.
- Same mock-data flag as Member 1 — build your upload flow and edit components against `shared-contracts/mock-candidates.json` and a mocked upload response.
- No Azure secrets needed.
- **Upload contract changed:** the multipart field is `files` (repeatable — multi-file upload is supported) and the response is `{created[], failed[], count}`. Render `failed[]` so the user sees which files were rejected. Details in [`backend/CHANGELOG.md`](backend/CHANGELOG.md).

    http://localhost:5173

## Backend

``` bash
cd backend

python3 -m venv venv

source venv/bin/activate

pip install -r requirements.txt

uvicorn app.main:app --reload --port 8000
```
- Runs on `http://localhost:8000` (interactive API docs at `/docs`).
- **No `.env` and no database setup needed** — defaults to SQLite at `backend/data/dev.db` and seeds itself from `shared-contracts/mock-candidates.json` on first boot. Copy `backend/.env.example` to `backend/.env` only to override something.
- `AZURE_STORAGE_CONNECTION_STRING` is optional — leave it unset and CV files go to local disk. Set it and the app switches to Azure Blob automatically, no code change.
- Tests: `pytest` from inside `backend/`.
- See [`backend/CHANGELOG.md`](backend/CHANGELOG.md) for the full API surface and what's done vs. pending.

Backend:

    http://localhost:8000

API Docs:

    http://localhost:8000/docs

## LLM Service

``` bash
cd llm-service

python3 -m venv venv

source venv/bin/activate

pip install -r requirements.txt

python run_test_harness.py
```

------------------------------------------------------------------------

# 10. Environment Variables

`shared-contracts/` holds the two files every lane depends on:
- `schema.json` — the candidate JSON schema (mirrored as Pydantic models in `backend/app/schemas.py`, and to be mirrored as a TypeScript type in `frontend/components/types.ts`)
- `mock-candidates.json` — 9 static fake candidates matching the schema, for both frontend lanes to build against

**Any change requires a same-day message to all 4 members before editing** — a silent change here breaks 3 other people's work simultaneously.

**Revision history:**

| When | What changed | Why |
|---|---|---|
| Day 1 | Initial freeze | — |
| 10 Sep 2026 | `candidate_id` UUID → 7-digit running number (`"0000001"`); added `upload_status` (`Not Uploaded`/`Processing`/`Done`/`Failed`) | task-extension spec — see [`backend/CHANGELOG.md`](backend/CHANGELOG.md) |

Note `status` (HR pipeline: `New`…`Archived`) and `upload_status` (file lifecycle) are **two separate fields** — don't mix them up.

Azure Storage:

    AZURE_STORAGE_CONNECTION_STRING_FILE

| Problem | Likely Fix |
|---|---|
| Frontend can't reach backend (CORS error) | Confirm `CORS_ORIGINS` in backend `.env` includes your frontend's port (`5173`/`5174`) |
| API returns `401` on every call | Missing/expired token — `POST /api/auth/login` and send `Authorization: Bearer <jwt>` (tokens last 8h) |
| Candidate not found / IDs look wrong | `candidate_id` is now `"0000001"`, not a UUID. It's a **string** — don't `parseInt` it, the leading zeros matter |
| `docker compose up --build` fails during `pip install` | Seen on an unstable Docker Desktop/WSL2 VM (random segfaults). `wsl --shutdown`, restart Docker Desktop, raise its memory to ≥ 4 GB, retry |
| Stale data after pulling the new backend | The old `dev.db` still has UUID ids — `docker compose down -v`, or delete `backend/data/` |
| Azure OpenAI 401/403 error | Double-check `AZURE_OPENAI_API_KEY` and `AZURE_OPENAI_ENDPOINT` — no trailing slash mismatches, no quotes around values in `.env` |
| Azure Blob upload fails | Re-verify the assembled connection string format in Section 4.2 — a missing `;` between fields is the most common mistake |
| `npm install` fails | Confirm Node 20.x with `node --version`; delete `node_modules` + `package-lock.json` and retry |
| Backend can't find `AZURE_STORAGE_CONNECTION_STRING` | Confirm `.env` exists in `backend/` (or the repo root, depending on your `docker-compose.yml` setup) and isn't named `.env.example` |

    DATABASE_URL
    CORS_ORIGINS

Frontend:

    VITE_API_BASE_URL
    VITE_USE_MOCK_DATA

Never commit:

    .env
    *.env
    azure-storage-connection-string.txt
    API keys
    connection strings

------------------------------------------------------------------------

# 11. Shared Contracts

The shared contract contains:

-   Candidate schema
-   API contract
-   Mock candidate data

Any changes to shared contracts must be communicated to all team members
before editing.

------------------------------------------------------------------------

# 12. Development Notes

Current dashboard data flow:

    Candidate API

          |

          v

    Search / Filter

          |

          v

    Sorting

          |

          v

    Board / Table Display

When modifying candidate schema, API responses, or shared contracts,
notify other team members to avoid integration issues.

------------------------------------------------------------------------

# 13. Troubleshooting

## Frontend cannot reach backend

Check:

-   Backend running
-   CORS_ORIGINS configuration
-   VITE_API_BASE_URL

## Azure OpenAI Error

Check:

-   AZURE_OPENAI_ENDPOINT
-   AZURE_OPENAI_API_KEY
-   AZURE_OPENAI_DEPLOYMENT

## Upload Error

Check:

-   Azure Storage connection string
-   Backend environment variables

------------------------------------------------------------------------

# 14. Team Conventions

-   Use feature branches:

```{=html}
<!-- -->
```
    feature/<lane>-<description>

-   Do not commit secrets.
-   Changes to shared-contracts require team notification.
-   Keep commits focused on your assigned module.
