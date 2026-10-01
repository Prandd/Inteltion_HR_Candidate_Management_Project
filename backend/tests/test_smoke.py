"""The round-1..3 regression suite, kept green through round 4.

Round-4 changes visible here:
  * login is DB-backed, so the credentials come from the seeded admin account;
  * the upload response gained `updated[]`;
  * resume URLs resolve through resume_versions.
"""
import io

from conftest import ADMIN_USERNAME, pdf_bytes, upload

from app.database import SessionLocal
from app.models_db import Candidate


# ---------------- auth ----------------


def test_health_is_open(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "ok"


def test_health_reports_the_active_storage_backend(client):
    """F1 - the team confirms which account they are hitting without reading
    anyone's .env. Never the key."""
    storage = client.get("/health").json()["data"]["storage"]
    assert storage["backend"] in {"local_disk", "azure_blob"}
    assert "key" not in str(storage).lower()


def test_candidates_requires_auth(client):
    r = client.get("/api/candidates")
    assert r.status_code == 401
    assert r.json()["data"] is None
    assert r.json()["error"]


def test_login_rejects_bad_credentials(client):
    r = client.post(
        "/api/auth/login", json={"username": ADMIN_USERNAME, "password": "nope"}
    )
    assert r.status_code == 401


# ---------------- list / filter / search ----------------


def test_list_is_enveloped_list(client, auth):
    r = client.get("/api/candidates", headers=auth)
    assert r.status_code == 200
    body = r.json()
    assert body["error"] is None
    assert isinstance(body["data"], list)
    assert body["data"], "seed data should be present"


def test_filter_by_status(client, auth):
    r = client.get("/api/candidates", headers=auth, params={"status": "Hired"})
    assert r.status_code == 200
    rows = r.json()["data"]
    assert rows and all(row["status"] == "Hired" for row in rows)


def test_filter_by_experience_range(client, auth):
    r = client.get(
        "/api/candidates", headers=auth,
        params={"min_experience": 6, "max_experience": 8},
    )
    assert r.status_code == 200
    assert all(6 <= row["experience_total"] <= 8 for row in r.json()["data"])


def test_keyword_search_matches_skill_and_id(client, auth):
    by_skill = client.get("/api/candidates", headers=auth, params={"q": "airflow"})
    assert by_skill.status_code == 200
    assert by_skill.json()["data"], "expected a candidate with an Airflow tool"

    by_id = client.get("/api/candidates", headers=auth, params={"q": "0000001"})
    assert [r["candidate_id"] for r in by_id.json()["data"]] == ["0000001"]


# ---------------- upload (multi-file + running id) ----------------


def test_get_unknown_returns_404_envelope(client, auth):
    r = client.get("/api/candidates/9999999", headers=auth)
    assert r.status_code == 404
    assert r.json()["data"] is None


def test_resume_url_resolves_after_upload(client, auth, fixed_extraction):
    fixed_extraction("resume-url-case", email="resume.url@smoke.test")
    up = upload(client, auth, ("cv.pdf", "resume-url-case"))
    cid = up.json()["data"]["created"][0]["candidate_id"]

    r = client.get(f"/api/candidates/{cid}/resume-url", headers=auth)
    assert r.status_code == 200
    body = r.json()["data"]
    assert body["filename"] == "cv.pdf"
    assert body["resume_url"]  # local disk -> http://.../files/<id>/v1/cv.pdf
    assert body["version_no"] == 1


def test_upload_rejects_non_pdf_docx(client, auth):
    r = client.post(
        "/api/candidates/upload",
        headers=auth,
        files={"files": ("resume.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert r.status_code == 400


def test_multi_upload_creates_running_ids(client, auth, fixed_extraction):
    # Two distinct people - pinned, so the assertion is about id assignment and
    # not about whether the mock happened to invent two different emails.
    fixed_extraction("multi-a", email="multi.a@smoke.test", full_name="Multi A")
    fixed_extraction("multi-b", email="multi.b@smoke.test", full_name="Multi B")
    r = client.post(
        "/api/candidates/upload",
        headers=auth,
        files=[
            ("files", ("a.pdf", io.BytesIO(pdf_bytes("multi-a")), "application/pdf")),
            ("files", ("b.docx", io.BytesIO(pdf_bytes("multi-b")),
                       "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
        ],
    )
    assert r.status_code == 201, r.text
    data = r.json()["data"]
    assert data["count"] == 2
    assert data["updated"] == [], "two different CVs are two different people"
    created = data["created"]
    ids = [c["candidate_id"] for c in created]
    assert all(len(cid) == 7 and cid.isdigit() for cid in ids)
    assert int(ids[1]) == int(ids[0]) + 1
    assert all(c["upload_status"] == "Done" for c in created)


def test_upload_then_get_then_edit_roundtrip(client, auth, new_candidate):
    candidate = new_candidate("roundtrip")
    cid = candidate["candidate_id"]
    assert candidate["status"] == "New"
    assert candidate["updated_at"] is not None

    got = client.get(f"/api/candidates/{cid}", headers=auth)
    assert got.status_code == 200
    assert got.json()["data"]["candidate_id"] == cid

    candidate["full_name"] = "Edited Name"
    candidate["status"] = "Review"
    put = client.put(f"/api/candidates/{cid}", headers=auth, json=candidate)
    assert put.status_code == 200
    assert put.json()["data"]["full_name"] == "Edited Name"
    assert put.json()["data"]["status"] == "Review"


def test_put_rejects_bad_status(client, auth):
    cid = client.get("/api/candidates", headers=auth).json()["data"][0]["candidate_id"]
    full = client.get(f"/api/candidates/{cid}", headers=auth).json()["data"]
    full["status"] = "Bogus"
    r = client.put(f"/api/candidates/{cid}", headers=auth, json=full)
    assert r.status_code == 400


# ---------------- conditional delete (keys off upload_status) ----------------


def test_delete_rejected_while_processing(client, auth):
    db = SessionLocal()
    try:
        db.add(Candidate(candidate_id="8000001", full_name="In progress",
                         upload_status="Processing"))
        db.commit()
    finally:
        db.close()

    r = client.delete("/api/candidates/8000001", headers=auth)
    assert r.status_code == 400
    assert r.json()["error"] == "Cannot cancel/delete file in current status"


def test_delete_allowed_when_done_or_not_uploaded(client, auth):
    db = SessionLocal()
    try:
        db.add(Candidate(candidate_id="8000002", full_name="Finished",
                         upload_status="Done"))
        db.add(Candidate(candidate_id="8000003", full_name="Draft",
                         upload_status="Not Uploaded"))
        db.commit()
    finally:
        db.close()

    for cid in ("8000002", "8000003"):
        r = client.delete(f"/api/candidates/{cid}", headers=auth)
        assert r.status_code == 200, r.text
        assert r.json()["data"]["deleted"] is True
        assert client.get(f"/api/candidates/{cid}", headers=auth).status_code == 404
