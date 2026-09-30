"""Round 5 - candidate ownership.

Rule: whoever imports a CV owns it. Re-upload and the pending-upload "update"
resolution never change it. Only the dedicated transfer endpoint does, and only
for the current owner or an admin.
"""
from conftest import upload


def test_owner_is_the_uploading_account(client, auth, admin_login, new_candidate):
    candidate = new_candidate()
    assert candidate["owner_account_id"] == admin_login["account"]["account_id"]
    assert candidate["owner_name"]  # not blank


def test_owner_appears_on_the_list_endpoint_too(client, auth, admin_login, new_candidate):
    candidate = new_candidate()
    rows = client.get("/api/candidates", headers=auth).json()["data"]
    row = next(r for r in rows if r["candidate_id"] == candidate["candidate_id"])
    assert row["owner_account_id"] == admin_login["account"]["account_id"]
    assert row["owner_name"] == candidate["owner_name"]


def test_owner_account_id_filters_the_list(client, auth, make_account, new_candidate):
    owner_account, owner_headers = make_account(role="hr")

    # Uploaded by a DIFFERENT account than the filter target, on purpose -
    # proves the filter is really reading owner_account_id, not just "did this
    # account touch the row somehow".
    import app.routers.candidates as candidates_router
    from conftest import candidate_fields
    from unittest import mock

    spec = candidate_fields(full_name="Owner Filter Target")
    with mock.patch.object(candidates_router, "extract_candidate",
                           lambda b, filename=None: dict(spec)):
        r = upload(client, owner_headers, ("owned.pdf", "owner-filter-marker"))
    assert r.status_code == 201, r.text
    owned_id = r.json()["data"]["created"][0]["candidate_id"]

    filtered = client.get(
        "/api/candidates", headers=auth,
        params={"owner_account_id": owner_account["account_id"]},
    ).json()["data"]
    assert [r["candidate_id"] for r in filtered] == [owned_id]


# ---------------------------------------------------------------- transfer


