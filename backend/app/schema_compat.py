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


# --- every text column -------------------------------------------------------
#
# SQL Server VARCHAR/TEXT keep text in the database code page, so Thai, Chinese,
# Arabic ... are stored as '?'. models_db declares every column a person or a CV
# writes into as Unicode/UText (NVARCHAR); this brings a database that was built
# earlier (create_all, never migrated) in line. It only changes the column TYPE:
# values already stored as '?' cannot be recovered.
#
# SQL Server refuses ALTER COLUMN while a default constraint, index or UNIQUE
# constraint depends on the column, so those are dropped first and recreated
# (same name, same columns) right after - all inside the caller's transaction,
# so a failure rolls the whole upgrade back instead of leaving it half done.

_DEFAULTS_SQL = sa.text(
    "SELECT dc.name AS name, dc.definition AS definition "
    "FROM sys.default_constraints dc "
    "JOIN sys.columns c ON c.object_id = dc.parent_object_id "
    "AND c.column_id = dc.parent_column_id "
    "WHERE dc.parent_object_id = OBJECT_ID(:table) AND c.name = :column"
)

_INDEXES_SQL = sa.text(
    "SELECT i.name AS name, i.index_id AS index_id, i.is_unique AS is_unique, "
    "i.is_unique_constraint AS is_unique_constraint, "
    "i.is_primary_key AS is_primary_key, i.has_filter AS has_filter "
    "FROM sys.indexes i "
    "WHERE i.object_id = OBJECT_ID(:table) AND i.name IS NOT NULL AND EXISTS ("
    "SELECT 1 FROM sys.index_columns ic "
    "JOIN sys.columns c ON c.object_id = ic.object_id AND c.column_id = ic.column_id "
    "WHERE ic.object_id = i.object_id AND ic.index_id = i.index_id AND c.name = :column)"
)

_INDEX_COLUMNS_SQL = sa.text(
    "SELECT c.name AS name, ic.is_included_column AS is_included, "
    "ic.is_descending_key AS is_descending "
    "FROM sys.index_columns ic "
    "JOIN sys.columns c ON c.object_id = ic.object_id AND c.column_id = ic.column_id "
    "WHERE ic.object_id = OBJECT_ID(:table) AND ic.index_id = :index_id "
    "ORDER BY ic.is_included_column, ic.key_ordinal"
)


def _is_unicode(column_type) -> bool:
    return isinstance(column_type, (sa.Unicode, sa.UnicodeText))


def _upgrade_column(connection, schema, table_name, column, current) -> None:
    quote = connection.dialect.identifier_preparer.quote
    table = f"{quote(schema)}.{quote(table_name)}" if schema else quote(table_name)
    params = {"table": table, "column": column.name}

    defaults = connection.execute(_DEFAULTS_SQL, params).mappings().all()
    indexes = connection.execute(_INDEXES_SQL, params).mappings().all()

    drops, recreates = [], []
    for default in defaults:
        drops.append(f"ALTER TABLE {table} DROP CONSTRAINT {quote(default['name'])}")
        recreates.append(
            f"ALTER TABLE {table} ADD CONSTRAINT {quote(default['name'])} "
            f"DEFAULT {default['definition']} FOR {quote(column.name)}"
        )
    for index in indexes:
        if index["is_primary_key"] or index["has_filter"]:
            raise RuntimeError(
                f"Refusing to auto-convert {table_name}.{column.name}: it is part of "
                f"{'the primary key' if index['is_primary_key'] else 'a filtered index'} "
                f"{index['name']!r}. Convert it by hand."
            )
        members = connection.execute(
            _INDEX_COLUMNS_SQL, {"table": table, "index_id": index["index_id"]}
        ).mappings().all()
        if any(m["is_included"] or m["is_descending"] for m in members):
            raise RuntimeError(
                f"Refusing to auto-convert {table_name}.{column.name}: index "
                f"{index['name']!r} has included or descending columns. Convert it by hand."
            )
        columns = ", ".join(quote(m["name"]) for m in members)
        name = quote(index["name"])
        if index["is_unique_constraint"]:
            drops.append(f"ALTER TABLE {table} DROP CONSTRAINT {name}")
            recreates.append(f"ALTER TABLE {table} ADD CONSTRAINT {name} UNIQUE ({columns})")
        else:
            drops.append(f"DROP INDEX {name} ON {table}")
            unique = "UNIQUE " if index["is_unique"] else ""
            recreates.append(f"CREATE {unique}INDEX {name} ON {table} ({columns})")

    target = column.type.compile(dialect=connection.dialect)
    nullability = "NULL" if current["nullable"] else "NOT NULL"
    alter = f"ALTER TABLE {table} ALTER COLUMN {quote(column.name)} {target} {nullability}"

    for statement in [*drops, alter, *recreates]:
        connection.execute(sa.text(statement))


def ensure_unicode_text_columns(connection, metadata) -> list[str]:
    """Convert every model column declared Unicode/UnicodeText whose SQL Server
    column is still VARCHAR/TEXT. Returns the "table.column" names changed;
    already-Unicode columns, missing tables and non-SQL-Server databases are
    left alone, so it is safe to call on every boot."""
    if connection.dialect.name != "mssql":
        return []
    inspector = sa.inspect(connection)
    schema = inspector.default_schema_name
    upgraded = []
    for table in metadata.sorted_tables:
        if not inspector.has_table(table.name, schema=schema):
            continue
        existing = {c["name"]: c for c in inspector.get_columns(table.name, schema=schema)}
        for column in table.columns:
            current = existing.get(column.name)
            if current is None or not _is_unicode(column.type) or _is_unicode(current["type"]):
                continue
            _upgrade_column(connection, schema, table.name, column, current)
            upgraded.append(f"{table.name}.{column.name}")
    return upgraded
