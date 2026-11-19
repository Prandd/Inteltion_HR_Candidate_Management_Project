"""Any number of named contacts per candidate (`contacts`), replacing the single
free-text `contact_other`."""
import json

import pytest
import sqlalchemy as sa

from app.schema_compat import backfill_contacts_from_other, ensure_contacts_column
from app.services import HR_OWNED

LINE = {"label": "LINE", "value": "candidate.line"}
LINKEDIN = {"label": "LinkedIn", "value": "https://www.linkedin.com/in/candidate"}


def _put(client, auth, cid, **body):
    return client.put(f"/api/candidates/{cid}", headers=auth, json=body)


def _get(client, auth, cid):
    return client.get(f"/api/candidates/{cid}", headers=auth).json()["data"]


def test_new_candidate_has_no_contacts_and_no_legacy_field(client, auth, new_candidate):
    candidate = _get(client, auth, new_candidate()["candidate_id"])
    assert candidate["contacts"] == []
    assert "contact_other" not in candidate


def test_contacts_persist_in_order_and_are_audited(client, auth, new_candidate):
    candidate = new_candidate()
    cid = candidate["candidate_id"]
    response = _put(client, auth, cid, contacts=[LINE, LINKEDIN])
    assert response.status_code == 200, response.text
    assert response.json()["data"]["contacts"] == [LINE, LINKEDIN]

    after = _get(client, auth, cid)
    assert after["contacts"] == [LINE, LINKEDIN]
    # the rest of the record is untouched
    assert after["email"] == candidate["email"]
    assert after["phone"] == candidate["phone"]
    assert after["education"] == candidate["education"]

    changes = client.get(f"/api/candidates/{cid}/changes", headers=auth).json()["data"]
    assert any(c["field"] == "contacts" and "candidate.line" in c["new_value"] for c in changes)


def test_contacts_can_grow_shrink_and_be_cleared(client, auth, new_candidate):
    cid = new_candidate()["candidate_id"]
    many = [{"label": f"Contact {n}", "value": f"value-{n}"} for n in range(12)]
    assert _put(client, auth, cid, contacts=many).status_code == 200
    assert _get(client, auth, cid)["contacts"] == many

    assert _put(client, auth, cid, contacts=many[:3]).status_code == 200
    assert _get(client, auth, cid)["contacts"] == many[:3]

    assert _put(client, auth, cid, contacts=[]).status_code == 200
    assert _get(client, auth, cid)["contacts"] == []


def test_contacts_are_trimmed_and_unicode_safe(client, auth, new_candidate):
    cid = new_candidate()["candidate_id"]
    sent = [{"label": "  ไลน์  ", "value": "  somchai.line  "},
            {"label": "微信", "value": "wxid_王小明"}]
    assert _put(client, auth, cid, contacts=sent).status_code == 200
    assert _get(client, auth, cid)["contacts"] == [
        {"label": "ไลน์", "value": "somchai.line"},
        {"label": "微信", "value": "wxid_王小明"},
    ]


def test_updating_other_fields_does_not_wipe_contacts(client, auth, new_candidate):
    cid = new_candidate()["candidate_id"]
    _put(client, auth, cid, contacts=[LINE])
    assert _put(client, auth, cid, phone="0812345678").status_code == 200
    assert _get(client, auth, cid)["contacts"] == [LINE]


@pytest.mark.parametrize("contacts", [
    [{"label": "", "value": "x"}],
    [{"label": "LINE", "value": ""}],
    [{"label": "   ", "value": "x"}],
    [{"label": "L" * 51, "value": "x"}],
    [{"label": "LINE", "value": "v" * 501}],
    [{"label": f"c{n}", "value": "x"} for n in range(51)],
])
def test_invalid_contacts_are_rejected_and_nothing_is_saved(client, auth, new_candidate, contacts):
    cid = new_candidate()["candidate_id"]
    _put(client, auth, cid, contacts=[LINE])
    response = _put(client, auth, cid, contacts=contacts)
    assert response.status_code == 400
    assert _get(client, auth, cid)["contacts"] == [LINE]


def test_exactly_the_limits_are_accepted(client, auth, new_candidate):
    cid = new_candidate()["candidate_id"]
    contacts = [{"label": "L" * 50, "value": "v" * 500}] + [
        {"label": f"c{n}", "value": "x"} for n in range(49)
    ]
    assert len(contacts) == 50
    assert _put(client, auth, cid, contacts=contacts).status_code == 200


