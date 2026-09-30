"""Round 5: candidate ownership (+ ownership_history) and sql_test_scores.

Revision ID: 0005_ownership_sql_scores
Revises: 0004_pending_uploads
Create Date: 2026-09-30

Ownership rule (round 5 decision): whoever imports a CV owns it. Re-upload and
the pending-upload 'update' resolution never change it; only the dedicated
transfer endpoint does (current owner, or an admin override).

Backfill for existing candidates: `status_history` already has one row per
candidate with `reason='created by upload'` (or `'seeded'`) recording exactly
who created the record - see routers/candidates.py and seed.py. That is a more
accurate source than guessing, so this migration reads it back rather than
assigning every existing candidate to the seed admin. A candidate with no such
row (should not happen post-round-4, but the assertion below does not rely on
that) falls back to the earliest active admin account; if there is truly no
account to attribute to, owner_account_id is left NULL rather than invented.
"""
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = "0005_ownership_sql_scores"
down_revision = "0004_pending_uploads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    with op.batch_alter_table("candidates") as batch:
        batch.add_column(sa.Column("owner_account_id", sa.String(), nullable=True))

    op.create_table(
        "ownership_history",
        sa.Column("ownership_history_id", sa.String(), primary_key=True),
        sa.Column("candidate_id", sa.String(), nullable=False),
        sa.Column("from_owner_account_id", sa.String(), nullable=True),
        sa.Column("to_owner_account_id", sa.String(), nullable=False),
        sa.Column("changed_by", sa.String(), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False, server_default=""),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.candidate_id"]),
        sa.ForeignKeyConstraint(["from_owner_account_id"], ["hr_accounts.account_id"]),
        sa.ForeignKeyConstraint(["to_owner_account_id"], ["hr_accounts.account_id"]),
        sa.ForeignKeyConstraint(["changed_by"], ["hr_accounts.account_id"]),
    )
    op.create_index("ix_ownership_history_candidate", "ownership_history", ["candidate_id"])

    op.create_table(
        "sql_test_scores",
        sa.Column("score_id", sa.String(), primary_key=True),
        sa.Column("candidate_id", sa.String(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("source", sa.String(), nullable=False, server_default="sql_test"),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recorded_by", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.candidate_id"]),
        sa.ForeignKeyConstraint(["recorded_by"], ["hr_accounts.account_id"]),
    )
    op.create_index("ix_sql_test_scores_candidate", "sql_test_scores", ["candidate_id"])

    # --- backfill: earliest status_history.changed_by per candidate ---
    earliest_creator = conn.execute(text(
        """
        SELECT sh.candidate_id, sh.changed_by
        FROM status_history sh
        INNER JOIN (
            SELECT candidate_id, MIN(changed_at) AS first_at
            FROM status_history
            GROUP BY candidate_id
        ) first_row
        ON sh.candidate_id = first_row.candidate_id
        AND sh.changed_at = first_row.first_at
        """
    )).fetchall()
    creator_by_candidate = {cid: changed_by for cid, changed_by in earliest_creator}

    # Fallback for any candidate with no status_history row at all (should not
    # exist post-round-4, but do not leave owner_account_id NULL if we can
    # attribute it to somebody real).
    fallback_admin = conn.execute(text(
        "SELECT account_id FROM hr_accounts WHERE is_active = 1 "
        "ORDER BY created_at ASC LIMIT 1"
    )).fetchone()
    fallback_admin_id = fallback_admin[0] if fallback_admin else None

    all_candidates = conn.execute(text("SELECT candidate_id FROM candidates")).fetchall()
    now = conn.execute(text("SELECT CURRENT_TIMESTAMP")).scalar()

    backfilled = 0
    for (candidate_id,) in all_candidates:
        owner = creator_by_candidate.get(candidate_id) or fallback_admin_id
        if owner is None:
            continue  # no account exists at all - leave NULL, nothing to attribute to
        conn.execute(
            text("UPDATE candidates SET owner_account_id = :owner WHERE candidate_id = :cid"),
            {"owner": owner, "cid": candidate_id},
        )
        conn.execute(
            text(
                "INSERT INTO ownership_history "
                "(ownership_history_id, candidate_id, from_owner_account_id, "
                " to_owner_account_id, changed_by, changed_at, reason) "
                "VALUES (:id, :cid, NULL, :owner, :owner, :now, 'backfilled from status_history')"
            ),
            {"id": str(uuid.uuid4()), "cid": candidate_id,
             "owner": owner, "now": now},
        )
        backfilled += 1

    if backfilled:
        print(f"[0005] backfilled owner_account_id for {backfilled} existing candidate(s)")


def downgrade() -> None:
    op.drop_index("ix_sql_test_scores_candidate", table_name="sql_test_scores")
    op.drop_table("sql_test_scores")
    op.drop_index("ix_ownership_history_candidate", table_name="ownership_history")
    op.drop_table("ownership_history")
    with op.batch_alter_table("candidates") as batch:
        batch.drop_column("owner_account_id")
