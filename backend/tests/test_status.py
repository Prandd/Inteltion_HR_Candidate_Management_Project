"""F5 (before_rejected_status + status history) and F6 (one canonical enum)."""
import json
import os

import pytest

from app.statuses import REJECTED_STATES, STATUS_VALUES

REJECTED = sorted(REJECTED_STATES)[0]


def _put_status(client, auth, candidate_id, status):
    body = client.get(f"/api/candidates/{candidate_id}", headers=auth).json()["data"]
    body["status"] = status
    return client.put(f"/api/candidates/{candidate_id}", headers=auth, json=body)


# ---------------- F6 ----------------


def test_backend_enum_matches_the_contract(client):
    """The one thing round 4 had to guarantee: backend and contract cannot drift."""
    here = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(here, "..", "..", "shared-contracts", "schema.json")
    with open(schema_path, "r", encoding="utf-8") as fh:
        contract = json.load(fh)
    assert contract["properties"]["status"]["enum"] == STATUS_VALUES


def test_health_publishes_the_canonical_enum(client):
    assert client.get("/health").json()["data"]["statuses"] == STATUS_VALUES


@pytest.mark.parametrize(
    "bad",
    [
        "CV rejected",  # the pre-v2.1.0 name - must NOT be accepted any more
        "rejected",     # wrong case
        "CVRejected",
        "",
        "Bogus",
    ],
)
def test_status_outside_the_enum_is_rejected(client, auth, new_candidate, bad):
    cid = new_candidate()["candidate_id"]
    assert _put_status(client, auth, cid, bad).status_code == 400


def test_generated_typescript_matches_the_contract():
    """status.ts is generated from schema.json - if somebody edits one by hand,
    Lane A's Kanban silently drops a column. Catch it here instead."""
    here = os.path.dirname(os.path.abspath(__file__))
    ts_path = os.path.join(here, "..", "..", "shared-contracts", "status.ts")
    with open(ts_path, "r", encoding="utf-8") as fh:
        ts = fh.read()
    for value in STATUS_VALUES:
        assert json.dumps(value) in ts, f"{value!r} missing from status.ts"


# ---------------- F5 ----------------


def test_before_rejected_status_captures_the_stage(client, auth, new_candidate):
    cid = new_candidate()["candidate_id"]
    _put_status(client, auth, cid, "Interview")

    r = _put_status(client, auth, cid, REJECTED)
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["status"] == REJECTED
    assert data["before_rejected_status"] == "Interview"


def test_before_rejected_status_survives_an_unrelated_put(client, auth, new_candidate):
    """The regression the naive "mirror status on every write" implementation
    would introduce: the next PUT re-runs the mirror and stamps
    before_rejected_status = the rejected status itself."""
    cid = new_candidate()["candidate_id"]
    _put_status(client, auth, cid, "Assessment")
    _put_status(client, auth, cid, REJECTED)

    body = client.get(f"/api/candidates/{cid}", headers=auth).json()["data"]
    body["phone"] = "0800000000"  # nothing to do with status
    r = client.put(f"/api/candidates/{cid}", headers=auth, json=body)

    assert r.status_code == 200
    assert r.json()["data"]["status"] == REJECTED
    assert r.json()["data"]["before_rejected_status"] == "Assessment"


def test_before_rejected_status_is_not_settable_from_the_body(
    client, auth, new_candidate
):
    cid = new_candidate()["candidate_id"]
    body = client.get(f"/api/candidates/{cid}", headers=auth).json()["data"]
    body["before_rejected_status"] = "Hired"
    r = client.put(f"/api/candidates/{cid}", headers=auth, json=body)
    assert r.status_code == 200
    assert r.json()["data"]["before_rejected_status"] == ""


def test_moving_out_of_a_rejected_state_clears_the_field(client, auth, new_candidate):
    cid = new_candidate()["candidate_id"]
    _put_status(client, auth, cid, "Review")
    _put_status(client, auth, cid, REJECTED)
    r = _put_status(client, auth, cid, "Interview")
    assert r.json()["data"]["before_rejected_status"] == ""


def test_restore_moves_the_candidate_back(client, auth, new_candidate):
    cid = new_candidate()["candidate_id"]
    _put_status(client, auth, cid, "Assessment")
    _put_status(client, auth, cid, REJECTED)

    r = client.post(f"/api/candidates/{cid}/restore", headers=auth,
                    json={"reason": "rejected by mistake"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["status"] == "Assessment"
    assert data["before_rejected_status"] == ""


def test_restore_refuses_when_the_candidate_is_not_rejected(
    client, auth, new_candidate
):
    cid = new_candidate()["candidate_id"]
    r = client.post(f"/api/candidates/{cid}/restore", headers=auth, json={"reason": ""})
    assert r.status_code == 400


def test_status_history_records_every_transition(client, auth, new_candidate):
    cid = new_candidate()["candidate_id"]
    _put_status(client, auth, cid, "Review")
    _put_status(client, auth, cid, "Assessment")
    _put_status(client, auth, cid, REJECTED)

    history = client.get(
        f"/api/candidates/{cid}/status-history", headers=auth
    ).json()["data"]
    transitions = [(h["from_status"], h["to_status"]) for h in history]
    assert ("Assessment", REJECTED) in transitions
    assert ("Review", "Assessment") in transitions
    assert ("New", "Review") in transitions
    assert all(h["changed_by"] for h in history), "every change is attributed"


def test_a_no_op_status_write_adds_no_history(client, auth, new_candidate):
    cid = new_candidate()["candidate_id"]
    before = len(client.get(
        f"/api/candidates/{cid}/status-history", headers=auth
    ).json()["data"])

    _put_status(client, auth, cid, "New")  # already "New"

    after = len(client.get(
        f"/api/candidates/{cid}/status-history", headers=auth
    ).json()["data"])
    assert after == before


def test_seeded_rejected_candidate_carries_its_prior_stage(client, auth):
    """mock-candidates.json ships one rejected candidate so Lane A can render the
    'rejected at X' badge against fixtures."""
    rows = client.get("/api/candidates", headers=auth, params={"status": REJECTED}).json()["data"]
    assert rows, f"expected a seeded candidate with status {REJECTED!r}"
    assert any(r["before_rejected_status"] for r in rows)
