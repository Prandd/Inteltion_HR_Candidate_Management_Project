"""Add id_counters so candidate ids are never reused after a delete.

Revision ID: 0008_id_counters
Revises: 0007_application_cycles
"""
from alembic import op
import sqlalchemy as sa

revision = "0008_id_counters"
down_revision = "0007_application_cycles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "id_counters",
        sa.Column("name", sa.String(50), primary_key=True),
        sa.Column("last_value", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("id_counters")
