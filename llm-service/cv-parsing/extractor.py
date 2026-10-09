"""
extractor.py — the single public entry point for this module.

    extract_candidate(file_bytes: bytes, filename: str | None = None) -> dict

This is the exact function signature agreed in Section 2.4 of the sprint
plan (a direct Python import, the recommended default for a 7-day sprint).
Member 3 imports this directly from `llm-service/` and calls it from
inside `POST /api/candidates/upload`. Nothing here touches the API, the
database, or any UI.

Pipeline:
    1. Extract raw text from the uploaded file (PDF/DOCX).
    2. Call the LLM with the frozen schema + few-shot prompt, in JSON mode.
    3. Parse + validate the response against the Pydantic schema (this is
       also the "repair pass" — missing/invalid fields silently get their
       agreed defaults instead of raising).
    4. Force `hr_comment`, `line_manager_comment`, `applied_position`, and
       `candidate_id` to their required empty/null values regardless of
       what the LLM did.
    5. Overwrite `experience_total` with the programmatically-computed
       value — the LLM's own arithmetic is never trusted.
    5b. `full_name` is always title-cased (enforced in schema.py's
       validator, applied on every construction of CandidateExtraction —
       including this step, the initial validation, and the fallback path).
    5c. `summary` is guaranteed non-empty: if the LLM returned nothing
       usable, a strictly factual one-line summary is derived from
       already-extracted experience/skills only — never fabricated.
    5d. Every string field — including nested skills/experience/education
       entries — is passed through a sanitizer (schema.py's model
       validator) that strips mojibake and the Unicode replacement
       character ('\ufffd') left behind by PDFs with broken font tables.
    6. On ANY unrecoverable failure along the way, return the hardcoded
       fallback (schema-valid, confidence=0.0) instead of raising —
       a malformed response must never crash the pipeline.
"""
from __future__ import annotations

import json
import logging
from typing import Optional

from pydantic import ValidationError

from experience_calc import compute_experience_total
from fallback import build_fallback_candidate
from llm_client import LLMCallError, LLMConfigError, call_llm_json
from pdf_docx_reader import TextExtractionError, UnsupportedFileTypeError, extract_text
from prompt import build_messages
from schema import CandidateExtraction
from summary_fallback import build_fallback_summary

logger = logging.getLogger("llm_service.extractor")

# Fields the LLM is never allowed to author, enforced unconditionally
# after validation regardless of what came back in the raw response.
# - hr_comment / line_manager_comment: HR-entered post-upload, not on the CV.
# - applied_position: assigned/edited by HR after upload, not inferred
#   from the CV (a resume doesn't reliably say which open role it's for).
_FORCE_EMPTY_STRING_FIELDS = ("hr_comment", "line_manager_comment", "applied_position")


def _parse_json_response(raw_json_str: str) -> dict:
    """Parses the LLM's raw string response into a dict.

    Handles the common failure mode of a model wrapping JSON in markdown
    code fences even when JSON mode is requested, before giving up.
    """
    text = raw_json_str.strip()
    if text.startswith("```"):
        # Strip ```json ... ``` or ``` ... ``` fences defensively.
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()

    return json.loads(text)  # raises json.JSONDecodeError on failure


def _validate_and_repair(raw_dict: dict, raw_text_snippet: str) -> CandidateExtraction:
    """Validates the raw LLM dict against the schema.

    Pydantic's default-filling IS the repair layer here: any missing key,
    wrong type coerced by our field_validators, or extra hallucinated key
    (ignored) results in a still-valid CandidateExtraction rather than an
    exception, as long as the payload is at least a JSON object.
    """
    if not isinstance(raw_dict, dict):
        raise ValueError(f"Expected a JSON object, got {type(raw_dict).__name__}")

    # Ensure raw_text_snippet is populated even if the model omitted it —
    # useful for debugging regardless of what the LLM chose to return.
    raw_dict.setdefault("raw_text_snippet", raw_text_snippet[:500])

    return CandidateExtraction(**raw_dict)