def test_owner_can_transfer_their_own_candidate(client, make_account, new_candidate):
    owner_account, owner_headers = make_account(role="hr")
    other_account, _ = make_account(role="hr")

    import app.routers.candidates as candidates_router
    from conftest import candidate_fields
    from unittest import mock

    spec = candidate_fields(full_name="Transfer Test A")
    with mock.patch.object(candidates_router, "extract_candidate",
                           lambda b, filename=None: dict(spec)):
        created = upload(client, owner_headers, ("a.pdf", "transfer-a")).json()["data"]["created"][0]
    cid = created["candidate_id"]
    assert created["owner_account_id"] == owner_account["account_id"]

    r = client.post(
        f"/api/candidates/{cid}/transfer-ownership", headers=owner_headers,
        json={"new_owner_account_id": other_account["account_id"], "reason": "going on leave"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["data"]["owner_account_id"] == other_account["account_id"]


def test_admin_can_transfer_a_candidate_they_do_not_own(client, auth, make_account, new_candidate):
    owner_account, owner_headers = make_account(role="hr")
    other_account, _ = make_account(role="hr")

    import app.routers.candidates as candidates_router
    from conftest import candidate_fields
    from unittest import mock

    spec = candidate_fields(full_name="Transfer Test B")
    with mock.patch.object(candidates_router, "extract_candidate",
                           lambda b, filename=None: dict(spec)):
        created = upload(client, owner_headers, ("b.pdf", "transfer-b")).json()["data"]["created"][0]
    cid = created["candidate_id"]

    r = client.post(
        f"/api/candidates/{cid}/transfer-ownership", headers=auth,  # the seed admin, not the owner
        json={"new_owner_account_id": other_account["account_id"]},
    )
    assert r.status_code == 200, r.text
    assert r.json()["data"]["owner_account_id"] == other_account["account_id"]


def test_neither_owner_nor_admin_cannot_transfer(client, make_account, new_candidate):
    owner_account, owner_headers = make_account(role="hr")
    _, bystander_headers = make_account(role="hr")
    target_account, _ = make_account(role="hr")

    import app.routers.candidates as candidates_router
    from conftest import candidate_fields
    from unittest import mock

    spec = candidate_fields(full_name="Transfer Test C")
    with mock.patch.object(candidates_router, "extract_candidate",
                           lambda b, filename=None: dict(spec)):
        created = upload(client, owner_headers, ("c.pdf", "transfer-c")).json()["data"]["created"][0]
    cid = created["candidate_id"]

    r = client.post(
        f"/api/candidates/{cid}/transfer-ownership", headers=bystander_headers,
        json={"new_owner_account_id": target_account["account_id"]},
    )
    assert r.status_code == 403


def test_the_incoming_owner_cannot_grant_themselves_ownership(
    client, make_account, new_candidate
):
    """A transfer is done TO an account, never something an account does to
    itself - being the target does not make you an allowed caller."""
    owner_account, owner_headers = make_account(role="hr")
    target_account, target_headers = make_account(role="hr")

    import app.routers.candidates as candidates_router
    from conftest import candidate_fields
    from unittest import mock

    spec = candidate_fields(full_name="Transfer Test D")
    with mock.patch.object(candidates_router, "extract_candidate",
                           lambda b, filename=None: dict(spec)):
        created = upload(client, owner_headers, ("d.pdf", "transfer-d")).json()["data"]["created"][0]
    cid = created["candidate_id"]

    r = client.post(
        f"/api/candidates/{cid}/transfer-ownership", headers=target_headers,
        json={"new_owner_account_id": target_account["account_id"]},
    )
    assert r.status_code == 403


def test_transfer_to_unknown_account_is_404(client, auth, new_candidate):
    cid = new_candidate()["candidate_id"]
    r = client.post(
        f"/api/candidates/{cid}/transfer-ownership", headers=auth,
        json={"new_owner_account_id": "does-not-exist"},
    )
    assert r.status_code == 404


def test_transfer_to_a_deactivated_account_is_400(client, auth, make_account, new_candidate):
    deactivated, _ = make_account(role="hr")
    client.delete(f"/api/hr-accounts/{deactivated['account_id']}", headers=auth)

    cid = new_candidate()["candidate_id"]
    r = client.post(
        f"/api/candidates/{cid}/transfer-ownership", headers=auth,
        json={"new_owner_account_id": deactivated["account_id"]},
    )
    assert r.status_code == 400


def test_transfer_to_the_current_owner_is_400(client, auth, admin_login, new_candidate):
    cid = new_candidate()["candidate_id"]
    r = client.post(
        f"/api/candidates/{cid}/transfer-ownership", headers=auth,
        json={"new_owner_account_id": admin_login["account"]["account_id"]},
    )
    assert r.status_code == 400


def test_ownership_history_records_creation_and_transfer(
    client, auth, admin_login, make_account, new_candidate
):
    new_owner, _ = make_account(role="hr")
    cid = new_candidate()["candidate_id"]

    client.post(
        f"/api/candidates/{cid}/transfer-ownership", headers=auth,
        json={"new_owner_account_id": new_owner["account_id"], "reason": "handoff"},
    )

    history = client.get(f"/api/candidates/{cid}/ownership-history", headers=auth).json()["data"]
    assert len(history) == 2  # created + transferred
    newest, oldest = history[0], history[1]

    assert oldest["from_owner_account_id"] is None
    assert oldest["to_owner_account_id"] == admin_login["account"]["account_id"]

    assert newest["from_owner_account_id"] == admin_login["account"]["account_id"]
    assert newest["to_owner_account_id"] == new_owner["account_id"]
    assert newest["changed_by"] == admin_login["account"]["account_id"]
    assert newest["reason"] == "handoff"


# --------------------------------------------------- ownership survives re-upload


def test_reupload_does_not_change_owner(client, auth, make_account, fixed_extraction):
    owner_account, owner_headers = make_account(role="hr")
    _, reuploader_headers = make_account(role="hr")

    fixed_extraction("own-reup-v1", email="own.reup@corp.example.com")
    fixed_extraction("own-reup-v2", email="own.reup@corp.example.com", full_name="Updated Name")

    created = upload(client, owner_headers, ("v1.pdf", "own-reup-v1")).json()["data"]["created"][0]
    cid = created["candidate_id"]
    assert created["owner_account_id"] == owner_account["account_id"]

    # A DIFFERENT account re-uploads the same person's CV.
    updated = upload(client, reuploader_headers, ("v2.pdf", "own-reup-v2")).json()["data"]["updated"][0]
    assert updated["candidate_id"] == cid
    assert updated["owner_account_id"] == owner_account["account_id"], (
        "re-upload must not silently reassign ownership to whoever re-uploaded"
    )


def test_pending_upload_resolve_as_update_does_not_change_owner(
    client, auth, make_account, fixed_extraction
):
    owner_account, owner_headers = make_account(role="hr")
    _, resolver_headers = make_account(role="hr")

    base = {"email": "", "full_name": "Owner Pending Soft", "phone": "0891119999",
            "applied_position": "Backend Engineer"}
    fixed_extraction("own-pend-a", **base)
    fixed_extraction("own-pend-b", **base)

    created = upload(client, owner_headers, ("a.pdf", "own-pend-a")).json()["data"]["created"][0]
    cid = created["candidate_id"]

    review = upload(client, resolver_headers, ("b.pdf", "own-pend-b")).json()["data"]["needs_review"][0]
    resolved = client.post(
        f"/api/pending-uploads/{review['pending_upload_id']}/update", headers=resolver_headers
    ).json()["data"]

    assert resolved["candidate"]["candidate_id"] == cid
    assert resolved["candidate"]["owner_account_id"] == owner_account["account_id"]


def test_pending_upload_resolve_as_create_new_owner_is_original_uploader(
    client, auth, make_account, fixed_extraction
):
    """Owner = whoever originally uploaded the file, not whoever later clicks
    'create new' on the queue item."""
    uploader_account, uploader_headers = make_account(role="hr")
    resolver_account, resolver_headers = make_account(role="hr")

    base = {"email": "", "full_name": "Owner Pending New", "phone": "0891118888",
            "applied_position": "Backend Engineer"}
    fixed_extraction("own-new-a", **base)
    fixed_extraction("own-new-b", **base)

    upload(client, uploader_headers, ("a.pdf", "own-new-a"))
    review = upload(client, uploader_headers, ("b.pdf", "own-new-b")).json()["data"]["needs_review"][0]

    # A DIFFERENT account resolves the queue item.
    resolved = client.post(
        f"/api/pending-uploads/{review['pending_upload_id']}/create-new", headers=resolver_headers
    ).json()["data"]

    assert resolved["candidate"]["owner_account_id"] == uploader_account["account_id"]
    assert resolved["candidate"]["owner_account_id"] != resolver_account["account_id"]
