"""Regenerate shared-contracts/status.ts from shared-contracts/schema.json.

    cd backend && python scripts/gen_frontend_types.py

F6 step 3. Members 1 and 2 import the generated union instead of retyping the
strings, so a status can only ever be added in one place.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CONTRACTS = os.path.abspath(os.path.join(HERE, "..", "..", "shared-contracts"))
SCHEMA = os.path.join(CONTRACTS, "schema.json")
OUT = os.path.join(CONTRACTS, "status.ts")

HEADER = """// GENERATED FILE - do not edit by hand.
// Regenerate:  cd backend && python scripts/gen_frontend_types.py
// Source of truth: shared-contracts/schema.json -> properties.status.enum
//
// Import these instead of retyping the strings. A typo in a status literal does
// not throw anywhere - the Kanban column just silently renders empty, and
// ?status= filtering just silently returns nothing.
"""


def ts_array(name: str, values: list[str]) -> str:
    items = "\n".join(f'  {json.dumps(v)},' for v in values)
    return f"export const {name} = [\n{items}\n] as const;\n"


def main() -> int:
    # utf-8-sig everywhere we READ a contract: a Windows editor re-saving one
    # adds a BOM, and json.load fails on it with a misleading message.
    with open(SCHEMA, "r", encoding="utf-8-sig") as fh:
        schema = json.load(fh)

    statuses = schema["properties"]["status"]["enum"]
    uploads = schema["properties"]["upload_status"]["enum"]
    rejected = [s for s in statuses if s.lower().endswith("rejected")]

    roles, comment_types = ["admin", "hr", "line_manager", "viewer"], []
    account_schema = os.path.join(CONTRACTS, "hr-account-schema.json")
    if os.path.exists(account_schema):
        with open(account_schema, "r", encoding="utf-8-sig") as fh:
            roles = json.load(fh)["properties"]["role"]["enum"]
    comment_schema = os.path.join(CONTRACTS, "comment-log-schema.json")
    if os.path.exists(comment_schema):
        with open(comment_schema, "r", encoding="utf-8-sig") as fh:
            comment_types = json.load(fh)["properties"]["comment_type"]["enum"]

    parts = [
        HEADER,
        ts_array("CANDIDATE_STATUSES", statuses),
        "\nexport type CandidateStatus = (typeof CANDIDATE_STATUSES)[number];\n",
        f'\nexport const DEFAULT_CANDIDATE_STATUS: CandidateStatus = {json.dumps(statuses[0])};\n',
        "\n/**\n"
        " * Statuses that count as \"rejected\". Convention: any status ending in\n"
        " * \"rejected\". `before_rejected_status` holds the stage the candidate was at\n"
        " * when they entered one of these, and POST /api/candidates/{id}/restore moves\n"
        " * them back to it.\n"
        " */\n",
        "export const REJECTED_STATUSES: readonly CandidateStatus[] = [\n"
        + "\n".join(f"  {json.dumps(v)}," for v in rejected)
        + "\n];\n",
        "\nexport function isRejected(status: string): status is CandidateStatus {\n"
        "  return (REJECTED_STATUSES as readonly string[]).includes(status);\n"
        "}\n",
        "\n// File/extraction lifecycle - SEPARATE from the HR pipeline status above.\n"
        "// The delete/cancel button keys off this one; the dashboard badge keys off `status`.\n",
        ts_array("UPLOAD_STATUSES", uploads),
        "\nexport type UploadStatus = (typeof UPLOAD_STATUSES)[number];\n",
        "\n// Account roles - shared-contracts/hr-account-schema.json\n",
        f"export const ACCOUNT_ROLES = {json.dumps(roles)} as const;\n"
        "export type AccountRole = (typeof ACCOUNT_ROLES)[number];\n",
    ]
    if comment_types:
        parts.append(
            "\n// Comment types - shared-contracts/comment-log-schema.json\n"
            f"export const COMMENT_TYPES = {json.dumps(comment_types)} as const;\n"
            "export type CommentType = (typeof COMMENT_TYPES)[number];\n"
        )

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("".join(parts))

    print(f"wrote {OUT} ({len(statuses)} statuses, rejected={rejected})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
