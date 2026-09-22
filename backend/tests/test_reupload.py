"""F4 - re-uploading a CV for an existing candidate updates the record.

Every test here pins exactly what each file extracts to (`fixed_extraction`), so
the assertions are about the merge policy and nothing else. "Same person" means
the same extracted email; the file bytes only decide which registered result the
extractor returns.
"""
import io

from conftest import pdf_bytes, upload

ALICE = "alice@corp.example.com"


def test_reupload_updates_instead_of_duplicating(client, auth, fixed_extraction):
    fixed_extraction("alice-v1", email=ALICE, full_name="Alice Tanaka")
    fixed_extraction("alice-v2", email=ALICE, full_name="Alice Tanaka-Smith")

    first = upload(client, auth, ("alice.pdf", "alice-v1"))
    assert first.status_code == 201, first.text
    cid = first.json()["data"]["created"][0]["candidate_id"]

    second = upload(client, auth, ("alice-updated.pdf", "alice-v2"))
    assert second.status_code == 201, second.text
    data = second.json()["data"]

    assert data["created"] == [], "a known candidate must not be created again"
    assert [c["candidate_id"] for c in data["updated"]] == [cid]
    assert data["count"] == 1
    assert data["updated"][0]["full_name"] == "Alice Tanaka-Smith"


def test_email_match_ignores_case_and_whitespace(client, auth, fixed_extraction):
    fixed_extraction("bob-v1", email="Bob.Lee@Corp.Example.com")
    fixed_extraction("bob-v2", email="  bob.lee@corp.example.com  ")

    cid = upload(client, auth, ("bob.pdf", "bob-v1")).json()["data"]["created"][0]["candidate_id"]
    second = upload(client, auth, ("bob2.pdf", "bob-v2"))

    assert [c["candidate_id"] for c in second.json()["data"]["updated"]] == [cid]


def test_a_different_email_is_a_different_person(client, auth, fixed_extraction):
    fixed_extraction("carol", email="carol@corp.example.com", full_name="Carol")
    fixed_extraction("dave", email="dave@corp.example.com", full_name="Dave")

    first = upload(client, auth, ("carol.pdf", "carol"))
    second = upload(client, auth, ("dave.pdf", "dave"))

    assert len(first.json()["data"]["created"]) == 1
    assert len(second.json()["data"]["created"]) == 1
    assert second.json()["data"]["updated"] == []


def test_reupload_preserves_hr_owned_and_identity_fields(client, auth, fixed_extraction):
    fixed_extraction("erin-v1", email="erin@corp.example.com",
                     applied_position="Backend Engineer", summary="First CV.")
    fixed_extraction("erin-v2", email="erin@corp.example.com",
                     applied_position="Something The CV Claims", summary="Second CV.")

    created = upload(client, auth, ("erin.pdf", "erin-v1")).json()["data"]["created"][0]
    cid = created["candidate_id"]

    # HR does their work on the record.
    body = client.get(f"/api/candidates/{cid}", headers=auth).json()["data"]
    body["status"] = "Interview"
    body["applied_position"] = "Staff Platform Engineer"
    body["location"] = "Phuket, Thailand"
    assert client.put(f"/api/candidates/{cid}", headers=auth, json=body).status_code == 200

    upload(client, auth, ("erin-v2.pdf", "erin-v2"))

    after = client.get(f"/api/candidates/{cid}", headers=auth).json()["data"]
    # HR-owned: untouched, even though the new CV carried a different position.
    assert after["status"] == "Interview"
    assert after["applied_position"] == "Staff Platform Engineer"
    assert after["location"] == "Phuket, Thailand"
    # Identity: untouched.
    assert after["candidate_id"] == cid
    assert after["created_at"] == created["created_at"]
    # Extraction-owned: overwritten.
    assert after["summary"] == "Second CV."


def test_empty_extracted_value_does_not_wipe_a_good_one(client, auth, fixed_extraction):
    """Extraction failing on a scanned PDF must not delete data we already had."""
    fixed_extraction("frank-v1", email="frank@corp.example.com",
                     phone="0891234567", summary="Detailed summary.")
    fixed_extraction("frank-v2", email="frank@corp.example.com",
                     phone="", summary="")

    cid = upload(client, auth, ("frank.pdf", "frank-v1")).json()["data"]["created"][0]["candidate_id"]
    upload(client, auth, ("frank-scan.pdf", "frank-v2"))

    after = client.get(f"/api/candidates/{cid}", headers=auth).json()["data"]
    assert after["phone"] == "0891234567"
    assert after["summary"] == "Detailed summary."


