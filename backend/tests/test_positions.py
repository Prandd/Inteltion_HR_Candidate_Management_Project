"""Positions - reverse-engineered from frontend/dashboard's Positions,
PositionDetail and PositionRequirements pages, which call GET/POST
/positions against a resource that never existed on this branch before.
No prior contract to match beyond what those three pages actually read
and send - see app/routers/positions.py.
"""


def test_create_and_list_position(client, auth):
    # A deliberately unique title: the mock extractor's own position list
    # includes "Backend Engineer" among its choices, and this suite shares
    # one database across tests, so a common title risks colliding with
    # candidates other tests created - see test_candidate_count_... below,
    # which tests that exact matching behavior on purpose instead.
    title = "Backend Engineer - Create And List Test"
    r = client.post(
        "/api/positions", headers=auth,
        json={
            "title": title,
            "department": "Engineering",
            "description": "Build the API.",
            "location": "Bangkok, Thailand",
            "skills": ["Python", "FastAPI"],
        },
    )
    assert r.status_code == 201, r.text
    created = r.json()["data"]
    assert created["title"] == title
    assert created["status"] == "Open"  # always starts Open; not client-settable
    assert created["skills"] == ["Python", "FastAPI"]
    assert created["candidate_count"] == 0
    assert "id" in created  # the frontend's field name, not position_id

    listed = client.get("/api/positions", headers=auth).json()["data"]
    assert any(p["id"] == created["id"] for p in listed)
    # The list shape omits description/skills (PositionSummaryOut), unlike
    # the detail shape (PositionOut) - matches Positions.tsx's Position
    # interface, which never declares either field.
    summary = next(p for p in listed if p["id"] == created["id"])
    assert "description" not in summary
    assert "skills" not in summary


def test_get_one_position(client, auth):
    created = client.post(
        "/api/positions", headers=auth,
        json={"title": "Data Engineer"},
    ).json()["data"]

    r = client.get(f"/api/positions/{created['id']}", headers=auth)
    assert r.status_code == 200
    assert r.json()["data"]["title"] == "Data Engineer"
    assert r.json()["data"]["department"] == ""  # NULL RULE - "" not omitted


def test_unknown_position_is_404(client, auth):
    r = client.get("/api/positions/does-not-exist", headers=auth)
    assert r.status_code == 404


def test_candidate_count_matches_applied_position_by_name(
    client, auth, new_candidate
):
    """candidate_count has no real foreign key to lean on - applied_position
    is free text HR assigns after upload - so this is a name match, and the
    test exists specifically to pin that behavior down."""
    position = client.post(
        "/api/positions", headers=auth,
        json={"title": "QA Engineer - Candidate Count Test"},
    ).json()["data"]

    assert client.get(f"/api/positions/{position['id']}", headers=auth).json()["data"]["candidate_count"] == 0

    cid = new_candidate()["candidate_id"]
    body = client.get(f"/api/candidates/{cid}", headers=auth).json()["data"]
    body["applied_position"] = "QA Engineer - Candidate Count Test"
    client.put(f"/api/candidates/{cid}", headers=auth, json=body)

    updated = client.get(f"/api/positions/{position['id']}", headers=auth).json()["data"]
    assert updated["candidate_count"] == 1

    listed = client.get("/api/positions", headers=auth).json()["data"]
    assert next(p for p in listed if p["id"] == position["id"])["candidate_count"] == 1


def test_positions_require_auth(client):
    assert client.get("/api/positions").status_code == 401
    assert client.post("/api/positions", json={"title": "x"}).status_code == 401