def test_cv_replacement_keeps_manually_entered_contacts(client, auth, fixed_extraction):
    from conftest import upload
    fixed_extraction('contacts-before', email='contacts-test@example.com')
    fixed_extraction('contacts-after', email='contacts-test@example.com')
    first = upload(client, auth, ('before.pdf', 'contacts-before')).json()['data']['created'][0]
    cid = first['candidate_id']
    _put(client, auth, cid, contacts=[LINE, LINKEDIN])
    review = upload(client, auth, ('after.pdf', 'contacts-after')).json()['data']['needs_review'][0]
    response = client.post(f"/api/pending-uploads/{review['pending_upload_id']}/update", headers=auth)
    assert response.status_code == 200, response.text
    assert response.json()['data']['candidate']['contacts'] == [LINE, LINKEDIN]


def test_contacts_are_hr_owned_so_uploads_never_overwrite_them():
    assert "contacts" in HR_OWNED


# ---------------------------------------------------- moving the old free text


def _legacy_engine(rows):
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(sa.text(
            "CREATE TABLE candidates (candidate_id VARCHAR(7) PRIMARY KEY, "
            "contact_other TEXT NOT NULL DEFAULT '', contacts JSON NOT NULL DEFAULT '[]')"))
        for candidate_id, other, contacts in rows:
            connection.execute(
                sa.text("INSERT INTO candidates VALUES (:i, :o, :c)"),
                {"i": candidate_id, "o": other, "c": json.dumps(contacts)})
    return engine


def _contacts(engine):
    with engine.connect() as connection:
        return {r[0]: (json.loads(r[1]), r[2]) for r in connection.execute(
            sa.text("SELECT candidate_id, contacts, contact_other FROM candidates"))}


def test_old_other_contact_text_moves_into_contacts_once():
    engine = _legacy_engine([
        ("0000001", "LINE: old.line\nLinkedIn: https://x.test/in/a", []),
        ("0000002", "", []),
        ("0000003", "   ", []),
        ("0000004", "ไลน์: somchai", []),
        ("0000005", "extra", [LINE]),
    ])
    try:
        with engine.begin() as connection:
            assert backfill_contacts_from_other(connection) == 4  # blank-only rows are cleared too
        result = _contacts(engine)
        assert result["0000001"] == ([{"label": "Other", "value": "LINE: old.line\nLinkedIn: https://x.test/in/a"}], "")
        assert result["0000002"] == ([], "")
        assert result["0000003"] == ([], "")
        assert result["0000004"] == ([{"label": "Other", "value": "ไลน์: somchai"}], "")
        assert result["0000005"] == ([LINE, {"label": "Other", "value": "extra"}], "")

        # second run: nothing left to move, so a contact HR deletes stays deleted
        with engine.begin() as connection:
            assert backfill_contacts_from_other(connection) == 0
        assert _contacts(engine) == result
    finally:
        engine.dispose()


def test_backfill_is_a_noop_when_the_columns_are_missing():
    engine = sa.create_engine("sqlite:///:memory:")
    try:
        with engine.begin() as connection:
            connection.execute(sa.text("CREATE TABLE candidates (candidate_id VARCHAR(7) PRIMARY KEY)"))
            assert backfill_contacts_from_other(connection) == 0
    finally:
        engine.dispose()


def test_contacts_column_is_added_to_an_existing_table_and_repeatable():
    engine = sa.create_engine("sqlite:///:memory:")
    try:
        with engine.begin() as connection:
            connection.execute(sa.text("CREATE TABLE candidates (candidate_id VARCHAR(7) PRIMARY KEY)"))
            connection.execute(sa.text("INSERT INTO candidates (candidate_id) VALUES ('0000001')"))
            assert ensure_contacts_column(connection) is True
            assert ensure_contacts_column(connection) is False
        with engine.connect() as connection:
            assert json.loads(connection.execute(sa.text("SELECT contacts FROM candidates")).scalar_one()) == []
    finally:
        engine.dispose()


def test_contact_other_column_upgrade_backfills_existing_rows_and_is_repeatable(monkeypatch):
    from app import main
    engine = sa.create_engine('sqlite:///:memory:')
    try:
        with engine.begin() as connection:
            connection.execute(sa.text('CREATE TABLE candidates (candidate_id VARCHAR(7) PRIMARY KEY)'))
            connection.execute(sa.text("INSERT INTO candidates (candidate_id) VALUES ('0000001')"))
        monkeypatch.setattr(main, 'engine', engine)
        main._ensure_contact_other_column()
        main._ensure_contact_other_column()
        with engine.connect() as connection:
            assert connection.execute(sa.text('SELECT contact_other FROM candidates')).scalar_one() == ''
    finally:
        engine.dispose()
