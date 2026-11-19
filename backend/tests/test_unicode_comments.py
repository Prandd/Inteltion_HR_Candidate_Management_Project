from unittest.mock import MagicMock, patch

import pytest
import sqlalchemy as sa
from sqlalchemy.dialects import mssql, sqlite

from app.models_db import CommentLog
from app.schema_compat import ensure_unicode_comment_column


def test_sql_server_comment_storage_is_nvarchar_max():
    column_type = CommentLog.__table__.c.comment.type
    assert str(column_type.compile(dialect=mssql.dialect())).upper() == 'NVARCHAR(MAX)'
    assert str(column_type.compile(dialect=sqlite.dialect())).upper() == 'TEXT'
    statement = sa.insert(CommentLog).values(comment_id='unicode-ddl-test', comment='ทดสอบความคิดเห็นภาษาไทย')
    sql = str(statement.compile(dialect=mssql.dialect(), compile_kwargs={'literal_binds': True}))
    assert "N'ทดสอบความคิดเห็นภาษาไทย'" in sql


def test_thai_comment_create_read_and_edit(client, auth, new_candidate):
    cid = new_candidate()['candidate_id']
    endpoint = f'/api/candidates/{cid}/comments'
    text = 'ผู้สมัครมีทักษะดี เหมาะกับตำแหน่งนี้\nนัดสัมภาษณ์รอบถัดไปได้ครับ'
    created = client.post(endpoint, headers=auth, json={'comment': text})
    assert created.status_code == 201, created.text
    comment = created.json()['data']
    assert comment['comment'] == text
    listed = client.get(endpoint, headers=auth).json()['data']
    assert next(item for item in listed if item['comment_id'] == comment['comment_id'])['comment'] == text
    edited_text = 'แก้ไข: ผ่านการสัมภาษณ์แล้ว — English + ภาษาไทย ✅'
    edited = client.put(f"/api/comments/{comment['comment_id']}", headers=auth, json={'comment': edited_text})
    assert edited.status_code == 200, edited.text
    assert edited.json()['data']['comment'] == edited_text
    assert edited.json()['data']['is_edited'] is True
    listed = client.get(endpoint, headers=auth).json()['data']
    assert next(item for item in listed if item['comment_id'] == comment['comment_id'])['comment'] == edited_text


def test_legacy_sql_server_column_is_upgraded_and_repeat_is_noop():
    connection = MagicMock()
    connection.dialect = mssql.dialect()
    inspector = MagicMock()
    inspector.default_schema_name = 'dbo'
    inspector.get_columns.side_effect = [
        [{'name': 'comment', 'type': sa.Text(), 'nullable': False}],
        [{'name': 'comment', 'type': mssql.NVARCHAR(), 'nullable': False}],
    ]
    with patch('app.schema_compat.sa.inspect', return_value=inspector):
        assert ensure_unicode_comment_column(connection) is True
        assert ensure_unicode_comment_column(connection) is False
    connection.execute.assert_called_once()
    assert str(connection.execute.call_args.args[0]) == 'ALTER TABLE dbo.comment_logs ALTER COLUMN comment NVARCHAR(MAX) NOT NULL'


@pytest.mark.parametrize('column_type', [mssql.NVARCHAR(), mssql.NTEXT()])
def test_existing_unicode_sql_server_column_is_unchanged(column_type):
    connection = MagicMock()
    connection.dialect = mssql.dialect()
    inspector = MagicMock()
    inspector.default_schema_name = 'dbo'
    inspector.get_columns.return_value = [{'name': 'comment', 'type': column_type, 'nullable': False}]
    with patch('app.schema_compat.sa.inspect', return_value=inspector):
        assert ensure_unicode_comment_column(connection) is False
    connection.execute.assert_not_called()


def test_sqlite_does_not_need_schema_conversion():
    engine = sa.create_engine('sqlite:///:memory:')
    try:
        with engine.begin() as connection:
            assert ensure_unicode_comment_column(connection) is False
    finally:
        engine.dispose()
