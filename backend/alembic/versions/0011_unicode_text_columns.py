"""Store every text column as Unicode on SQL Server (NVARCHAR).

Revision ID: 0011_unicode_text_columns
Revises: 0010_unicode_comments

VARCHAR/TEXT keep text in the database code page, so Thai (and any other
non-Latin script) became '?'. Ids, foreign keys and the password hash stay
VARCHAR - they are ASCII by construction.
"""
from alembic import op

from app.database import Base
from app import models_db  # noqa: F401  (registers every table on Base.metadata)
from app.schema_compat import ensure_unicode_text_columns

revision = "0011_unicode_text_columns"
down_revision = "0010_unicode_comments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    ensure_unicode_text_columns(op.get_bind(), Base.metadata)


def downgrade() -> None:
    # Keep Unicode storage: converting back to VARCHAR would turn any non-Latin
    # text written since into '?'. The old application reads NVARCHAR fine.
    pass
