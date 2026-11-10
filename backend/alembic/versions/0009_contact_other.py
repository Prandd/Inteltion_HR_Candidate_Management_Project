"""Add manually maintained extra contact details.

Revision ID: 0009_contact_other
Revises: 0008_id_counters
"""
from alembic import op
import sqlalchemy as sa

revision = "0009_contact_other"
down_revision = "0008_id_counters"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if "contact_other" not in {column["name"] for column in sa.inspect(op.get_bind()).get_columns("candidates")}:
        op.add_column("candidates", sa.Column("contact_other", sa.Text(), nullable=False, server_default=""))


def downgrade() -> None:
    with op.batch_alter_table("candidates") as batch:
        batch.drop_column("contact_other")
