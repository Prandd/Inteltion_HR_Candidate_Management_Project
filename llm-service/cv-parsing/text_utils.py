"""
text_utils.py — text cleanup shared across the pipeline.

Fixes two concrete bugs:
1. '\ufffd' (Unicode replacement character) and other mojibake leaking
   into extracted text / LLM output — usually caused by PDFs with
   subset/custom font encodings that pypdf can't map to real glyphs.
2. Inconsistent name capitalization ("JOHN SMITH", "john smith") —
   normalized to a name-aware title case that still respects common
   surname particles ("de", "van", "bin", ...) and apostrophes/hyphens.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any

try:
    import ftfy  # best-effort mojibake repair (e.g. "donâ€™t" -> "don't")

    _HAS_FTFY = True
except ImportError:
    _HAS_FTFY = False

REPLACEMENT_CHAR = "\ufffd"

# Surname/given-name particles that conventionally stay lowercase unless
# they're the first word of the whole name.
_LOWERCASE_NAME_PARTICLES = {
    "de", "del", "dela", "della", "des", "di", "da", "das", "dos",
    "du", "van", "von", "der", "den", "ter", "ten", "la", "le", "el",
    "al", "bin", "binti", "ibn", "abu",
}


def sanitize_text(text: str) -> str:
    """Cleans mojibake, replacement characters, and stray control
    characters out of a string. Safe to call on already-clean text
    (idempotent) and safe on non-Latin scripts (Thai, etc.) — it only
    strips true control characters, not combining marks.

    Returns "" for falsy input rather than raising.
    """
    if not text:
        return text or ""

    if _HAS_FTFY:
        # Repairs classic double-encoding mojibake before we do anything else.
        text = ftfy.fix_text(text)

    # Explicit removal of the Unicode replacement character — this is the
    # symptom reported: pypdf/python-docx emit this for glyphs it can't map
    # to a real character (broken font tables in the source PDF/DOCX).
    text = text.replace(REPLACEMENT_CHAR, "")

    # Normalize compatibility characters/ligatures (e.g. "ﬁ" -> "fi").
    text = unicodedata.normalize("NFKC", text)

    # Strip true control characters (category "Cc") but keep newline/tab/CR
    # and keep combining marks/joiners used by non-Latin scripts intact.
    text = "".join(
        ch for ch in text if ch in ("\n", "\t", "\r") or unicodedata.category(ch) != "Cc"
    )

    # Collapse whitespace runs left behind by stripped characters.
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def sanitize_candidate_strings(data: Any) -> Any:
    """Recursively applies sanitize_text() to every string value in a
    (possibly nested) dict/list structure, leaving non-string values
    (numbers, None, bool) untouched. Used to clean an entire candidate
    dict — including nested skills/experience/education arrays — in one
    call.
    """
    if isinstance(data, str):
        return sanitize_text(data)
    if isinstance(data, list):
        return [sanitize_candidate_strings(v) for v in data]
    if isinstance(data, dict):
        return {k: sanitize_candidate_strings(v) for k, v in data.items()}
    return data


def _split_surrounding_punctuation(word: str) -> tuple[str, str, str]:
    """Splits leading/trailing punctuation (commas, periods, parens) off a
    word so titlecasing logic sees just the letters — e.g. "MCDONALD," ->
    ("", "MCDONALD", ","). Without this, "McDonald," fails the Mc-prefix
    regex simply because of the trailing comma."""
    m = re.match(r"^([^A-Za-z0-9']*)(.*?)([^A-Za-z0-9']*)$", word)
    if not m:
        return "", word, ""
    return m.group(1), m.group(2), m.group(3)


def _titlecase_single_word(word: str) -> str:
    if not word:
        return word

    prefix, core, suffix = _split_surrounding_punctuation(word)
    if not core:
        return word

    lower = core.lower()

    # "McDonald", "McFly" — but not shorter false positives like "Mc".
    m = re.match(r"^(mc)([a-z]+)$", lower)
    if m and len(core) > 2:
        processed = "Mc" + m.group(2).capitalize()
    elif "'" in core:
        # "O'Brien", "D'Angelo"
        parts = core.split("'")
        processed = "'".join(p.capitalize() if p else p for p in parts)
    else:
        processed = core.capitalize()

    return prefix + processed + suffix


def _titlecase_word(word: str) -> str:
    if "-" in word:
        # "Jean-Pierre", "Smith-Jones"
        return "-".join(_titlecase_single_word(part) for part in word.split("-"))
    return _titlecase_single_word(word)


def titlecase_name(name: str) -> str:
    """Title-cases a person's full name, handling common edge cases that
    Python's naive str.title() gets wrong:
        - ALL CAPS or all-lowercase input ("JOHN SMITH" / "john smith")
        - Surname particles that stay lowercase mid-name ("Lars van der Berg")
        - Apostrophes ("O'Brien") and hyphens ("Jean-Pierre")
        - "Mc" prefixes ("McDonald")

    The first word is never lowercased even if it matches a particle
    (e.g., a name that IS just "De Souza" as a surname-first entry).
    """
    if not name or not name.strip():
        return name or ""

    words = name.strip().split()
    result = []
    for i, word in enumerate(words):
        if i != 0 and word.lower() in _LOWERCASE_NAME_PARTICLES:
            result.append(word.lower())
        else:
            result.append(_titlecase_word(word))
    return " ".join(result)
