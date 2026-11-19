"""Non-Latin text survives on SQL Server: every free-text column is NVARCHAR.

SQL Server VARCHAR/TEXT store text in the database code page, so Thai, Chinese,
Arabic ... silently became '?'. These tests cover (1) the declared column types,
(2) text round-tripping through the API, and (3) the boot-time upgrade of a
database that already exists. (3) uses a scripted connection because the test
suite runs on SQLite; the statement order it asserts is the part SQL Server is
strict about.
"""
import pytest
import sqlalchemy as sa
from sqlalchemy.dialects import mssql

from app.database import Base
import app.models_db  # noqa: F401
from app import schema_compat
from app.schema_compat import ensure_unicode_text_columns

ID_LIKE = {"password_hash", "changed_by", "resolved_candidate_id", "name"}


def _mssql_type(column) -> str:
    return str(column.type.compile(dialect=mssql.dialect())).upper()


def test_only_ascii_by_design_columns_are_non_unicode_on_sql_server():
    """A new String/Text column silently reintroduces the bug, so any VARCHAR/TEXT
    column on SQL Server has to be an id/FK/hash on purpose."""
    offenders = []
    for table in Base.metadata.sorted_tables:
        for column in table.columns:
            sql_type = _mssql_type(column)
            if not sql_type.startswith(("VARCHAR", "TEXT")):
                continue
            is_id = column.name.endswith("_id") or column.foreign_keys or column.primary_key
            if not (is_id or column.name in ID_LIKE):
                offenders.append(f"{table.name}.{column.name}: {sql_type}")
    assert offenders == [], f"use Unicode/UText for: {offenders}"


def test_user_typed_columns_are_nvarchar():
    from app.models_db import Candidate, CommentLog, HRAccount

    assert _mssql_type(Candidate.__table__.c.full_name) == "NVARCHAR(MAX)"
    assert _mssql_type(Candidate.__table__.c.summary) == "NVARCHAR(MAX)"
    assert _mssql_type(CommentLog.__table__.c.comment) == "NVARCHAR(MAX)"
    assert _mssql_type(HRAccount.__table__.c.username) == "NVARCHAR(100)"
    assert _mssql_type(HRAccount.__table__.c.email) == "NVARCHAR(255)"
    assert _mssql_type(Candidate.__table__.c.email_normalized) == "NVARCHAR(255)"
    # ids stay VARCHAR: system-generated, indexed, referenced by foreign keys
    assert _mssql_type(Candidate.__table__.c.candidate_id) == "VARCHAR(7)"
    assert _mssql_type(HRAccount.__table__.c.account_id) == "VARCHAR(36)"


SAMPLES = {
    "thai": "สมชาย ใจดี",
    "chinese": "王小明 软件工程师",
    "arabic": "محمد الأحمد",
    "japanese": "山田 太郎",
    "emoji": "Alex ✅ 😀",
}


@pytest.mark.parametrize("script", SAMPLES)
def test_candidate_text_round_trips_and_is_searchable(client, auth, new_candidate, script):
    text = SAMPLES[script]
    cid = new_candidate()["candidate_id"]
    r = client.put(
        f"/api/candidates/{cid}", headers=auth,
        json={"full_name": text, "summary": f"{text} สรุป", "location": text,
              "applied_position": text},
    )
    assert r.status_code == 200, r.text
    got = client.get(f"/api/candidates/{cid}", headers=auth).json()["data"]
    assert got["full_name"] == text
    assert got["summary"] == f"{text} สรุป"
    assert got["location"] == text
    assert got["applied_position"] == text

    found = client.get("/api/candidates", headers=auth, params={"q": text}).json()["data"]
    assert cid in [row["candidate_id"] for row in found]


