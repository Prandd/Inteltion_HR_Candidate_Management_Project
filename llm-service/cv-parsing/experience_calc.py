"""
experience_calc.py — computes `experience_total` from parsed experience
date ranges, rather than trusting the LLM's own arithmetic (Section 2.1,
recommended approach).

Handles:
- "YYYY-MM" and "YYYY" formatted dates
- "Present" / "Current" / "Now" (case-insensitive) as an open-ended end date
- Overlapping roles (e.g., concurrent freelance + full-time) are merged so
  overlapping months aren't double-counted
- Malformed / unparseable entries are skipped rather than raising, so one
  bad date never crashes extraction for an otherwise-good CV
"""
from __future__ import annotations

import re
from datetime import date
from typing import List, Optional, Tuple

_PRESENT_ALIASES = {"present", "current", "currently", "now", "ongoing", "till date", "to date"}

_YYYY_MM_RE = re.compile(r"^(?P<year>\d{4})[-/](?P<month>\d{1,2})$")
_YYYY_RE = re.compile(r"^(?P<year>\d{4})$")


def _parse_date_token(token: str, *, is_end_date: bool, today: date) -> Optional[date]:
    """Parses a single date-like string into a date. Returns None if unparseable."""
    if not token:
        return None
    cleaned = token.strip().lower()

    if cleaned in _PRESENT_ALIASES:
        return today if is_end_date else None

    m = _YYYY_MM_RE.match(cleaned)
    if m:
        year = int(m.group("year"))
        month = int(m.group("month"))
        if not (1 <= month <= 12) or year < 1950 or year > today.year + 1:
            return None
        return date(year, month, 1)

    m = _YYYY_RE.match(cleaned)
    if m:
        year = int(m.group("year"))
        if year < 1950 or year > today.year + 1:
            return None
        # Year-only entries: assume Jan for start, Dec for end (conservative
        # for start, generous for end — this only affects edge months).
        return date(year, 1 if not is_end_date else 12, 1)

    return None


def _months_between(start: date, end: date) -> int:
    if end < start:
        return 0
    return (end.year - start.year) * 12 + (end.month - start.month) + 1


def _merge_intervals(intervals: List[Tuple[date, date]]) -> List[Tuple[date, date]]:
    """Merges overlapping/adjacent (start, end) date ranges so concurrent
    roles aren't double-counted."""
    if not intervals:
        return []
    intervals = sorted(intervals, key=lambda iv: iv[0])
    merged = [intervals[0]]
    for start, end in intervals[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


def compute_experience_total(
    experience_entries: List[dict],
    *,
    today: Optional[date] = None,
    round_to: int = 1,
) -> float:
    """Computes total years of experience from a list of experience entries.

    Args:
        experience_entries: list of dicts with 'start_date' / 'end_date'
            keys (as produced by the extraction schema).
        today: override "now" for deterministic testing; defaults to
            date.today().
        round_to: decimal places for the returned years figure.

    Returns:
        Total years of experience as a float (0.0 if nothing parseable).
    """
    today = today or date.today()
    intervals: List[Tuple[date, date]] = []

    for entry in experience_entries or []:
        start_raw = (entry.get("start_date") or "").strip()
        end_raw = (entry.get("end_date") or "").strip()

        start = _parse_date_token(start_raw, is_end_date=False, today=today)
        end = _parse_date_token(end_raw, is_end_date=True, today=today)

        if start is None:
            continue
        if end is None:
            # No parseable end date and not "Present" — skip this entry
            # rather than guessing.
            continue
        if end < start:
            # Data entry error (e.g., swapped dates) — skip rather than
            # producing a negative or nonsensical contribution.
            continue

        intervals.append((start, end))

    merged = _merge_intervals(intervals)
    total_months = sum(_months_between(s, e) for s, e in merged)
    years = total_months / 12.0
    return round(years, round_to)
