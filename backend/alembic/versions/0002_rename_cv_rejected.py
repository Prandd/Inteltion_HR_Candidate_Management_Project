"""Rename the status 'CV rejected' to 'Rejected' (contract v2.1.0).

Revision ID: 0002_rename_cv_rejected
Revises: 0001_round4
Create Date: 2026-09-19

The two names always meant the same thing; the team settled on the shorter one.
"Rejected at which stage" is answered by `candidates.before_rejected_status`.

Three places hold the literal, and ALL of them have to move together - a row
left as 'CV rejected' fails the startup enum assertion in app/statuses.py and
the API will not boot:

  * candidates.status               - the live value
  * candidates.before_rejected_status - defensive; the transition rule in
    services.py never writes a rejected state here, but a hand-edited or
    pre-F5 row could hold one
  * status_history.from_status / to_status - the audit trail. Rewritten so the
    history reads consistently with the current enum. This edits history, which
    is normally forbidden - it is acceptable here only because the underlying
    fact is unchanged (the candidate was rejected); only our name for it moved.
"""
from alembic import op

revision = "0002_rename_cv_rejected"
down_revision = "0001_round4"
branch_labels = None
depends_on = None

OLD = "CV rejected"
NEW = "Rejected"


def _rewrite(old: str, new: str) -> None:
    op.execute(
        f"UPDATE candidates SET status = '{new}' WHERE status = '{old}'"
    )
    op.execute(
        "UPDATE candidates SET before_rejected_status = "
        f"'{new}' WHERE before_rejected_status = '{old}'"
    )
    op.execute(
        f"UPDATE status_history SET to_status = '{new}' WHERE to_status = '{old}'"
    )
    op.execute(
        f"UPDATE status_history SET from_status = '{new}' WHERE from_status = '{old}'"
    )


def upgrade() -> None:
    _rewrite(OLD, NEW)


def downgrade() -> None:
    _rewrite(NEW, OLD)
