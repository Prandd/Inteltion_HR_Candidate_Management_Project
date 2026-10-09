"""Add positions table.

Revision ID: 0006_positions
Revises: 0005_ownership_sql_scores
Create Date: 2026-10-09

Reverse-engineered from the frontend's Positions/PositionDetail/
PositionRequirements pages, which called GET/POST /positions against a
resource that never existed on this branch - no prior contract. See
app/models_db.py's Position class docstring.

String lengths are explicit here (unlike some older migrations in this
file set) because a length-less String() compiles to NVARCHAR(MAX) on
the mssql dialect, which cannot be a primary key - see the round-5
Azure SQL migration fixes in models_db.py for the same issue hit live.
"""
from alembic import op
import sqlalchemy as sa

revision = "0006_positions"
down_revision = "0005_ownership_sql_scores"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "positions",
        sa.Column("position_id", sa.String(36), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("department", sa.String(255), nullable=False, server_default=""),
        sa.Column("location", sa.String(255), nullable=False, server_default=""),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("skills", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="Open"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("positions")
