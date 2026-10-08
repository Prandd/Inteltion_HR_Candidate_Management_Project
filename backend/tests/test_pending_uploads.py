"""Round 4 - the create-or-update decision for soft-matched CVs.

A CV that matches an existing candidate only loosely (same phone, or same name
and position, but no matching email) is held instead of guessed at. These tests
cover both exits, the auto-pick rule when several candidates match, and the
stale-list cases.
"""
from conftest import upload


def _stage_soft_duplicate(client, auth, fixed_extraction, marker_a, marker_b,
                          **overrides):
    """Create one candidate, then upload a look-alike. Returns
    (first_candidate_id, pending_review_entry).

    The identity is derived from `marker_a` so two tests never accidentally
    match each other's candidates - the database is shared for the whole
    session, and a stray cross-test hint would show up as a baffling extra
    entry in `duplicate_candidates`.
    """
    base = {
        "email": "",
        "full_name": f"Soft Dup {marker_a}",
        "phone": "0891110000",
        "applied_position": "Backend Engineer",
    }
    base.update(overrides)
    fixed_extraction(marker_a, **base)
    fixed_extraction(marker_b, **base)

    first = upload(client, auth, (f"{marker_a}.pdf", marker_a))
    assert first.status_code == 201, first.text
    first_id = first.json()["data"]["created"][0]["candidate_id"]

    second = upload(client, auth, (f"{marker_b}.pdf", marker_b))
    assert second.status_code == 201, second.text
    reviews = second.json()["data"]["needs_review"]
    assert len(reviews) == 1, second.text
    return first_id, reviews[0]


# ---------------------------------------------------------------- the queue


def test_pending_upload_appears_in_the_queue(client, auth, fixed_extraction):
    _, review = _stage_soft_duplicate(client, auth, fixed_extraction,
                                      "queue-a", "queue-b", phone="0891110001")

    listed = client.get("/api/pending-uploads", headers=auth).json()["data"]
    ids = [p["pending_upload_id"] for p in listed]
    assert review["pending_upload_id"] in ids


def test_queue_requires_auth(client):
    assert client.get("/api/pending-uploads").status_code == 401


def test_preview_shows_enough_to_tell_the_candidates_apart(
    client, auth, fixed_extraction
):
    first_id, review = _stage_soft_duplicate(
        client, auth, fixed_extraction, "preview-a", "preview-b",
        phone="0891110002", full_name="Preview Person",
    )

    assert review["extracted_preview"]["full_name"] == "Preview Person"
    assert review["extracted_preview"]["phone"] == "0891110002"

    hint = review["duplicate_candidates"][0]
    assert hint["candidate_id"] == first_id
    assert hint["full_name"] == "Preview Person"
    assert hint["status"] == "New"


# ---------------------------------------------------------------- update path


def test_update_merges_onto_the_existing_candidate(client, auth, fixed_extraction):
    first_id, review = _stage_soft_duplicate(
        client, auth, fixed_extraction, "upd-a", "upd-b",
        phone="0891110003", summary="the newer CV",
    )
    before = client.get("/api/candidates", headers=auth).json()["data"]

    r = client.post(
        f"/api/pending-uploads/{review['pending_upload_id']}/update", headers=auth
    )
    assert r.status_code == 200, r.text
    body = r.json()["data"]
    assert body["resolution"] == "updated"
    assert body["candidate"]["candidate_id"] == first_id
    assert body["candidate"]["summary"] == "the newer CV"

    # No new candidate appeared.
    after = client.get("/api/candidates", headers=auth).json()["data"]
    assert len(after) == len(before)


def test_replace_restarts_status_and_preserves_other_hr_fields_and_comments(
    client, auth, make_account, fixed_extraction
):
    """Replacing a CV restarts status while preserving other HR data."""
    _, hr = make_account(role="hr")
    first_id, review = _stage_soft_duplicate(
        client, auth, fixed_extraction, "keep-a", "keep-b", phone="0891110004",
    )

    body = client.get(f"/api/candidates/{first_id}", headers=auth).json()["data"]
    body["status"] = "Interview"
    body["applied_position"] = "Staff Engineer"
    body["location"] = "Phuket"
    assert client.put(f"/api/candidates/{first_id}", headers=auth,
                      json=body).status_code == 200
    client.post(f"/api/candidates/{first_id}/comments", headers=hr,
                json={"comment": "screened already"})

    client.post(f"/api/pending-uploads/{review['pending_upload_id']}/update",
                headers=auth)

    after = client.get(f"/api/candidates/{first_id}", headers=auth).json()["data"]
    assert after["status"] == "New"
    history = client.get(f"/api/candidates/{first_id}/status-history", headers=auth).json()["data"]
    assert history[0]["from_status"] == "Interview"
    assert history[0]["to_status"] == "New"
    assert history[0]["reason"] == "Application restarted by replacing CV"
    assert after["applied_position"] == "Staff Engineer"
    assert after["location"] == "Phuket"

    comments = client.get(f"/api/candidates/{first_id}/comments",
                          headers=hr).json()["data"]
    assert [c["comment"] for c in comments] == ["screened already"]