def _apply_hard_business_rules(
    candidate: CandidateExtraction, raw_text: str
) -> CandidateExtraction:
    """Applies the non-negotiable rules from Section 2.1 regardless of what
    the LLM produced:
        - hr_comment / line_manager_comment are always "".
        - applied_position is always "" (HR assigns this after upload).
        - candidate_id is always None (backend-assigned).
        - experience_total is always computed programmatically, never
          trusted from the LLM.
        - full_name is always title-cased (enforced by schema.py's
          validator, which fires again on this re-construction).
        - summary is guaranteed non-empty and non-fabricated (see below).
    """
    data = candidate.model_dump()

    for field in _FORCE_EMPTY_STRING_FIELDS:
        data[field] = ""

    data["candidate_id"] = None

    experience_dicts = [exp for exp in data.get("experience", [])]
    data["experience_total"] = compute_experience_total(experience_dicts)

    # Guarantee a non-empty, non-fabricated summary. If the LLM left it
    # blank (or the prompt-level instruction to avoid fabrication caused it
    # to leave a sparse CV's summary empty), derive a strictly factual
    # one-liner from fields we've ALREADY extracted and validated — never
    # invent new facts here either.
    summary = (data.get("summary") or "").strip()
    data["summary"] = summary if summary else build_fallback_summary(data)

    return CandidateExtraction(**data)


def extract_candidate(file_bytes: bytes, filename: Optional[str] = None) -> dict:
    """Extracts structured candidate data from a CV file.

    Args:
        file_bytes: raw bytes of the uploaded CV (PDF or DOCX).
        filename: optional original filename (helps with type detection
            and shows up in logs; not required).

    Returns:
        A dict matching the frozen candidate schema exactly. This
        function NEVER raises for expected failure modes (bad file,
        LLM/provider errors, malformed JSON) — it always returns a
        schema-valid dict, falling back to build_fallback_candidate()
        when extraction cannot be completed.
    """
    raw_text = ""

    # --- Step 1: text extraction ---
    try:
        raw_text = extract_text(file_bytes, filename=filename)
    except (UnsupportedFileTypeError, TextExtractionError) as e:
        logger.warning("Text extraction failed for %s: %s", filename, e)
        return build_fallback_candidate(reason=f"text_extraction_failed: {e}")
    except Exception as e:  # noqa: BLE001 - last-resort safety net
        logger.exception("Unexpected error during text extraction for %s", filename)
        return build_fallback_candidate(reason=f"unexpected_text_extraction_error: {e}")

    # --- Step 2: LLM call (with one retry, handled inside call_llm_json) ---
    try:
        messages = build_messages(raw_text)
        raw_json_str = call_llm_json(messages, max_retries=1)
    except (LLMConfigError, LLMCallError) as e:
        logger.warning("LLM call failed for %s: %s", filename, e)
        return build_fallback_candidate(raw_text_snippet=raw_text, reason=f"llm_call_failed: {e}")
    except Exception as e:  # noqa: BLE001
        logger.exception("Unexpected error during LLM call for %s", filename)
        return build_fallback_candidate(
            raw_text_snippet=raw_text, reason=f"unexpected_llm_error: {e}"
        )

    # --- Step 3: parse + validate/repair ---
    try:
        raw_dict = _parse_json_response(raw_json_str)
        candidate = _validate_and_repair(raw_dict, raw_text)
    except (json.JSONDecodeError, ValidationError, ValueError) as e:
        # One repair attempt: re-ask the model with an explicit correction
        # instruction before giving up entirely. Cheap and catches the
        # "almost-JSON" failure mode (trailing commas, stray text).
        logger.info("First parse/validation failed for %s (%s); attempting repair re-ask.", filename, e)
        try:
            repair_messages = build_messages(raw_text) + [
                {"role": "assistant", "content": raw_json_str},
                {
                    "role": "user",
                    "content": (
                        "That response was not valid JSON matching the schema "
                        f"(error: {e}). Return ONLY the corrected, valid JSON "
                        "object now — no explanation, no markdown."
                    ),
                },
            ]
            raw_json_str_retry = call_llm_json(repair_messages, max_retries=0)
            raw_dict = _parse_json_response(raw_json_str_retry)
            candidate = _validate_and_repair(raw_dict, raw_text)
        except Exception as repair_error:  # noqa: BLE001
            logger.warning(
                "Repair re-ask also failed for %s: %s", filename, repair_error
            )
            return build_fallback_candidate(
                raw_text_snippet=raw_text,
                reason=f"malformed_json_after_repair: {repair_error}",
            )

    # --- Step 4: enforce non-negotiable business rules ---
    try:
        candidate = _apply_hard_business_rules(candidate, raw_text)
    except Exception as e:  # noqa: BLE001
        logger.exception("Failed applying business rules for %s", filename)
        return build_fallback_candidate(
            raw_text_snippet=raw_text, reason=f"post_processing_failed: {e}"
        )

    return candidate.to_output_dict()