def test_hr_account_with_non_latin_name_and_username(client, auth):
    r = client.post(
        "/api/hr-accounts", headers=auth,
        json={"username": "สมชาย", "email": "somchai.unicode@example.com",
              "full_name": "สมชาย ใจดี", "password": "Passw0rd!unicode", "role": "hr"},
    )
    assert r.status_code == 201, r.text
    assert r.json()["data"]["username"] == "สมชาย"
    assert r.json()["data"]["full_name"] == "สมชาย ใจดี"


# ---------------------------------------------------------------- the upgrade


class _Result:
    def __init__(self, rows):
        self._rows = rows

    def mappings(self):
        return self

    def all(self):
        return self._rows


class ScriptedConnection:
    """Stands in for a SQL Server connection that still has the legacy schema.
    Catalog SELECTs are answered from `defaults` / `indexes`; everything else is
    recorded in `statements`."""

    dialect = mssql.dialect()

    def __init__(self, defaults=None, indexes=None, index_columns=None):
        self.defaults = defaults or {}          # (table, column) -> rows
        self.indexes = indexes or {}            # (table, column) -> rows
        self.index_columns = index_columns or {}  # (table, index_id) -> rows
        self.statements = []

    def execute(self, statement, params=None):
        if statement is schema_compat._DEFAULTS_SQL:
            return _Result(self.defaults.get((params["table"], params["column"]), []))
        if statement is schema_compat._INDEXES_SQL:
            return _Result(self.indexes.get((params["table"], params["column"]), []))
        if statement is schema_compat._INDEX_COLUMNS_SQL:
            return _Result(self.index_columns.get((params["table"], params["index_id"]), []))
        self.statements.append(str(statement))
        return _Result([])


class _FakeInspector:
    default_schema_name = "dbo"

    def __init__(self, type_for):
        self._type_for = type_for

    def has_table(self, name, schema=None):
        return True

    def get_columns(self, name, schema=None):
        table = Base.metadata.tables[name]
        return [{"name": c.name, "type": self._type_for(c), "nullable": c.nullable}
                for c in table.columns]


def _legacy(column):
    """What create_all left behind before the Unicode change."""
    if isinstance(column.type, sa.UnicodeText):
        return mssql.TEXT()
    if isinstance(column.type, sa.Unicode):
        return mssql.VARCHAR(column.type.length)
    return column.type


def _index(name, index_id, unique=False, constraint=False, pk=False, filtered=False):
    return {"name": name, "index_id": index_id, "is_unique": unique,
            "is_unique_constraint": constraint, "is_primary_key": pk, "has_filter": filtered}


def _member(name, included=False, descending=False):
    return {"name": name, "is_included": included, "is_descending": descending}


def _run(monkeypatch, connection, type_for=_legacy):
    monkeypatch.setattr(schema_compat.sa, "inspect", lambda _c: _FakeInspector(type_for))
    return ensure_unicode_text_columns(connection, Base.metadata)


def test_upgrade_converts_every_legacy_text_column(monkeypatch):
    connection = ScriptedConnection()
    upgraded = _run(monkeypatch, connection)

    assert "comment_logs.comment" in upgraded
    assert "candidates.full_name" in upgraded
    assert "hr_accounts.username" in upgraded
    assert "candidates.candidate_id" not in upgraded
    assert "hr_accounts.password_hash" not in upgraded
    assert all(s.startswith("ALTER TABLE dbo.") and "ALTER COLUMN" in s
               for s in connection.statements)
    by_column = {s.split("ALTER COLUMN ")[1]: s for s in connection.statements}
    assert "username NVARCHAR(100) NOT NULL" in by_column
    assert "full_name NVARCHAR(max) NOT NULL" in " ".join(by_column) or any(
        "full_name NVARCHAR(max) NOT NULL" in s for s in connection.statements)


