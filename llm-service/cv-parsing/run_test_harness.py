"""
run_test_harness.py — standalone test harness (sprint plan Day 5 & README
Section 6, Member 4).

Run with:
    python run_test_harness.py

Requires .env variables set (see README.md Section 4.1):
    CV_SCORING_PROVIDER, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_DEPLOYMENT

Picks up every .pdf/.docx file in sample_cvs/, runs it through
extract_candidate(), and prints a field-by-field summary so accuracy can
be spot-checked by hand — no FastAPI app, database, or frontend required
(Anti-Blocking Strategy, Section 3).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Load .env if python-dotenv is available (matches README's .env setup).
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from extractor import extract_candidate

SAMPLE_DIR = Path(__file__).parent / "sample_cvs"
SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


def _has_mojibake(candidate: dict) -> bool:
    """Recursively checks every string value for the Unicode replacement
    character, so a regression here fails loudly in the harness output."""
    def _walk(v):
        if isinstance(v, str):
            return "\ufffd" in v
        if isinstance(v, list):
            return any(_walk(x) for x in v)
        if isinstance(v, dict):
            return any(_walk(x) for x in v.values())
        return False
    return _walk(candidate)


def _summarize(candidate: dict) -> str:
    summary = candidate.get("summary") or ""
    lines = [
        f"  full_name:            {candidate.get('full_name')!r} (title-cased)",
        f"  email:                {candidate.get('email')!r}",
        f"  phone:                {candidate.get('phone')!r}",
        f"  applied_position:     {candidate.get('applied_position')!r} (must be '')",
        f"  summary:              {summary!r} (must NOT be '')",
        f"  skills:               {len(candidate.get('skills', []))} group(s)",
        f"  experience entries:   {len(candidate.get('experience', []))}",
        f"  experience_total:     {candidate.get('experience_total')} years (computed)",
        f"  current_salary:       {candidate.get('current_salary')}",
        f"  expected_salary:      {candidate.get('expected_salary')}",
        f"  education entries:    {len(candidate.get('education', []))}",
        f"  hr_comment:           {candidate.get('hr_comment')!r} (must be '')",
        f"  line_manager_comment: {candidate.get('line_manager_comment')!r} (must be '')",
        f"  candidate_id:         {candidate.get('candidate_id')!r} (must be None)",
        f"  extraction_confidence:{candidate.get('extraction_confidence')}",
        f"  contains '\\ufffd':    {_has_mojibake(candidate)} (must be False)",
    ]
    return "\n".join(lines)


def _is_fallback(candidate: dict) -> bool:
    return candidate.get("extraction_confidence") == 0.0 and candidate.get(
        "summary", ""
    ).startswith("[AUTO-FALLBACK")


def main() -> int:
    if not SAMPLE_DIR.exists():
        print(f"Sample directory not found: {SAMPLE_DIR}")
        return 1

    files = sorted(
        p for p in SAMPLE_DIR.iterdir() if p.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    if not files:
        print(
            f"No sample CVs found in {SAMPLE_DIR}.\n"
            f"Add 5-10 real or synthetic .pdf/.docx files here (Day 1 task) "
            f"and re-run this harness."
        )
        return 1

    print(f"Found {len(files)} sample CV(s). Running extraction...\n")

    fallback_count = 0
    results = []

    for path in files:
        print("=" * 70)
        print(f"File: {path.name}")
        print("-" * 70)
        try:
            file_bytes = path.read_bytes()
            candidate = extract_candidate(file_bytes, filename=path.name)
            print(_summarize(candidate))
            if _is_fallback(candidate):
                fallback_count += 1
                print("\n  >>> FALLBACK PATH USED for this file. <<<")
            results.append({"file": path.name, "candidate": candidate})
        except Exception as e:  # noqa: BLE001 - harness should never crash mid-run
            print(f"  UNEXPECTED HARNESS ERROR (extract_candidate should not raise): {e}")
        print()

    # Dump full JSON results for detailed field-by-field spot-checking.
    out_path = Path(__file__).parent / "test_harness_results.json"
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))

    print("=" * 70)
    print(f"Done. {len(files)} file(s) processed, {fallback_count} used the fallback path.")
    print(f"Full results written to: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())