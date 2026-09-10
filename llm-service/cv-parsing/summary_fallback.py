"""
summary_fallback.py — deterministic, non-fabricated summary generation.

Used only when the LLM returns an empty `summary`. Per the requirement
that `summary` must never be fabricated, this builds a summary using
ONLY fields that were already extracted and validated elsewhere in the
pipeline (experience, skills) — it never invents years of experience,
job titles, or skills that aren't already present in the structured
data.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from experience_calc import _parse_date_token


def _most_recent_experience(experience: list[dict]) -> Optional[dict]:
    """Picks the most recent role: an entry ending 'Present' wins outright;
    otherwise the entry with the latest parseable end_date. Falls back to
    the first entry if no dates are parseable, since CVs are conventionally
    listed reverse-chronologically."""
    if not experience:
        return None

    for entry in experience:
        if str(entry.get("end_date", "")).strip().lower() == "present":
            return entry

    today = date.today()
    best_entry, best_date = None, None
    for entry in experience:
        parsed = _parse_date_token(str(entry.get("end_date", "")), is_end_date=True, today=today)
        if parsed and (best_date is None or parsed > best_date):
            best_date, best_entry = parsed, entry

    return best_entry or experience[0]


def build_fallback_summary(candidate_data: dict) -> str:
    """Builds a short, strictly factual summary from already-extracted
    experience/skills fields. Returns a plain, honest placeholder if
    nothing usable was extracted at all — never a fabricated claim.
    """
    experience = candidate_data.get("experience") or []
    skills = candidate_data.get("skills") or []

    latest = _most_recent_experience(experience)
    skill_names = [s.get("skill") for s in skills if s.get("skill")]

    clauses = []

    if latest:
        position = (latest.get("position") or "").strip()
        company = (latest.get("company") or "").strip()
        if position and company:
            clauses.append(f"Most recently worked as {position} at {company}")
        elif position:
            clauses.append(f"Most recently worked as {position}")
        elif company:
            clauses.append(f"Most recently worked at {company}")

    if skill_names:
        shown = skill_names[:3]
        clauses.append(f"with background in {', '.join(shown)}")

    if not clauses:
        return "No summary could be derived from the extracted CV content."

    return (" ".join(clauses)).strip().rstrip(",") + "."
