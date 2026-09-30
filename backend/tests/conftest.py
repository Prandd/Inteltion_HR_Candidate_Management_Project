"""Test isolation + shared fixtures.

The env block runs BEFORE any `app.*` import (pytest loads conftest first), so
`Settings()` in app/config.py picks these up instead of the real values. Without
it, `pytest` writes into the dev database: it leaves rows behind, renames seeded
candidates, and - worst - the high candidate_ids the delete tests insert become
the new max, so the next real upload jumps from 0000013 to 8000002.
"""
import io
import itertools
import os
import tempfile
import uuid
from unittest import mock

_tmp = tempfile.mkdtemp(prefix="inteltion-tests-")

os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["UPLOAD_DIR"] = os.path.join(_tmp, "uploads")
# Force local-disk storage for the whole suite, overriding whatever
# backend/.env has set. Without this, a real backend/.env pointed at Azure
# (as it has been all along this round) makes every pytest run write real
# files to the live storage account over the network - slower, costs money
# (however little), and leaves fixture01234.pdf-style junk behind in
# production storage forever. Tests exercise the Azure path deliberately and
# separately (a live uvicorn boot against the real account), never through
# this suite.
os.environ["AZURE_STORAGE_CONNECTION_STRING"] = ""
# Lower bcrypt cost for the whole suite - purely for test speed (rounds=12 is
# ~150-250ms per hash; rounds=4 is single-digit ms), NOT a security setting.
# Real accounts (seed admin, everyone created through POST /api/hr-accounts
# outside tests) always get the real default of 12 from config.py.
#
# This also shrinks - but does not eliminate - an intermittent failure this
# round's testing surfaced: with round-5 adding many more back-to-back
# make_account() calls per run, roughly 1-2% of create-account-then-login
# round trips fail with a wrong-password 401 even though the password is
# correct. Isolated proof this is not an app bug: 500 sequential
# hash_password()/verify_password() calls with no web/DB layer involved at
# all had ZERO failures; the failures only appear once FastAPI dispatches the
# sync endpoints through its thread pool, run under CPU-intensive bcrypt work,
# and - critically - a failing case does NOT reproduce on an immediate
# re-check with the exact same stored hash and password. That non-determinism
# on an identical repeat computation is not something a logic bug produces;
# it matches this machine's independently-confirmed RAM instability (see
# machine-has-memory-corruption in project memory) now shown to affect
# CPU-bound crypto work, not just process crashes. If a test fails here with
# a plausible-looking wrong-password 401, re-run before assuming a regression.
os.environ["BCRYPT_ROUNDS"] = "4"
os.environ["SEED_ADMIN_USERNAME"] = "admin"
os.environ["SEED_ADMIN_PASSWORD"] = "test-admin-pw"
os.environ["SEED_ADMIN_EMAIL"] = "admin@test.local"
os.environ["SEED_ADMIN_FULL_NAME"] = "Test Admin"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.security import login_limiter  # noqa: E402

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "test-admin-pw"


@pytest.fixture(scope="session")
def client():
    # `with` runs the lifespan (table create + seed + status assertion).
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def _clear_login_limiter():
    """The limiter is process-global and survives between tests. Clearing it
    keeps one test's deliberate failures from locking out the next one."""
    login_limiter._failures.clear()
    yield
    login_limiter._failures.clear()


def login(client, username: str, password: str) -> dict:
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["data"]


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def admin_login(client):
    r = client.post(
        "/api/auth/login",
        json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
    )
    assert r.status_code == 200, r.text
    return r.json()["data"]


@pytest.fixture(scope="session")
def auth(admin_login):
    """Authorization header for the seeded admin."""
    return bearer(admin_login["access_token"])


@pytest.fixture
def make_account(client, auth):
    """Factory: create an HR account and return (account, headers)."""

    def _make(role: str = "hr", password: str = "correct-horse-1", **overrides):
        suffix = uuid.uuid4().hex[:8]
        body = {
            "username": overrides.get("username", f"user_{suffix}"),
            "email": overrides.get("email", f"user_{suffix}@test.local"),
            "full_name": overrides.get("full_name", f"User {suffix}"),
            "password": password,
            "role": role,
        }
        r = client.post("/api/hr-accounts", headers=auth, json=body)
        assert r.status_code == 201, r.text
        account = r.json()["data"]
        data = login(client, body["username"], password)
        return account, bearer(data["access_token"])

    return _make


# --------------------------------------------------------------- upload helpers

_PREFIX = b"%PDF-1.4 |"
_SUFFIX = b"| fake resume bytes"


def pdf_bytes(marker: str) -> bytes:
    """Fake CV content carrying a readable marker.

    Two properties the tests depend on: different markers are different bytes,
    and the marker can be read back out of the bytes (see `marker_of`), which is
    what lets `fixed_extraction` decide exactly what a given file extracts to.
    """
    return _PREFIX + marker.encode("utf-8") + _SUFFIX


