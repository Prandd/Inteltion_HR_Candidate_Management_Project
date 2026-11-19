"""Any number of named contacts per candidate (candidates.contacts).

Revision ID: 0012_contacts
Revises: 0011_unicode_text_columns

Replaces the single free-text `contact_other`: its text is moved into `contacts`
as one entry named "Other" and the old column is cleared (left in place, unused).
"""
from alembic import op
import sqlalchemy as sa

from app.schema_compat import backfill_contacts_from_other

revision = "0012_contacts"
down_revision = "0011_unicode_text_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if "contacts" not in {column["name"] for column in sa.inspect(bind).get_columns("candidates")}:
        op.add_column("candidates", sa.Column("contacts", sa.JSON(), nullable=False, server_default="[]"))
    backfill_contacts_from_other(bind)


def downgrade() -> None:
    with op.batch_alter_table("candidates") as batch:
        batch.drop_column("contacts")
