"""F6 - single source of truth for the HR pipeline `status` enum.

The canonical list lives in `shared-contracts/schema.json`. This module loads it
from there at import time so the backend cannot drift from the contract the two
frontend lanes code against; `_FALLBACK` is used only when the contract file is
not reachable (e.g. a container that mounts the backend without the contracts
folder).

Round-4 note: `schemas.py` and `schema.json` already agreed before this round -
only the planning documents disagreed ("Rejected" vs "CV rejected"). The team
then decided the two names always meant the same thing and settled on the
shorter one, so "CV rejected" was renamed "Rejected" (contract v2.1.0). That is
a breaking change for stored rows and for both frontend lanes - see
alembic/versions/0002_rename_cv_rejected.py. "Rejected at which stage" is
answered by F5's `before_rejected_status`, not by splitting the enum.

No static Python `Enum` is declared on purpose: the values are read from the
contract at runtime, and a hand-written Enum beside it would be exactly the
second source of truth F6 exists to remove.
"""
from __future__ import annotations

import json
import logging
import os

log = logging.getLogger("app.statuses")

# Mirror of shared-contracts/schema.json -> properties.status.enum.
# Only used when the contract file cannot be read.
_FALLBACK: list[str] = [
    "New",
    "Review",
    "Needs information",
    "CV passed",
    "Assessment",
    "Interview",
    "Hired",
    "Rejected",
    "Archived",
]

DEFAULT_STATUS = "New"

_HERE = os.path.dirname(os.path.abspath(__file__))


def _contract_candidates() -> list[str]:
    """Where schema.json might live, most specific first.

    - repo layout:   backend/app/statuses.py -> ../../shared-contracts/
    - bundled copy:  backend/contracts/ (what a services deploy ships - the
                     repo-root shared-contracts/ is outside the backend root)
    - docker-compose mounts ./shared-contracts at /contracts (read-only)
    - CONTRACT_SCHEMA_FILE overrides both
    """
    paths = []
    env_path = os.environ.get("CONTRACT_SCHEMA_FILE", "").strip()
    if env_path:
        paths.append(env_path)
    paths.append(os.path.join(_HERE, "..", "..", "shared-contracts", "schema.json"))
    paths.append(os.path.join(_HERE, "..", "contracts", "schema.json"))
    paths.append(os.path.join("/contracts", "schema.json"))
    return paths


def load_status_values() -> list[str]:
    """Read properties.status.enum out of the contract, or fall back."""
    for path in _contract_candidates():
        if not os.path.exists(path):
            continue
        try:
            # utf-8-sig, not utf-8: a Windows editor (Notepad, PowerShell's
            # Set-Content) re-saving this file adds a BOM, and json.load chokes
            # on it with a baffling "Expecting value: line 1 column 1".
            with open(path, "r", encoding="utf-8-sig") as fh:
                contract = json.load(fh)
            values = contract["properties"]["status"]["enum"]
            if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
                raise ValueError("status.enum is not a list of strings")
            if values != _FALLBACK:
                # Not fatal - the contract wins - but somebody edited one side only.
                log.warning(
                    "STATUS: contract enum differs from the built-in fallback. "
                    "contract=%s fallback=%s (using the contract, from %s)",
                    values, _FALLBACK, os.path.abspath(path),
                )
            return values
        except Exception as exc:  # malformed contract must not stop the API booting
            log.warning(
                "STATUS: could not read the status enum from '%s' (%s); using the built-in list",
                path, exc,
            )
            break
    return list(_FALLBACK)


STATUS_VALUES: list[str] = load_status_values()
STATUS_SET: frozenset[str] = frozenset(STATUS_VALUES)

# F5 - which statuses count as "rejected".
# Convention: a rejected state is any status ending in "rejected", so adding
# "Assessment rejected" / "Interview rejected" to the contract later needs no
# code change here. Today that resolves to {"Rejected"}.
REJECTED_STATES: frozenset[str] = frozenset(
    s for s in STATUS_VALUES if s.lower().endswith("rejected")
) or frozenset({"Rejected"})


def is_rejected(status: str) -> bool:
    return status in REJECTED_STATES


def assert_valid_db_statuses(db) -> None:
    """F6 step 4 - fail fast if anything in the DB drifted out of the enum.

    Called once on startup, after seeding. Raises rather than logs: a status the
    frontend has no column for is silently invisible in the Kanban, which is the
    exact failure this round is meant to make impossible.
    """
    from .models_db import Candidate  # local import - avoids an import cycle

    rows = db.query(Candidate.candidate_id, Candidate.status).all()
    bad = [(cid, st) for cid, st in rows if st not in STATUS_SET]
    if bad:
        listed = ", ".join(f"{cid}='{st}'" for cid, st in bad[:10])
        hint = ""
        if any(st == "CV rejected" for _, st in bad):
            hint = (
                " This database predates contract v2.1.0, which renamed "
                "'CV rejected' to 'Rejected'. Run `alembic upgrade head`."
            )
        raise RuntimeError(
            f"{len(bad)} candidate(s) hold a status outside the contract enum: {listed}"
            f"{' ...' if len(bad) > 10 else ''}. Allowed: {STATUS_VALUES}.{hint}"
        )