def test_low_confidence_still_writes_through(client, auth, fixed_extraction):
    """Team decision: it overwrites, and the change log is how HR spots a bad one."""
    fixed_extraction("gina-v1", email="gina@corp.example.com",
                     full_name="Gina Prasert", extraction_confidence=0.95)
    fixed_extraction("gina-v2", email="gina@corp.example.com",
                     full_name="G1na Prasert", extraction_confidence=0.21)

    cid = upload(client, auth, ("gina.pdf", "gina-v1")).json()["data"]["created"][0]["candidate_id"]
    upload(client, auth, ("gina-bad.pdf", "gina-v2"))

    after = client.get(f"/api/candidates/{cid}", headers=auth).json()["data"]
    assert after["full_name"] == "G1na Prasert"
    assert after["extraction_confidence"] == 0.21


def test_reupload_leaves_comment_history_fully_intact(
    client, auth, make_account, fixed_extraction
):
    """The whole point of isolating comments: candidate_id is preserved, comments
    are keyed on it, so history survives with no merge logic at all."""
    _, hr = make_account(role="hr")
    fixed_extraction("hana-v1", email="hana@corp.example.com")
    fixed_extraction("hana-v2", email="hana@corp.example.com", full_name="Hana II")

    cid = upload(client, auth, ("hana.pdf", "hana-v1")).json()["data"]["created"][0]["candidate_id"]
    for text in ("First note", "Second note"):
        r = client.post(f"/api/candidates/{cid}/comments", headers=hr, json={"comment": text})
        assert r.status_code == 201, r.text

    upload(client, auth, ("hana2.pdf", "hana-v2"))

    after = client.get(f"/api/candidates/{cid}/comments", headers=hr).json()["data"]
    assert sorted(c["comment"] for c in after) == ["First note", "Second note"]


def test_reupload_keeps_the_old_cv_as_a_version(client, auth, fixed_extraction):
    email = "ivan@corp.example.com"
    for marker in ("ivan-v1", "ivan-v2", "ivan-v3"):
        fixed_extraction(marker, email=email)

    cid = upload(client, auth, ("first.pdf", "ivan-v1")).json()["data"]["created"][0]["candidate_id"]
    upload(client, auth, ("second.pdf", "ivan-v2"))
    upload(client, auth, ("third.pdf", "ivan-v3"))

    versions = client.get(
        f"/api/candidates/{cid}/resume-versions", headers=auth
    ).json()["data"]
    assert [v["version_no"] for v in versions] == [3, 2, 1]
    assert [v["filename"] for v in versions] == ["third.pdf", "second.pdf", "first.pdf"]

    # The newest is what resume-url resolves by default...
    newest = client.get(f"/api/candidates/{cid}/resume-url", headers=auth).json()["data"]
    assert newest["version_no"] == 3
    assert newest["filename"] == "third.pdf"

    # ...and the first is still retrievable.
    first = client.get(
        f"/api/candidates/{cid}/resume-url", headers=auth, params={"version": 1}
    ).json()["data"]
    assert first["version_no"] == 1
    assert first["filename"] == "first.pdf"
    assert first["resume_url"] != newest["resume_url"]


def test_reupload_writes_a_field_level_change_log(client, auth, fixed_extraction):
    fixed_extraction("judy-v1", email="judy@corp.example.com", full_name="Judy Somsak")
    fixed_extraction("judy-v2", email="judy@corp.example.com", full_name="Judy Somsak-Lee")

    cid = upload(client, auth, ("judy.pdf", "judy-v1")).json()["data"]["created"][0]["candidate_id"]
    upload(client, auth, ("judy2.pdf", "judy-v2"))

    changes = client.get(f"/api/candidates/{cid}/changes", headers=auth).json()["data"]
    renamed = [c for c in changes
               if c["field"] == "full_name" and c["source"] == "reupload"]
    assert len(renamed) == 1
    assert renamed[0]["old_value"] == "Judy Somsak"
    assert renamed[0]["new_value"] == "Judy Somsak-Lee"
    assert renamed[0]["changed_by"], "every change is attributed to an account"


def test_two_files_same_email_in_one_request_make_one_candidate(
    client, auth, fixed_extraction
):
    """The second file must update the record the first one created."""
    fixed_extraction("kim-a", email="kim@corp.example.com", full_name="Kim First")
    fixed_extraction("kim-b", email="kim@corp.example.com", full_name="Kim Second")

    before = len(client.get("/api/candidates", headers=auth).json()["data"])

    r = client.post(
        "/api/candidates/upload",
        headers=auth,
        files=[
            ("files", ("first.pdf", io.BytesIO(pdf_bytes("kim-a")), "application/pdf")),
            ("files", ("second.pdf", io.BytesIO(pdf_bytes("kim-b")), "application/pdf")),
        ],
    )
    assert r.status_code == 201, r.text
    data = r.json()["data"]
    assert len(data["created"]) == 1
    assert len(data["updated"]) == 1
    assert data["created"][0]["candidate_id"] == data["updated"][0]["candidate_id"]
    assert data["updated"][0]["full_name"] == "Kim Second"

    after = len(client.get("/api/candidates", headers=auth).json()["data"])
    assert after == before + 1


