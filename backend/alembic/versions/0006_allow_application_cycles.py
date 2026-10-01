"""Allow multiple application cycles for one normalized email.

Revision ID: 0006_application_cycles
Revises: 0005_ownership_sql_scores
"""
from alembic import op
import sqlalchemy as sa

revision = "0006_application_cycles"
down_revision = "0005_ownership_sql_scores"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    indexes = sa.inspect(bind).get_indexes("candidates")
    for index in indexes:
        if index.get("unique") and index.get("column_names") == ["email_normalized"]:
            op.drop_index(index["name"], table_name="candidates")

    remaining = sa.inspect(bind).get_indexes("candidates")
    has_lookup_index = any(
        index.get("column_names") == ["email_normalized"]
        for index in remaining
    )
    if not has_lookup_index:
        op.create_index(
            "ix_candidates_email_normalized",
            "candidates",
            ["email_normalized"],
        )


def downgrade() -> None:
    # This can fail if multiple application cycles share an email.
    op.create_index(
        "ux_candidates_email_normalized",
        "candidates",
        ["email_normalized"],
        unique=True,
    )