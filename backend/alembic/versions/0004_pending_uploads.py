"""pending_uploads - CVs held for a human create-or-update decision.

Revision ID: 0004_pending_uploads
Revises: 0003_unique_email
Create Date: 2026-09-19

Round 4: an upload with no exact email match but a plausible soft match (phone,
or name + position) stops here instead of silently becoming a new candidate.

`file_bytes` holds the raw upload until somebody resolves it. Keeping the bytes
in the database for what should be a short wait avoids inventing a "move this
blob later" operation on the Storage protocol; uploads are capped at
MAX_UPLOAD_MB (10 MB) and the column is cleared on resolution, so this does not
grow unbounded.

No foreign key on resolved_candidate_id on purpose: it points at whichever
candidate the file ended up on, and that candidate may later be deleted without
invalidating the audit record of the decision that was made.
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_pending_uploads"
down_revision = "0003_unique_email"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pending_uploads",
        sa.Column("pending_upload_id", sa.String(), primary_key=True),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("file_bytes", sa.LargeBinary(), nullable=True),
        sa.Column("extracted_fields", sa.JSON(), nullable=False),
        sa.Column("duplicate_candidate_ids", sa.JSON(), nullable=False),
        sa.Column("uploaded_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution", sa.String(), nullable=True),
        sa.Column("resolved_candidate_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["uploaded_by"], ["hr_accounts.account_id"]),
    )
    # The work queue reads "everything still open, oldest first".
    op.create_index(
        "ix_pending_uploads_open",
        "pending_uploads",
        ["resolved_at", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_pending_uploads_open", table_name="pending_uploads")
    op.drop_table("pending_uploads")
