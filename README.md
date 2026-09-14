# Inteltion HR Candidate Management — 7-Day MVP

A web-based system that uploads a CV, extracts structured candidate data via an LLM, and displays it on an HR dashboard with inline editing.

This README is the **single setup guide** for all 4 lanes. Follow it once on Day 1 and every member should be able to run the full stack locally.

---

## 0. Current Status (updated 14 Sep 2026)

| Lane | Branch | State |
|---|---|---|
| 🟥 Backend (Member 3) | `feature/backend` | API complete — auth, CRUD, batch upload, filter/search, Azure Blob ready. **Not yet tested** (`pytest` still needs a run) |
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

```
Inteltion_HR_Candidate_Management_Project/
├── frontend/
│   ├── dashboard/        # Member 1 — HR Dashboard (list + detail views)
│   ├── upload-edit/      # Member 2 — Upload flow + edit forms
│   └── components/       # Shared edit-input components (owned by Member 2, imported by Member 1)
├── backend/              # Member 3 — FastAPI app, DB, file handling
├── llm-service/          # Member 4 — CV extraction engine (LLM + parsing)
├── shared-contracts/     # Frozen JSON schema + API contract (touched by all 4, reviewed before edits)
├── docker-compose.yml
├── .env.example
└── README.md
```

**Folder discipline (Section 2.5 of the sprint plans):** work only inside your own folder. `shared-contracts/` is the one shared file set — changes go through a quick team heads-up, not a silent edit.

---

## 2. Prerequisites

Install these before Day 1 kickoff:

| Tool | Version | Purpose |
|---|---|---|
| [Git](https://git-scm.com/) | latest | Version control |
| [Node.js](https://nodejs.org/) | 20.x LTS | Frontend (React + Vite) |
| [Python](https://www.python.org/) | 3.11+ | Backend (FastAPI) + LLM service |
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | latest | Local Postgres + one-command full-stack run |
| A code editor | — | VS Code recommended (consistent extensions across the team: ESLint, Python, Docker) |

Verify installs:
```bash
git --version
node --version
python3 --version
docker --version
docker compose version
```

---

## 3. Clone the Repo

```bash
git clone https://github.com/Prandd/Inteltion_HR_Candidate_Management_Project.
cd Inteltion_HR_Candidate_Management_Project
```

---

## 4. Environment Variables & Secrets (Read This Before Anything Else)

Inteltion has provided the team with:
- **Azure OpenAI** access: `CV_SCORING_PROVIDER`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_DEPLOYMENT`, `AZURE_STORAGE_CONNECTION_STRING`
- An `azure-storage-connection-string.txt` file containing `DefaultEndpointsProtocol`, `EndpointSuffix`, `AccountName`, `AccountKey`

### 🔒 Critical rule: none of these values are ever committed to Git
`.gitignore` already excludes `.env` and any `*.txt` secrets file — double check this before your first commit:

```gitignore
.env
.env.*
!.env.example
azure-storage-connection-string.txt
```

### 4.1 Create your local `.env`
Copy the template and fill in the real values shared privately by the team lead (Slack DM or a password manager — **never** in a group chat or committed file):

```bash
cp .env.example .env
```

`.env.example` (already in the repo, safe to commit — placeholders only):

```env
# --- LLM / Azure OpenAI (Member 4, used inside llm-service) ---
CV_SCORING_PROVIDER=azure_openai
AZURE_OPENAI_ENDPOINT=https://<your-resource-name>.openai.azure.com/
AZURE_OPENAI_API_KEY=<paste-from-team-lead>
AZURE_OPENAI_DEPLOYMENT=<your-deployment-name>

# --- Azure Blob Storage (Member 3, used inside backend for file uploads) ---
AZURE_STORAGE_CONNECTION_STRING=<paste-full-connection-string-here>

# --- Backend ---
DATABASE_URL=postgresql://inteltion:inteltion@localhost:5432/inteltion_mvp
CORS_ORIGINS=http://localhost:5173,http://localhost:5174

# --- Frontend (Vite exposes only VITE_-prefixed vars) ---
VITE_API_BASE_URL=http://localhost:8000
VITE_USE_MOCK_DATA=true
```

### 4.2 Building the Azure Storage connection string
The `azure-storage-connection-string.txt` file Inteltion provided contains four separate fields. Combine them into a **single connection string** for `AZURE_STORAGE_CONNECTION_STRING` in this exact format:

```
DefaultEndpointsProtocol=<value>;AccountName=<value>;AccountKey=<value>;EndpointSuffix=<value>
```

Example (values are illustrative, not real):
```
DefaultEndpointsProtocol=https;AccountName=inteltionstorage;AccountKey=abc123...==;EndpointSuffix=core.windows.net
```

Paste the fully-assembled string as the value of `AZURE_STORAGE_CONNECTION_STRING` in your `.env`. Only Member 3 (backend) and Member 4 (if testing upload-to-blob directly) need this value locally — the two frontend lanes never touch Azure credentials at all.

### 4.3 Who needs which secret

| Variable | Needed by | Where it's used |
|---|---|---|
| `CV_SCORING_PROVIDER` | Member 4 | `llm-service/` — selects the LLM provider path |
| `AZURE_OPENAI_ENDPOINT` | Member 4 | `llm-service/` — API base URL |
| `AZURE_OPENAI_API_KEY` | Member 4 | `llm-service/` — auth |
| `AZURE_OPENAI_DEPLOYMENT` | Member 4 | `llm-service/` — model deployment name |
| `AZURE_STORAGE_CONNECTION_STRING` | Member 3 | `backend/` — stores uploaded CV files in Blob |
| `DATABASE_URL` | Member 3 | `backend/` — Postgres connection |
| `VITE_API_BASE_URL` / `VITE_USE_MOCK_DATA` | Members 1 & 2 | frontend `.env` — points at real API or mock data |

**Members 1 and 2 do not need any Azure secrets.** You build entirely against mock data this week — see Section 6.

---

## 5. Running the Full Stack (Docker Compose)

For anyone who wants the whole system running at once (recommended for the Day 6 integration session and the Day 7 demo):

```bash
docker compose up --build
```

**What actually runs today:**
- **Backend (FastAPI)** on `localhost:8000` — interactive API docs at `localhost:8000/docs`, seeded with the 9 mock candidates automatically

**No `.env` needed** — the backend ships working defaults (SQLite + local disk + `admin`/`password123`). The frontend services aren't in `docker-compose.yml` yet; run those with `npm run dev` per Section 6.

Postgres is pre-written but commented out in `docker-compose.yml` — uncomment it and repoint `DATABASE_URL` when the team decides to switch.

Stop everything:
```bash
docker compose down
```

Reset the database (wipes local data, safe during dev):
```bash
docker compose down -v
```

---

## 6. Per-Lane Local Setup (Work in Isolation, Day 2 Onward)

You don't need Docker running to build your own lane. Each member should be able to develop independently against mocks — that's the whole point of the sprint structure.

### 🟦 Member 1 — Dashboard Frontend
```bash
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

### 🟥 Member 3 — Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
- Runs on `http://localhost:8000` (interactive API docs at `/docs`).
- **No `.env` and no database setup needed** — defaults to SQLite at `backend/data/dev.db` and seeds itself from `shared-contracts/mock-candidates.json` on first boot. Copy `backend/.env.example` to `backend/.env` only to override something.
- `AZURE_STORAGE_CONNECTION_STRING` is optional — leave it unset and CV files go to local disk. Set it and the app switches to Azure Blob automatically, no code change.
- Tests: `pytest` from inside `backend/`.
- See [`backend/CHANGELOG.md`](backend/CHANGELOG.md) for the full API surface and what's done vs. pending.

### 🟨 Member 4 — LLM Extraction Service
```bash
cd llm-service
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run_test_harness.py      # runs your sample CVs through extraction and prints results
```
- No server to run this week — you're building an importable function (`extract_candidate()`), not a standalone service.
- Needs `CV_SCORING_PROVIDER`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_DEPLOYMENT` in your `.env` from Day 2 onward.
- Test against local sample CVs in `llm-service/sample_cvs/` — add a few real or synthetic files here on Day 1.

---

## 7. Shared Contracts

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

---

## 8. Quick Troubleshooting

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

---

## 9. Team Conventions

- **Branching:** `feature/<lane>-<short-description>` (e.g., `feature/dashboard-candidate-cards`).
- **Commits:** stay inside your own folder; if you need to touch `shared-contracts/`, say so in the team channel first.
- **Daily standup:** 15 minutes, written — what I shipped / what I'm doing / what contract I need from someone else.
- **Never commit:** `.env`, `azure-storage-connection-string.txt`, or any file containing a real API key or connection string.

---
*If you get stuck for more than 15 minutes on setup, post in the team channel immediately — a blocked Day 1 or Day 2 has no slack left to recover in a 7-day sprint.*