def test_reupload_is_allowed_at_a_terminal_status(client, auth, fixed_extraction):
    """Team decision: data still updates, status is still preserved."""
    fixed_extraction("liam-v1", email="liam@corp.example.com", summary="Before hire.")
    fixed_extraction("liam-v2", email="liam@corp.example.com", summary="After hire.")

    cid = upload(client, auth, ("liam.pdf", "liam-v1")).json()["data"]["created"][0]["candidate_id"]
    body = client.get(f"/api/candidates/{cid}", headers=auth).json()["data"]
    body["status"] = "Hired"
    client.put(f"/api/candidates/{cid}", headers=auth, json=body)

    r = upload(client, auth, ("liam-post-hire.pdf", "liam-v2"))
    assert r.status_code == 201
    assert len(r.json()["data"]["updated"]) == 1

    after = client.get(f"/api/candidates/{cid}", headers=auth).json()["data"]
    assert after["status"] == "Hired"
    assert after["summary"] == "After hire."


def test_extraction_failure_leaves_the_existing_record_untouched(
    client, auth, fixed_extraction
):
    fixed_extraction("mia-v1", email="mia@corp.example.com", full_name="Mia Chen")
    fixed_extraction.fails("mia-broken", "scanned PDF, no text layer")
    fixed_extraction("healthy", email="healthy@corp.example.com")

    original = upload(client, auth, ("mia.pdf", "mia-v1")).json()["data"]["created"][0]
    cid = original["candidate_id"]

    # One good file alongside the broken one: the batch still succeeds, and the
    # broken file fails only its own entry.
    r = upload(client, auth, ("mia-broken.pdf", "mia-broken"), ("fine.pdf", "healthy"))
    assert r.status_code == 201, r.text
    data = r.json()["data"]
    assert len(data["failed"]) == 1
    assert "scanned PDF" in data["failed"][0]["error"]
    assert data["updated"] == [], "a failed extraction must not update anything"
    assert len(data["created"]) == 1

    after = client.get(f"/api/candidates/{cid}", headers=auth).json()["data"]
    for field in ("full_name", "email", "phone", "summary", "status",
                  "applied_position", "location", "created_at", "updated_at",
                  "resume_filename", "extraction_confidence"):
        assert after[field] == original[field], f"{field} changed on a failed upload"


def test_every_file_failing_is_a_400(client, auth, fixed_extraction):
    fixed_extraction.fails("all-broken", "unreadable")
    r = upload(client, auth, ("broken.pdf", "all-broken"))
    assert r.status_code == 400
    assert "unreadable" in r.json()["error"]


def test_soft_duplicate_stops_for_review_instead_of_guessing(
    client, auth, fixed_extraction
):
    """No exact email match but a phone/name hint -> do NOT auto-create and do
    NOT auto-merge. Stop and let a human decide (round-4 rule)."""
    for marker in ("somchai-1", "somchai-2"):
        fixed_extraction(
            marker,
            email="",
            full_name="Somchai Jaidee",
            phone="0891112223",
            applied_position="Backend Engineer",
        )

    first = upload(client, auth, ("one.pdf", "somchai-1"))
    second = upload(client, auth, ("two.pdf", "somchai-2"))
    assert first.status_code == second.status_code == 201

    # The first has nothing to match against, so it is created outright.
    first_id = first.json()["data"]["created"][0]["candidate_id"]

    # The second looks like the first - it must not silently become either a
    # second record or an overwrite.
    data = second.json()["data"]
    assert data["created"] == []
    assert data["updated"] == []
    assert data["count"] == 0
    assert len(data["needs_review"]) == 1

    review = data["needs_review"][0]
    assert review["filename"] == "two.pdf"
    assert [c["candidate_id"] for c in review["duplicate_candidates"]] == [first_id]
    assert review["extracted_preview"]["full_name"] == "Somchai Jaidee"


def test_no_match_at_all_still_auto_creates(client, auth, fixed_extraction):
    """The stop-and-ask rule must not make ordinary new candidates slower."""
    fixed_extraction("nobody-like-them", email="unique.person@corp.example.com",
                     full_name="Totally Unique Person", phone="0870000001")

    r = upload(client, auth, ("new.pdf", "nobody-like-them"))
    assert r.status_code == 201
    data = r.json()["data"]
    assert len(data["created"]) == 1
    assert data["needs_review"] == []
    assert data["created"][0]["possible_duplicate_of"] == []


def test_mock_extractor_is_a_pure_function_of_the_file(client, auth):
    """Guards the property every test above leans on. If this breaks, the mock
    started generating fresh people for the same CV again and F4 is untestable."""
    from app.extraction import extract_candidate

    content = pdf_bytes("purity-check")
    first = extract_candidate(content, filename="a.pdf")
    second = extract_candidate(content, filename="b.pdf")
    assert first == second

    different = extract_candidate(pdf_bytes("purity-check-2"), filename="a.pdf")
    assert different["email"] != first["email"]
