"""Delete duplicate-email candidates, then make email_normalized UNIQUE.

Revision ID: 0003_unique_email
Revises: 0002_rename_cv_rejected
Create Date: 2026-09-19

Why this could not be part of 0001: before F4 existed, every re-upload of the
same CV created a SECOND candidate, so any database that has been used for
testing already holds duplicate emails. `CREATE UNIQUE INDEX` on that data
fails, which would have blocked `alembic upgrade head` for the whole team.

Team decision (round 4): the duplicates are test data, not real records - wipe
them rather than building a merge tool for data nobody needs. This keeps the
OLDEST row per email (`MIN(candidate_id)`, which is the earliest created one
because candidate_id is a running number) - the same row `_find_by_email()`
already resolved to, so the choice is consistent with how the app has been
behaving.

Child rows are deleted explicitly. SQLite does not enforce foreign keys unless
PRAGMA foreign_keys is on, so without this the orphans would sit there quietly
until the move to Postgres turned them into constraint violations.

NOT reversible: downgrade drops the index, but the deleted candidates are gone.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import bindparam, text

revision = "0003_unique_email"
down_revision = "0002_rename_cv_rejected"
branch_labels = None
depends_on = None

CHILD_TABLES = (
    "resume_versions",
    "comment_logs",
    "status_history",
    "candidate_change_log",
)


def upgrade() -> None:
    conn = op.get_bind()

    # Everything that is NOT the oldest row for its email.
    doomed = [
        r[0]
        for r in conn.execute(text(
            """
            SELECT candidate_id FROM candidates
            WHERE email_normalized IS NOT NULL
              AND candidate_id NOT IN (
                  SELECT MIN(candidate_id) FROM candidates
                  WHERE email_normalized IS NOT NULL
                  GROUP BY email_normalized
              )
            """
        )).fetchall()
    ]

    if doomed:
        print(f"[0003] removing {len(doomed)} duplicate-email candidate(s): {doomed}")
        for table in CHILD_TABLES:
            conn.execute(
                text(f"DELETE FROM {table} WHERE candidate_id IN :ids").bindparams(
                    bindparam("ids", expanding=True)
                ),
                {"ids": doomed},
            )
        conn.execute(
            text("DELETE FROM candidates WHERE candidate_id IN :ids").bindparams(
                bindparam("ids", expanding=True)
            ),
            {"ids": doomed},
        )

    # NULL (no email) is excluded from a UNIQUE index by SQL's own rules -
    # NULL != NULL - which is exactly why normalize_email() returns None rather
    # than "" for a CV with no email. Any number of email-less candidates is fine.
    op.create_index(
        "ux_candidates_email_normalized",
        "candidates",
        ["email_normalized"],
        unique=True,
    )


def downgrade() -> None:
    # The index comes back off; the deleted rows do not come back.
    op.drop_index("ux_candidates_email_normalized", table_name="candidates")