def test_upgrade_drops_and_recreates_what_blocks_alter_column(monkeypatch):
    t = "dbo.hr_accounts"
    c = "dbo.candidates"
    connection = ScriptedConnection(
        defaults={(c, "contact_other"): [{"name": "DF_contact_other", "definition": "('')"}]},
        indexes={
            (t, "username"): [_index("ix_hr_accounts_username", 2, unique=True)],
            (t, "email"): [_index("UQ__hr_accou__email", 3, unique=True, constraint=True)],
            (c, "email_normalized"): [_index("ix_candidates_email_normalized", 5)],
        },
        index_columns={
            (t, 2): [_member("username")],
            (t, 3): [_member("email")],
            (c, 5): [_member("email_normalized")],
        },
    )
    _run(monkeypatch, connection)
    statements = connection.statements

    def block(column_fragment, drop, alter, recreate):
        i_drop = statements.index(drop)
        i_alter = next(i for i, s in enumerate(statements) if alter in s)
        i_recreate = statements.index(recreate)
        assert i_drop < i_alter < i_recreate, column_fragment

    block("username",
          "DROP INDEX ix_hr_accounts_username ON dbo.hr_accounts",
          "ALTER COLUMN username NVARCHAR(100) NOT NULL",
          "CREATE UNIQUE INDEX ix_hr_accounts_username ON dbo.hr_accounts (username)")
    block("email (unique constraint)",
          "ALTER TABLE dbo.hr_accounts DROP CONSTRAINT [UQ__hr_accou__email]",
          "ALTER COLUMN email NVARCHAR(255) NOT NULL",
          "ALTER TABLE dbo.hr_accounts ADD CONSTRAINT [UQ__hr_accou__email] UNIQUE (email)")
    block("email_normalized",
          "DROP INDEX ix_candidates_email_normalized ON dbo.candidates",
          "ALTER COLUMN email_normalized NVARCHAR(255) NULL",
          "CREATE INDEX ix_candidates_email_normalized ON dbo.candidates (email_normalized)")
    block("contact_other default",
          "ALTER TABLE dbo.candidates DROP CONSTRAINT [DF_contact_other]",
          "ALTER COLUMN contact_other NVARCHAR(max) NOT NULL",
          "ALTER TABLE dbo.candidates ADD CONSTRAINT [DF_contact_other] DEFAULT ('') FOR contact_other")


def test_upgrade_is_a_noop_when_already_unicode(monkeypatch):
    connection = ScriptedConnection()
    upgraded = _run(monkeypatch, connection,
                    type_for=lambda c: mssql.NVARCHAR() if isinstance(
                        c.type, (sa.Unicode, sa.UnicodeText)) else c.type)
    assert upgraded == []
    assert connection.statements == []


@pytest.mark.parametrize("bad, message", [
    (_index("pk_x", 1, pk=True), "primary key"),
    (_index("ix_filtered", 2, filtered=True), "filtered index"),
])
def test_upgrade_refuses_primary_key_and_filtered_indexes(monkeypatch, bad, message):
    t = "dbo.hr_accounts"
    connection = ScriptedConnection(
        indexes={(t, "username"): [bad]}, index_columns={(t, bad["index_id"]): [_member("username")]})
    with pytest.raises(RuntimeError, match=message):
        _run(monkeypatch, connection)
    assert not any("ALTER COLUMN" in s for s in connection.statements)


def test_upgrade_refuses_indexes_with_included_or_descending_columns(monkeypatch):
    t = "dbo.hr_accounts"
    connection = ScriptedConnection(
        indexes={(t, "username"): [_index("ix_wide", 2)]},
        index_columns={(t, 2): [_member("username"), _member("email", included=True)]})
    with pytest.raises(RuntimeError, match="included or descending"):
        _run(monkeypatch, connection)
    assert not any("ALTER COLUMN" in s for s in connection.statements)


def test_upgrade_ignores_non_sql_server():
    engine = sa.create_engine("sqlite:///:memory:")
    try:
        with engine.begin() as connection:
            assert ensure_unicode_text_columns(connection, Base.metadata) == []
    finally:
        engine.dispose()
