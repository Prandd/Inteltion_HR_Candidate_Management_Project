"""F3 - comment_logs. Ownership, immutability, and the forged-body cases."""


def _post(client, headers, candidate_id, **body):
    return client.post(
        f"/api/candidates/{candidate_id}/comments", headers=headers, json=body
    )


def test_comment_is_attributed_from_the_jwt(client, make_account, new_candidate):
    account, headers = make_account(role="hr")
    cid = new_candidate()["candidate_id"]

    r = _post(client, headers, cid, comment="Phone screen went well.")
    assert r.status_code == 201, r.text
    comment = r.json()["data"]
    assert comment["author_account_id"] == account["account_id"]
    assert comment["author_name"] == account["full_name"]
    assert comment["author_role"] == "hr"
    assert comment["comment_type"] == "hr"  # defaulted from the role
    assert comment["candidate_id"] == cid
    assert comment["is_edited"] is False


def test_forged_author_in_the_body_is_ignored(client, make_account, new_candidate):
    victim, _ = make_account(role="hr")
    attacker_account, attacker = make_account(role="hr")
    cid = new_candidate()["candidate_id"]

    # Built inline rather than through _post(): the forged body deliberately
    # carries its own `candidate_id`, which would collide with the helper's
    # path argument.
    r = client.post(
        f"/api/candidates/{cid}/comments",
        headers=attacker,
        json={
            "comment": "Signed by someone else.",
            "author_account_id": victim["account_id"],
            "author_name": victim["full_name"],
            "author_role": "admin",
            "candidate_id": "0000001",
        },
    )
    assert r.status_code == 201
    comment = r.json()["data"]
    assert comment["author_account_id"] == attacker_account["account_id"]
    assert comment["author_name"] == attacker_account["full_name"]
    assert comment["author_role"] == "hr"
    assert comment["candidate_id"] == cid  # from the path, not the body


def test_another_user_cannot_edit_or_delete(client, make_account, new_candidate):
    _, author = make_account(role="hr")
    _, other = make_account(role="hr")
    cid = new_candidate()["candidate_id"]

    comment_id = _post(client, author, cid, comment="Mine.").json()["data"]["comment_id"]

    assert client.put(
        f"/api/comments/{comment_id}", headers=other, json={"comment": "Hijacked"}
    ).status_code == 403
    assert client.delete(f"/api/comments/{comment_id}", headers=other).status_code == 403

    still = client.get(f"/api/candidates/{cid}/comments", headers=author).json()["data"]
    assert [c["comment"] for c in still] == ["Mine."]


def test_forged_author_id_in_an_edit_body_does_not_grant_access(
    client, make_account, new_candidate
):
    author_account, author = make_account(role="hr")
    _, other = make_account(role="hr")
    cid = new_candidate()["candidate_id"]
    comment_id = _post(client, author, cid, comment="Mine.").json()["data"]["comment_id"]

    r = client.put(
        f"/api/comments/{comment_id}",
        headers=other,
        json={"comment": "Hijacked", "author_account_id": author_account["account_id"]},
    )
    assert r.status_code == 403


def test_admin_may_delete_but_not_edit_someone_elses_comment(
    client, auth, make_account, new_candidate
):
    """Round-4 decision: deletion is moderation, editing would break attribution
    (the comment would still carry the original author's name)."""
    _, author = make_account(role="hr")
    cid = new_candidate()["candidate_id"]
    comment_id = _post(client, author, cid, comment="Author's words.").json()["data"]["comment_id"]

    assert client.put(
        f"/api/comments/{comment_id}", headers=auth, json={"comment": "Rewritten by admin"}
    ).status_code == 403
    assert client.delete(f"/api/comments/{comment_id}", headers=auth).status_code == 200


def test_created_at_survives_an_edit_that_tries_to_set_it(
    client, make_account, new_candidate
):
    _, headers = make_account(role="hr")
    cid = new_candidate()["candidate_id"]
    original = _post(client, headers, cid, comment="First draft.").json()["data"]

    r = client.put(
        f"/api/comments/{original['comment_id']}",
        headers=headers,
        json={
            "comment": "Second draft.",
            "created_at": "1999-01-01T00:00:00Z",
            "updated_at": "1999-01-01T00:00:00Z",
        },
    )
    assert r.status_code == 200
    edited = r.json()["data"]
    assert edited["created_at"] == original["created_at"]
    assert edited["comment"] == "Second draft."
    assert edited["is_edited"] is True


