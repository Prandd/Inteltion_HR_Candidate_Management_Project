"""Round 5 - scores from the external SQL-test tool.

The tool's real request contract is not confirmed yet, so these tests cover
what IS decided: a required numeric score, arbitrary extra data preserved
verbatim in raw_payload, normal auth, and simple retrieval. Nothing here should
be read as "this is the final shape" - see the note in models_db.py.
"""


def test_add_and_read_a_score(client, auth, new_candidate):
    cid = new_candidate()["candidate_id"]

    r = client.post(
        f"/api/candidates/{cid}/sql-test-score", headers=auth,
        json={"score": 87.5},
    )
    assert r.status_code == 201, r.text
    body = r.json()["data"]
    assert body["candidate_id"] == cid
    assert body["score"] == 87.5
    assert body["source"] == "sql_test"
    assert body["recorded_by"]  # attributed to the caller

    listed = client.get(f"/api/candidates/{cid}/sql-test-scores", headers=auth).json()["data"]
    assert [s["score"] for s in listed] == [87.5]


def test_raw_payload_is_preserved_verbatim(client, auth, new_candidate):
    """Nothing about the eventual real contract is known yet - whatever extra
    fields the caller sends must survive untouched."""
    cid = new_candidate()["candidate_id"]

    extra = {"query_count": 12, "passed": 10, "time_taken_ms": 45210,
             "breakdown": {"joins": 4, "subqueries": 2}}
    r = client.post(
        f"/api/candidates/{cid}/sql-test-score", headers=auth,
        json={"score": 91, "source": "external-sql-tool-v2", "raw_payload": extra},
    )
    assert r.status_code == 201, r.text
    body = r.json()["data"]
    assert body["source"] == "external-sql-tool-v2"
    assert body["raw_payload"] == extra


def test_multiple_scores_are_kept_not_overwritten(client, auth, new_candidate):
    """A candidate might sit the test more than once, or the tool might report
    progress - every submission is its own row, newest first."""
    cid = new_candidate()["candidate_id"]

    for score in (60, 75, 92):
        r = client.post(
            f"/api/candidates/{cid}/sql-test-score", headers=auth, json={"score": score}
        )
        assert r.status_code == 201

    listed = client.get(f"/api/candidates/{cid}/sql-test-scores", headers=auth).json()["data"]
    assert [s["score"] for s in listed] == [92, 75, 60]


def test_score_requires_auth(client, new_candidate):
    cid = new_candidate()["candidate_id"]
    r = client.post(f"/api/candidates/{cid}/sql-test-score", json={"score": 50})
    assert r.status_code == 401


def test_non_finite_score_is_rejected(client, auth, new_candidate):
    """Regression case for a real bug this uncovered: FastAPI's own
    RequestValidationError.errors() embeds the offending value verbatim, and
    Starlette's JSONResponse refuses to encode inf/nan (allow_nan=False) - so
    reporting *why* Infinity was rejected used to crash into a 500 instead of
    a clean 400. See _json_safe() in app/main.py.

    Sent as raw bytes containing the bare (non-standard but widely-accepted)
    Infinity/-Infinity/NaN JSON literals - Python's own stdlib json.dumps()
    would emit exactly this for float('inf') etc., but httpx's `json=`
    shorthand refuses to encode them at all (ValueError, request never sent),
    so building the body by hand is what actually reaches the server.
    """
    cid = new_candidate()["candidate_id"]
    for literal in ("Infinity", "-Infinity", "NaN"):
        r = client.post(
            f"/api/candidates/{cid}/sql-test-score",
            headers={**auth, "Content-Type": "application/json"},
            content=f'{{"score": {literal}}}'.encode(),
        )
        assert r.status_code == 400, r.text
        assert r.json()["error"] == "Validation error"


def test_score_on_unknown_candidate_is_404(client, auth):
    r = client.post(
        "/api/candidates/9999999/sql-test-score", headers=auth, json={"score": 50}
    )
    assert r.status_code == 404
    assert client.get("/api/candidates/9999999/sql-test-scores", headers=auth).status_code == 404