def test_update_stores_the_cv_as_a_new_version(client, auth, fixed_extraction):
    first_id, review = _stage_soft_duplicate(
        client, auth, fixed_extraction, "ver-a", "ver-b", phone="0891110005",
    )

    client.post(f"/api/pending-uploads/{review['pending_upload_id']}/update",
                headers=auth)

    versions = client.get(f"/api/candidates/{first_id}/resume-versions",
                          headers=auth).json()["data"]
    assert [v["version_no"] for v in versions] == [2, 1]
    assert versions[0]["filename"] == "ver-b.pdf"


def test_update_picks_the_most_recently_touched_candidate(
    client, auth, fixed_extraction
):
    """When several candidates match, don't ask - take the one HR is actually
    working on (newest `updated_at`)."""
    shared = {"email": "", "full_name": "Multi Match", "phone": "0891110006",
              "applied_position": "Backend Engineer"}
    for marker in ("multi-1", "multi-2", "multi-3"):
        fixed_extraction(marker, **shared)

    first_id = upload(client, auth, ("m1.pdf", "multi-1")).json()["data"]["created"][0]["candidate_id"]

    # The second one also stops for review; resolve it as a separate person so
    # there are now two candidates the third could match.
    second_review = upload(client, auth, ("m2.pdf", "multi-2")).json()["data"]["needs_review"][0]
    created = client.post(
        f"/api/pending-uploads/{second_review['pending_upload_id']}/create-new",
        headers=auth,
    )
    assert created.status_code == 201, created.text
    second_id = created.json()["data"]["candidate"]["candidate_id"]

    # Touch the FIRST one so it becomes the most recently updated.
    body = client.get(f"/api/candidates/{first_id}", headers=auth).json()["data"]
    body["location"] = "Bangkok"
    client.put(f"/api/candidates/{first_id}", headers=auth, json=body)

    third_review = upload(client, auth, ("m3.pdf", "multi-3")).json()["data"]["needs_review"][0]
    assert {c["candidate_id"] for c in third_review["duplicate_candidates"]} == {
        first_id, second_id
    }

    r = client.post(
        f"/api/pending-uploads/{third_review['pending_upload_id']}/update", headers=auth
    )
    assert r.status_code == 200, r.text
    assert r.json()["data"]["candidate"]["candidate_id"] == first_id


# ------------------------------------------------------------ create-new path


def test_create_new_makes_a_separate_candidate(client, auth, fixed_extraction):
    first_id, review = _stage_soft_duplicate(
        client, auth, fixed_extraction, "new-a", "new-b", phone="0891110007",
    )

    r = client.post(
        f"/api/pending-uploads/{review['pending_upload_id']}/create-new", headers=auth
    )
    assert r.status_code == 201, r.text
    body = r.json()["data"]
    assert body["resolution"] == "created_new"

    new_id = body["candidate"]["candidate_id"]
    assert new_id != first_id
    # The near-match stays visible on the new record.
    assert first_id in body["candidate"]["possible_duplicate_of"]
    assert body["candidate"]["upload_status"] == "Done"

    # Both exist independently.
    assert client.get(f"/api/candidates/{first_id}", headers=auth).status_code == 200
    assert client.get(f"/api/candidates/{new_id}", headers=auth).status_code == 200


def test_create_new_stores_the_cv_as_version_one(client, auth, fixed_extraction):
    _, review = _stage_soft_duplicate(
        client, auth, fixed_extraction, "v1-a", "v1-b", phone="0891110008",
    )

    new_id = client.post(
        f"/api/pending-uploads/{review['pending_upload_id']}/create-new", headers=auth
    ).json()["data"]["candidate"]["candidate_id"]

    versions = client.get(f"/api/candidates/{new_id}/resume-versions",
                          headers=auth).json()["data"]
    assert [v["version_no"] for v in versions] == [1]
    assert versions[0]["filename"] == "v1-b.pdf"


# ---------------------------------------------------------------- discard


