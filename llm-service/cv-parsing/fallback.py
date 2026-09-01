"""
fallback.py — the always-valid fallback response.

Per the sprint plan's Anti-Blocking Strategy: "Keep a hardcoded fallback
JSON ready at all times — if prompt tuning or provider quota runs long,
Member 3 can integrate against your fallback and swap in the tuned
version later without any code change on their end."

This is also the second-line defense inside extract_candidate() itself:
if text extraction, the LLM call, AND the repair pass all fail, this is
what gets returned instead of raising — the pipeline must never crash on
a single bad CV.
"""
from __future__ import annotations

from schema import CandidateExtraction


def build_fallback_candidate(
    *,
    raw_text_snippet: str = "",
    reason: str = "extraction_failed",
) -> dict:
    """Returns a schema-valid placeholder candidate dict.

    `extraction_confidence` is pinned to 0.0 so downstream UIs (Member 1's
    score/status display) can visually flag this record as needing manual
    HR review rather than silently showing placeholder data as if it were
    real.

    Args:
        raw_text_snippet: whatever raw text WAS successfully extracted
            (if any), so HR/debugging has some signal even in the
            failure path. Truncated to 500 chars per the schema.
        reason: short machine-readable failure reason, folded into
            `summary` so it's visible in the dashboard without needing
            a separate error-tracking field this MVP doesn't have.
    """
    fallback = CandidateExtraction(
        candidate_id=None,
        full_name="",
        email="",
        phone="",
        applied_position="",
        summary=f"[AUTO-FALLBACK: extraction did not complete — reason: {reason}. "
        f"Please review the original file manually.]",
        skills=[],
        experience=[],
        experience_total=0.0,
        current_salary=0.0,
        expected_salary=0.0,
        education=[],
        hr_comment="",
        line_manager_comment="",
        extraction_confidence=0.0,
        raw_text_snippet=(raw_text_snippet or "")[:500],
    )
    return fallback.to_output_dict()