def test_the_display_timestamp_is_editable(client, make_account, new_candidate):
    """HR backdating a comment about a call last Tuesday is the whole reason for
    the two-timestamp split."""
    _, headers = make_account(role="hr")
    cid = new_candidate()["candidate_id"]
    comment = _post(client, headers, cid, comment="Called them.").json()["data"]

    r = client.put(
        f"/api/comments/{comment['comment_id']}",
        headers=headers,
        json={"commented_at": "2026-09-08T09:00:00Z"},
    )
    assert r.status_code == 200
    edited = r.json()["data"]
    assert edited["commented_at"].startswith("2026-09-08T09:00:00")
    assert edited["created_at"] == comment["created_at"]


def test_backdating_on_create_is_allowed(client, make_account, new_candidate):
    _, headers = make_account(role="hr")
    cid = new_candidate()["candidate_id"]
    r = _post(client, headers, cid, comment="From last week.",
              commented_at="2026-09-10T08:30:00Z")
    assert r.status_code == 201
    assert r.json()["data"]["commented_at"].startswith("2026-09-10T08:30:00")


def test_empty_comment_is_rejected(client, make_account, new_candidate):
    _, headers = make_account(role="hr")
    cid = new_candidate()["candidate_id"]
    assert _post(client, headers, cid, comment="   ").status_code == 400
    assert _post(client, headers, cid, comment="").status_code == 400


def test_soft_delete_hides_the_comment_but_keeps_the_row(
    client, make_account, new_candidate
):
    _, headers = make_account(role="hr")
    cid = new_candidate()["candidate_id"]
    comment_id = _post(client, headers, cid, comment="Delete me.").json()["data"]["comment_id"]

    assert client.delete(f"/api/comments/{comment_id}", headers=headers).status_code == 200
    listed = client.get(f"/api/candidates/{cid}/comments", headers=headers).json()["data"]
    assert comment_id not in [c["comment_id"] for c in listed]

    from app.database import SessionLocal
    from app.models_db import CommentLog

    db = SessionLocal()
    try:
        row = db.get(CommentLog, comment_id)
        assert row is not None, "soft delete must keep the record"
        assert row.deleted_at is not None
    finally:
        db.close()

    # A deleted comment is gone for editing too.
    assert client.put(
        f"/api/comments/{comment_id}", headers=headers, json={"comment": "back?"}
    ).status_code == 404


def test_comments_are_sorted_and_filterable_by_type(client, make_account, new_candidate):
    _, hr = make_account(role="hr")
    _, lm = make_account(role="line_manager")
    cid = new_candidate()["candidate_id"]

    _post(client, hr, cid, comment="Older", commented_at="2026-09-01T10:00:00Z")
    _post(client, hr, cid, comment="Newer", commented_at="2026-09-05T10:00:00Z")
    _post(client, lm, cid, comment="Manager note")

    everything = client.get(f"/api/candidates/{cid}/comments", headers=hr).json()["data"]
    assert len(everything) == 3
    stamps = [c["commented_at"] for c in everything]
    assert stamps == sorted(stamps, reverse=True), "newest first"

    hr_only = client.get(
        f"/api/candidates/{cid}/comments", headers=hr, params={"comment_type": "hr"}
    ).json()["data"]
    assert [c["comment"] for c in hr_only] == ["Newer", "Older"]
    assert all(c["comment_type"] == "hr" for c in hr_only)


def test_deprecated_candidate_fields_are_computed_from_comments(
    client, auth, make_account, new_candidate
):
    """F3 phase 1: Lanes A and B keep rendering something while they migrate."""
    _, hr = make_account(role="hr")
    _, lm = make_account(role="line_manager")
    cid = new_candidate()["candidate_id"]

    _post(client, hr, cid, comment="Older HR note", commented_at="2026-09-01T10:00:00Z")
    _post(client, hr, cid, comment="Newest HR note", commented_at="2026-09-09T10:00:00Z")
    _post(client, lm, cid, comment="Manager note")

    candidate = client.get(f"/api/candidates/{cid}", headers=auth).json()["data"]
    assert candidate["hr_comment"] == "Newest HR note"
    assert candidate["line_manager_comment"] == "Manager note"


