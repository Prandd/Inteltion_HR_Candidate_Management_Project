"""`GET /api/candidates?q=` also searches comments (text and author name) and
skill group names, not just name/email/id/tools."""
from app.database import SessionLocal
from app.models_db import Candidate


def _ids(client, auth, q):
    r = client.get("/api/candidates", headers=auth, params={"q": q})
    assert r.status_code == 200
    return [row["candidate_id"] for row in r.json()["data"]]


def _add_comment(client, auth, candidate_id, text):
    r = client.post(
        f"/api/candidates/{candidate_id}/comments", headers=auth, json={"comment": text}
    )
    assert r.status_code == 201
    return r.json()["data"]


def test_q_matches_comment_text_case_insensitively(client, auth):
    assert "0000001" not in _ids(client, auth, "zzquokka")
    _add_comment(client, auth, "0000001", "Great ZZQuokka fluency on the call")
    assert "0000001" in _ids(client, auth, "zzquokka")
    assert "0000001" in _ids(client, auth, "ZZQUOKKA")


def test_q_matches_comment_author_name(client, auth):
    comment = _add_comment(client, auth, "0000002", "plain note")
    author = comment["author_name"]
    assert author, "comment should carry the author's name"
    assert "0000002" in _ids(client, auth, author)


def test_q_ignores_deleted_comments(client, auth):
    comment = _add_comment(client, auth, "0000003", "zzdeletedmarker")
    assert "0000003" in _ids(client, auth, "zzdeletedmarker")
    r = client.delete(f"/api/comments/{comment['comment_id']}", headers=auth)
    assert r.status_code == 200
    assert "0000003" not in _ids(client, auth, "zzdeletedmarker")


def test_q_treats_percent_and_underscore_literally(client, auth):
    _add_comment(client, auth, "0000001", "ordinary text")
    assert _ids(client, auth, "%") == []
    assert _ids(client, auth, "_") == []


def test_q_matches_skill_group_name_and_tool(client, auth):
    db = SessionLocal()
    try:
        row = db.get(Candidate, "0000004")
        row.skills = [{"skill": "Programming Languages", "tools": ["C++", "Python"]}]
        db.commit()
    finally:
        db.close()
    assert "0000004" in _ids(client, auth, "programming languages")
    assert "0000004" in _ids(client, auth, "c++")