def marker_of(file_bytes: bytes) -> str:
    parts = file_bytes.split(b"|")
    return parts[1].decode("utf-8") if len(parts) >= 3 else ""


def upload(client, headers, *files):
    """files: (filename, marker) pairs -> POST /api/candidates/upload."""
    payload = [
        ("files", (name, io.BytesIO(pdf_bytes(marker)), "application/pdf"))
        for name, marker in files
    ]
    return client.post("/api/candidates/upload", headers=headers, files=payload)


_fixture_counter = itertools.count(1)


@pytest.fixture
def new_candidate(client, auth):
    """Upload one CV for a guaranteed-new person and return the created payload.

    The identity is generated from a counter, not by the mock extractor. The
    mock only has ~8000 possible emails, a full run does ~45 uploads, and F4
    treats a repeated email as the SAME person - so leaning on the mock made
    roughly one run in eight fail with `created == []` while the product was
    behaving perfectly correctly. Birthday problem, not a bug.

    The patch is a context manager around the upload only, so a test that also
    uses `fixed_extraction` keeps its own registrations afterwards.
    """

    def _new(marker: str | None = None, **overrides) -> dict:
        import app.routers.candidates as candidates_router

        n = next(_fixture_counter)
        spec = candidate_fields(
            full_name=f"Fixture Person {n:03d}",
            email=f"fixture{n:03d}@fixture.test",
            phone=f"08{n:08d}",
            **overrides,
        )
        with mock.patch.object(
            candidates_router, "extract_candidate",
            lambda file_bytes, filename=None: dict(spec),
        ):
            r = upload(client, auth, (f"fixture{n:03d}.pdf", marker or f"fixture-{n}"))

        assert r.status_code == 201, r.text
        created = r.json()["data"]["created"]
        assert len(created) == 1, r.text
        return created[0]

    return _new


# ----------------------------------------------------------- fixed extraction
#
# The mock extractor is deterministic, but its output is still *generated* - a
# test that asserted on the name or email it happens to produce would be
# asserting on fixture tables it does not own. Anything that cares what a CV
# extracts to registers the exact dict here instead.

_identity_counter = itertools.count(1)


def candidate_fields(**overrides) -> dict:
    """A complete, schema-valid extraction result with explicit values.

    The three identity fields default to something UNIQUE per call. They used
    to be fixed strings, which was fine while a soft duplicate only populated a
    read-only hint - but now a shared phone or name diverts the whole upload
    into the needs-review queue, so every fixture candidate would have looked
    like a duplicate of every other one. A test that WANTS a collision passes
    the same phone/full_name explicitly.
    """
    n = next(_identity_counter)
    fields = {
        "full_name": f"Fixture Candidate {n:04d}",
        "email": f"fixture.candidate{n:04d}@example.com",
        "phone": f"081{n:07d}",
        "location": "",
        "applied_position": "",
        "summary": "A summary.",
        "skills": [{"skill": "Python", "tools": ["FastAPI"]}],
        "experience": [],
        "experience_total": 3.0,
        "current_salary": 50000.0,
        "expected_salary": 70000.0,
        "education": [],
        "extraction_confidence": 0.9,
        "raw_text_snippet": "raw text",
        "status": "New",
    }
    fields.update(overrides)
    return fields


class _Boom:
    """Registered in place of a dict to make that file's extraction fail."""

    def __init__(self, message: str) -> None:
        self.message = message


@pytest.fixture
def fixed_extraction(monkeypatch):
    """Pin exactly what each uploaded file extracts to.

        def test_x(client, auth, fixed_extraction):
            fixed_extraction("alice", email="alice@corp.com", full_name="Alice")
            upload(client, auth, ("cv.pdf", "alice"))

    An unregistered marker raises rather than falling back, so a typo shows up
    as a failing test instead of as data nobody chose.
    """
    import app.routers.candidates as candidates_router

    table: dict[str, object] = {}

    def _extract(file_bytes: bytes, filename: str | None = None) -> dict:
        marker = marker_of(file_bytes)
        if marker not in table:
            raise AssertionError(
                f"fixed_extraction: no result registered for marker {marker!r} "
                f"(registered: {sorted(table)})"
            )
        spec = table[marker]
        if isinstance(spec, _Boom):
            raise RuntimeError(spec.message)
        return dict(spec)

    monkeypatch.setattr(candidates_router, "extract_candidate", _extract)

    def _register(marker: str, **fields) -> str:
        # Defaults are filled in HERE, once, so re-uploading the same marker
        # extracts to exactly the same person every time. Resolving them per
        # extraction call would hand the same file a new identity on each
        # upload, which is the bug the content-hash mock exists to avoid.
        table[marker] = candidate_fields(**fields)
        return marker

    def _register_failure(marker: str, message: str) -> str:
        table[marker] = _Boom(message)
        return marker

    _register.fails = _register_failure
    return _register
