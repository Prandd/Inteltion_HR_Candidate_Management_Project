"""Small schema upgrades for deployments originally created without Alembic."""
import sqlalchemy as sa


def ensure_unicode_comment_column(connection) -> bool:
    """Upgrade legacy SQL Server comment bodies without reading candidate data.

    SQLite/Postgres text already supports Unicode. SQL Server TEXT/VARCHAR
    depends on the database code page; NVARCHAR preserves Thai regardless of it.
    Already-Unicode columns are left alone. Existing question marks cannot be
    reconstructed by changing the column type.
    """
    if connection.dialect.name != "mssql":
        return False
    inspector = sa.inspect(connection)
    schema = inspector.default_schema_name
    columns = inspector.get_columns("comment_logs", schema=schema)
    column = next(item for item in columns if item["name"] == "comment")
    if isinstance(column["type"], (sa.Unicode, sa.UnicodeText)):
        return False
    quote = connection.dialect.identifier_preparer.quote
    table = f"{quote(schema)}.{quote('comment_logs')}" if schema else quote("comment_logs")
    nullability = "NULL" if column["nullable"] else "NOT NULL"
    connection.execute(sa.text(
        f"ALTER TABLE {table} ALTER COLUMN {quote('comment')} NVARCHAR(MAX) {nullability}"
    ))
    return True
