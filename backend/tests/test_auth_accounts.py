"""F2 - DB-backed accounts, real login, role gating.

Adversarial cases, not just happy paths: deactivation mid-token, username
enumeration, and non-admins reaching the account endpoints.
"""
from conftest import ADMIN_PASSWORD, ADMIN_USERNAME, bearer, login

from app.config import settings


def test_login_returns_the_account_alongside_the_token(client):
    data = login(client, ADMIN_USERNAME, ADMIN_PASSWORD)
    assert data["token_type"] == "bearer"
    account = data["account"]
    assert account["username"] == ADMIN_USERNAME
    assert account["role"] == "admin"
    assert account["is_active"] is True
    # Nothing password-shaped may ride along in the login payload.
    assert "password" not in str(data).lower()
    assert "$2b$" not in str(data)


def test_me_returns_the_caller(client, make_account):
    account, headers = make_account(role="hr")
    r = client.get("/api/auth/me", headers=headers)
    assert r.status_code == 200
    me = r.json()["data"]
    assert me["account_id"] == account["account_id"]
    assert me["role"] == "hr"


def test_account_listing_never_exposes_the_password_hash(client, auth, make_account):
    make_account(role="hr")
    r = client.get("/api/hr-accounts", headers=auth)
    assert r.status_code == 200
    body = r.text.lower()
    assert "password_hash" not in body
    assert "$2b$" not in body  # a bcrypt hash would start like this


def test_deactivated_account_is_rejected_on_the_next_request(client, auth, make_account):
    """Not when the token expires - up to 8 hours later."""
    account, headers = make_account(role="hr")
    assert client.get("/api/candidates", headers=headers).status_code == 200

    r = client.delete(f"/api/hr-accounts/{account['account_id']}", headers=auth)
    assert r.status_code == 200
    assert r.json()["data"]["is_active"] is False

    after = client.get("/api/candidates", headers=headers)
    assert after.status_code == 401


def test_delete_is_a_soft_delete(client, auth, make_account):
    account, _ = make_account(role="hr")
    client.delete(f"/api/hr-accounts/{account['account_id']}", headers=auth)

    rows = client.get("/api/hr-accounts", headers=auth).json()["data"]
    match = [a for a in rows if a["account_id"] == account["account_id"]]
    assert match, "the account row must survive - comment history references it"
    assert match[0]["is_active"] is False


def test_wrong_password_is_indistinguishable_from_unknown_user(client):
    unknown = client.post(
        "/api/auth/login",
        json={"username": "nobody-at-all", "password": "whatever-1"},
    )
    wrong = client.post(
        "/api/auth/login",
        json={"username": ADMIN_USERNAME, "password": "definitely-wrong"},
    )
    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json()["error"] == wrong.json()["error"]


def test_deactivated_account_login_is_also_indistinguishable(client, auth, make_account):
    account, _ = make_account(role="hr", password="correct-horse-1")
    client.delete(f"/api/hr-accounts/{account['account_id']}", headers=auth)

    r = client.post(
        "/api/auth/login",
        json={"username": account["username"], "password": "correct-horse-1"},
    )
    assert r.status_code == 401
    unknown = client.post(
        "/api/auth/login", json={"username": "nobody-at-all", "password": "whatever-1"}
    )
    assert r.json()["error"] == unknown.json()["error"]


def test_login_is_rate_limited_per_username(client, make_account):
    account, _ = make_account(role="hr", password="correct-horse-1")
    username = account["username"]

    for _ in range(settings.login_max_failures):
        r = client.post("/api/auth/login", json={"username": username, "password": "x"})
        assert r.status_code == 401

    blocked = client.post(
        "/api/auth/login", json={"username": username, "password": "correct-horse-1"}
    )
    assert blocked.status_code == 429
    assert blocked.headers.get("Retry-After")