def test_writing_the_deprecated_fields_through_put_is_ignored(
    client, auth, new_candidate
):
    cid = new_candidate()["candidate_id"]
    body = client.get(f"/api/candidates/{cid}", headers=auth).json()["data"]
    body["hr_comment"] = "written the old way"
    body["line_manager_comment"] = "also the old way"

    r = client.put(f"/api/candidates/{cid}", headers=auth, json=body)
    assert r.status_code == 200
    assert r.json()["data"]["hr_comment"] == ""
    assert r.json()["data"]["line_manager_comment"] == ""


def test_comments_on_an_unknown_candidate_are_404(client, make_account):
    _, headers = make_account(role="hr")
    assert client.get("/api/candidates/9999999/comments", headers=headers).status_code == 404
    assert _post(client, headers, "9999999", comment="ghost").status_code == 404


def test_invalid_comment_type_is_rejected(client, make_account, new_candidate):
    _, headers = make_account(role="hr")
    cid = new_candidate()["candidate_id"]
    assert _post(client, headers, cid, comment="hi", comment_type="gossip").status_code == 400


# ---------------------------------------------- round 5: /candidates/comments alias


def test_candidates_prefixed_path_edits_the_same_comment(
    client, make_account, new_candidate
):
    """Compatibility alias added for feature/frontend-update, which calls
    PUT/DELETE /candidates/comments/{id} instead of the canonical
    /comments/{id}. Both paths must hit the exact same row and the exact same
    ownership rule."""
    account, headers = make_account(role="hr")
    cid = new_candidate()["candidate_id"]
    comment_id = _post(client, headers, cid, comment="original").json()["data"]["comment_id"]

    r = client.put(
        f"/api/candidates/comments/{comment_id}", headers=headers,
        json={"comment": "edited via the alias path"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["data"]["comment"] == "edited via the alias path"

    # The canonical path sees the same edit - it is the same row, not a copy.
    canonical = client.get(f"/api/candidates/{cid}/comments", headers=headers).json()["data"]
    assert canonical[0]["comment"] == "edited via the alias path"


def test_candidates_prefixed_path_still_enforces_ownership(
    client, make_account, new_candidate
):
    _, author_headers = make_account(role="hr")
    _, other_headers = make_account(role="hr")
    cid = new_candidate()["candidate_id"]
    comment_id = _post(client, author_headers, cid, comment="mine").json()["data"]["comment_id"]

    r = client.put(
        f"/api/candidates/comments/{comment_id}", headers=other_headers,
        json={"comment": "hijacked"},
    )
    assert r.status_code == 403


def test_candidates_prefixed_delete_alias_also_soft_deletes(
    client, make_account, new_candidate
):
    _, headers = make_account(role="hr")
    cid = new_candidate()["candidate_id"]
    comment_id = _post(client, headers, cid, comment="delete me").json()["data"]["comment_id"]

    r = client.delete(f"/api/candidates/comments/{comment_id}", headers=headers)
    assert r.status_code == 200
    assert r.json()["data"]["deleted"] is True

    listed = client.get(f"/api/candidates/{cid}/comments", headers=headers).json()["data"]
    assert comment_id not in [c["comment_id"] for c in listed]


def test_comment_list_shows_updated_account_name(client, auth, make_account, new_candidate):
    author, headers = make_account(role="hr", full_name="Original Name")
    cid = new_candidate()["candidate_id"]
    response = client.post(f"/api/candidates/{cid}/comments", headers=headers,
                           json={"comment": "Feedback from this account"})
    assert response.status_code == 201, response.text
    comment_id = response.json()["data"]["comment_id"]
    renamed = client.put(f"/api/hr-accounts/{author['account_id']}", headers=auth,
                        json={"full_name": "Updated Name"})
    assert renamed.status_code == 200, renamed.text
    comments = client.get(f"/api/candidates/{cid}/comments", headers=auth).json()["data"]
    comment = next(item for item in comments if item["comment_id"] == comment_id)
    assert comment["author_name"] == "Updated Name"
    assert comment["author_account_id"] == author["account_id"]
    assert comment["is_edited"] is False
