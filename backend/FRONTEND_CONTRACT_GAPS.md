# Frontend ↔ Backend contract gaps (round 4/5)

> Written after pulling `frontend/dashboard` from `feature/frontend-update` and comparing it against
> `backend` on `feature/backend`. Build passes 100% on the frontend side (Vite 8 + React 19 + TS +
> Tailwind 4) — this is not a code-quality problem, it's that the two lanes settled on different
> contracts independently. Needs a team decision on which side moves, not a unilateral fix.

## 1. Login is not wired to the backend at all

`Login.tsx` has a literal comment: `// MVP authentication, Replace with backend auth later`. It sets
`localStorage.inteltion_auth = "true"` and never calls `/api/auth/login`. `src/api/axios.ts` never
attaches an `Authorization` header either. Every `/api/*` endpoint requires a Bearer token — as it
stands today, **every request from this frontend gets 401**.

## 2. Upload contract

| | Frontend (`UploadCandidate.tsx`) | Backend (`feature/backend`) |
|---|---|---|
| file field | `file` (singular, one request per file) | `files` (plural, batch) |
| duplicate signal | `response.data.duplicate` + a single `candidate` object | `needs_review[]`, each item a `pending_upload_id` + `duplicate_candidates[]` |
| resolve "same person" | re-POST the same upload endpoint with `?force=true&candidate_id=` | `POST /api/pending-uploads/{id}/update` |
| resolve "different person" | **no button for this** — `DuplicateCandidateModal` only offers Cancel / View / "Upload Anyway" (= force update) | `POST /api/pending-uploads/{id}/create-new` |

## 3. Comment endpoints

- Path: frontend calls `PUT`/`DELETE` at `/candidates/comments/{id}`; backend's canonical path is
  `/comments/{id}`. **Fixed as a compatibility alias** — both paths now work identically
  (`backend/app/routers/comments.py`), so this specific line item is closed regardless of how the
  rest of the gaps get resolved.
- `comment.id` is typed `number` on the frontend; the backend uses a UUID `string`.
- The frontend's "Add feedback as HR / Line Manager" dropdown sends `role`/`author` in the POST body.
  The backend deliberately ignores both (author comes from the JWT only — see the F3 rules in
  `comments.py`), so **the dropdown currently has no effect**; every comment is tagged by the
  logged-in account's actual role.

## 4. Status history

Frontend's `CandidateDetailType`/`CandidateSummary` expect `status_history` embedded on the candidate
itself, with fields `status` / `previous_status` / `action`. Backend exposes it as a separate endpoint,
`GET /api/candidates/{id}/status-history`, with fields `to_status` / `from_status` / `reason`. Also:
frontend expects `rejected_after`; backend's field is `before_rejected_status`.

## What's already fixed, needs no team decision

- **Comment path alias** (#3 above) — additive, non-breaking, done.

## Still open — needs the team to pick a direction

1. Upload contract (#2): which shape wins, or do both sides move toward a third shape?
2. Status history / rejection naming (#4): embed vs. separate endpoint, and field names.
3. Login integration (#1): frontend work, not blocked on backend — the backend's `POST /api/auth/login`
   already returns `{access_token, account}` and is unchanged by anything in this doc.
4. Comment `id` type and the role dropdown (#3): decide whether the dropdown becomes read-only
   (showing the caller's real role) or the backend adds a way to write comments as a different role
   (weakens the F3 attribution guarantee — would need its own discussion).
