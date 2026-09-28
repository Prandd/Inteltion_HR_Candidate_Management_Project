import io

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "ok"


def test_list_is_enveloped_list():
    r = client.get("/api/candidates")
    assert r.status_code == 200
    body = r.json()
    assert body["error"] is None
    assert isinstance(body["data"], list)


def test_get_unknown_returns_404_envelope():
    r = client.get("/api/candidates/does-not-exist")
    assert r.status_code == 404
    assert r.json()["data"] is None
    assert r.json()["error"]


def test_upload_rejects_non_pdf_docx():
    r = client.post(
        "/api/candidates/upload",
        files={"file": ("resume.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert r.status_code == 400


def test_upload_then_get_then_edit_roundtrip():
    up = client.post(
        "/api/candidates/upload",
        files={"file": ("resume.pdf", io.BytesIO(b"%PDF-1.4 fake bytes"), "application/pdf")},
    )
    assert up.status_code == 201
    candidate = up.json()["data"]
    cid = candidate["candidate_id"]
    assert candidate["status"] == "New"
    assert candidate["updated_at"] is not None

    got = client.get(f"/api/candidates/{cid}")
    assert got.status_code == 200
    assert got.json()["data"]["candidate_id"] == cid

    candidate["full_name"] = "Edited Name"
    candidate["hr_comment"] = "Strong backend fit"
    candidate["status"] = "Review"
    put = client.put(f"/api/candidates/{cid}", json=candidate)
    assert put.status_code == 200
    data = put.json()["data"]
    assert data["full_name"] == "Edited Name"
    assert data["hr_comment"] == "Strong backend fit"
    assert data["status"] == "Review"


def test_put_rejects_bad_status():
    lst = client.get("/api/candidates").json()["data"]
    assert lst, "seed data should be present"
    cid = lst[0]["candidate_id"]
    full = client.get(f"/api/candidates/{cid}").json()["data"]
    full["status"] = "Bogus"
    r = client.put(f"/api/candidates/{cid}", json=full)
    assert r.status_code == 400
