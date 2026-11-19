"""Preserve Thai in SQL Server comment bodies.

Revision ID: 0010_unicode_comments
Revises: 0009_contact_other
"""
from alembic import op
from app.schema_compat import ensure_unicode_comment_column

revision = "0010_unicode_comments"
down_revision = "0009_contact_other"
branch_labels = None
depends_on = None


def upgrade() -> None:
    ensure_unicode_comment_column(op.get_bind())


def downgrade() -> None:
    # Keep Unicode storage: reverting to TEXT could destroy comments written
    # after this migration. The old application can still read this column.
    pass