def test_discard_leaves_no_candidate_behind(client, auth, fixed_extraction):
    _, review = _stage_soft_duplicate(
        client, auth, fixed_extraction, "dis-a", "dis-b", phone="0891110009",
    )
    before = len(client.get("/api/candidates", headers=auth).json()["data"])

    r = client.delete(f"/api/pending-uploads/{review['pending_upload_id']}",
                      headers=auth)
    assert r.status_code == 200
    assert r.json()["data"]["discarded"] is True

    after = len(client.get("/api/candidates", headers=auth).json()["data"])
    assert after == before


def test_discard_drops_the_stored_cv_bytes(client, auth, fixed_extraction):
    """PDPA: we decided not to keep this resume, so we must not still hold it."""
    _, review = _stage_soft_duplicate(
        client, auth, fixed_extraction, "bytes-a", "bytes-b", phone="0891110010",
    )
    client.delete(f"/api/pending-uploads/{review['pending_upload_id']}", headers=auth)

    from app.database import SessionLocal
    from app.models_db import PendingUpload

    db = SessionLocal()
    try:
        row = db.get(PendingUpload, review["pending_upload_id"])
        assert row is not None, "the decision itself stays as an audit record"
        assert row.resolution == "discarded"
        assert row.file_bytes is None
    finally:
        db.close()


# ---------------------------------------------------------------- stale cases


def test_resolving_twice_is_a_409(client, auth, fixed_extraction):
    _, review = _stage_soft_duplicate(
        client, auth, fixed_extraction, "twice-a", "twice-b", phone="0891110011",
    )
    pid = review["pending_upload_id"]

    assert client.post(f"/api/pending-uploads/{pid}/update",
                       headers=auth).status_code == 200

    again = client.post(f"/api/pending-uploads/{pid}/update", headers=auth)
    assert again.status_code == 409
    assert "already resolved" in again.json()["error"]

    other_way = client.post(f"/api/pending-uploads/{pid}/create-new", headers=auth)
    assert other_way.status_code == 409


def test_resolved_items_leave_the_queue(client, auth, fixed_extraction):
    _, review = _stage_soft_duplicate(
        client, auth, fixed_extraction, "gone-a", "gone-b", phone="0891110012",
    )
    pid = review["pending_upload_id"]
    client.post(f"/api/pending-uploads/{pid}/update", headers=auth)

    listed = client.get("/api/pending-uploads", headers=auth).json()["data"]
    assert pid not in [p["pending_upload_id"] for p in listed]


def test_unknown_pending_upload_is_404(client, auth):
    r = client.post("/api/pending-uploads/does-not-exist/update", headers=auth)
    assert r.status_code == 404


def test_update_when_every_match_was_deleted_says_use_create_new(
    client, auth, fixed_extraction
):
    first_id, review = _stage_soft_duplicate(
        client, auth, fixed_extraction, "del-a", "del-b", phone="0891110013",
    )
    assert client.delete(f"/api/candidates/{first_id}",
                         headers=auth).status_code == 200

    r = client.post(
        f"/api/pending-uploads/{review['pending_upload_id']}/update", headers=auth
    )
    assert r.status_code == 409
    assert "create-new" in r.json()["error"]

    # ...and that suggestion actually works.
    fallback = client.post(
        f"/api/pending-uploads/{review['pending_upload_id']}/create-new", headers=auth
    )
    assert fallback.status_code == 201
<<<<<<< HEAD


def test_replacing_rejected_candidate_starts_new_and_clears_rejection_state(
    client, auth, fixed_extraction, admin_login
):
    cid, review = _stage_soft_duplicate(
        client, auth, fixed_extraction, "restart-rejected-a", "restart-rejected-b",
        phone="0891110099",
    )
    client.put(f"/api/candidates/{cid}", headers=auth, json={"status": "Interview"})
    rejected = client.put(f"/api/candidates/{cid}", headers=auth, json={"status": "Rejected"})
    assert rejected.status_code == 200, rejected.text
    response = client.post(f"/api/pending-uploads/{review['pending_upload_id']}/update", headers=auth)
    assert response.status_code == 200, response.text
    candidate = response.json()["data"]["candidate"]
    assert candidate["candidate_id"] == cid
    assert candidate["status"] == "New"
    assert candidate["before_rejected_status"] == ""
    assert candidate["owner_account_id"] == admin_login["account"]["account_id"]
    history = client.get(f"/api/candidates/{cid}/status-history", headers=auth).json()["data"]
    assert history[0]["from_status"] == "Rejected"
    assert history[0]["to_status"] == "New"
    assert history[0]["changed_by"] == admin_login["account"]["account_id"]
=======
>>>>>>> origin/feature/backend