def test_non_admin_cannot_reach_account_management(client, make_account):
    _, hr_headers = make_account(role="hr")
    assert client.get("/api/hr-accounts", headers=hr_headers).status_code == 403
    created = client.post(
        "/api/hr-accounts",
        headers=hr_headers,
        json={"username": "sneaky", "email": "s@test.local",
              "full_name": "S", "password": "correct-horse-1", "role": "admin"},
    )
    assert created.status_code == 403


def test_account_options_lists_active_accounts_for_any_logged_in_role(
    client, auth, make_account
):
    """GET /api/hr-accounts/options feeds UI pickers (owner filter,
    ownership transfer) that need the full roster, not just admin-only
    /api/hr-accounts - any logged-in role should be able to read it."""
    hr_account, hr_headers = make_account(role="hr")

    r = client.get("/api/hr-accounts/options", headers=hr_headers)
    assert r.status_code == 200
    accounts = r.json()["data"]
    assert any(a["account_id"] == hr_account["account_id"] for a in accounts)
    assert all(set(a.keys()) == {"account_id", "full_name", "username"} for a in accounts)

    deactivated_id = hr_account["account_id"]
    client.delete(f"/api/hr-accounts/{deactivated_id}", headers=auth)
    r2 = client.get("/api/hr-accounts/options", headers=auth)
    assert all(a["account_id"] != deactivated_id for a in r2.json()["data"])


def test_duplicate_username_and_email_are_rejected(client, auth, make_account):
    account, _ = make_account(role="hr")
    dup_username = client.post(
        "/api/hr-accounts", headers=auth,
        json={"username": account["username"], "email": "other@test.local",
              "full_name": "Other", "password": "correct-horse-1", "role": "hr"},
    )
    assert dup_username.status_code == 409

    dup_email = client.post(
        "/api/hr-accounts", headers=auth,
        json={"username": "someone-else", "email": account["email"],
              "full_name": "Other", "password": "correct-horse-1", "role": "hr"},
    )
    assert dup_email.status_code == 409


def test_short_password_is_rejected(client, auth):
    r = client.post(
        "/api/hr-accounts", headers=auth,
        json={"username": "shorty", "email": "shorty@test.local",
              "full_name": "Shorty", "password": "abc", "role": "hr"},
    )
    assert r.status_code == 400


def test_change_password_requires_the_old_one(client, make_account):
    _, headers = make_account(role="hr", password="correct-horse-1")

    wrong = client.post(
        "/api/auth/change-password", headers=headers,
        json={"old_password": "not-it", "new_password": "brand-new-pw-2"},
    )
    assert wrong.status_code == 400

    ok = client.post(
        "/api/auth/change-password", headers=headers,
        json={"old_password": "correct-horse-1", "new_password": "brand-new-pw-2"},
    )
    assert ok.status_code == 200


def test_changed_password_actually_takes_effect(client, make_account):
    account, headers = make_account(role="hr", password="correct-horse-1")
    client.post(
        "/api/auth/change-password", headers=headers,
        json={"old_password": "correct-horse-1", "new_password": "brand-new-pw-2"},
    )

    old = client.post(
        "/api/auth/login",
        json={"username": account["username"], "password": "correct-horse-1"},
    )
    assert old.status_code == 401
    new = login(client, account["username"], "brand-new-pw-2")
    assert new["account"]["account_id"] == account["account_id"]


def test_admin_reset_password_then_login(client, auth, make_account):
    account, _ = make_account(role="hr")
    r = client.post(
        f"/api/hr-accounts/{account['account_id']}/reset-password",
        headers=auth, json={"new_password": "temp-password-9"},
    )
    assert r.status_code == 200
    data = login(client, account["username"], "temp-password-9")
    assert data["account"]["username"] == account["username"]


def test_admin_cannot_deactivate_their_own_account(client, auth, admin_login):
    account_id = admin_login["account"]["account_id"]
    r = client.delete(f"/api/hr-accounts/{account_id}", headers=auth)
    assert r.status_code == 400


def test_garbage_token_is_401_not_500(client):
    r = client.get("/api/candidates", headers=bearer("not-a-jwt"))
    assert r.status_code == 401
