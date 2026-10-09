"""
prompt.py — system prompt + few-shot example for CV extraction.

Design notes (per Section 3 of the sprint plan):
- `skills` must come back as [{skill, tools}], not a flat string list —
  LLMs default to flattening this unless shown an explicit example.
- `experience_total`, `hr_comment`, `line_manager_comment`, and
  `candidate_id` are explicitly forbidden from the model's own judgment —
  they're computed/injected by other layers, never by the LLM.
- We ask for JSON-only output; combined with response_format={"type":
  "json_object"} on the Azure OpenAI call (see llm_client.py), this
  eliminates the vast majority of malformed-JSON failures.
"""
from __future__ import annotations

import json

SYSTEM_PROMPT = """You are a precise CV/resume information extraction engine. \
You read raw text extracted from a candidate's CV and output ONLY a single \
JSON object matching the exact schema you are given. You do not add \
commentary, markdown formatting, or explanation — JSON only.

Rules you must follow exactly:
1. Output must be valid JSON and must contain every key from the schema, \
even if the value is an empty string, empty array, or 0.
2. `skills` MUST be an array of objects shaped like {"skill": "...", \
"tools": ["...", "..."]}. NEVER output skills as a flat list of strings.
3. `experience` and `education` are arrays of objects. Use "YYYY-MM" for \
dates when a month is known, "YYYY" if only a year is known, and the \
literal string "Present" for an ongoing role. Never invent a date that \
is not supported by the text.
4. Do NOT calculate `experience_total` yourself — always return it as 0. \
A separate system computes it deterministically from the experience dates.
5. `current_salary` and `expected_salary` are numbers. If the CV does not \
explicitly state a figure, return 0 — never estimate, infer, or guess a \
number from job title or seniority.
6. `hr_comment` and `line_manager_comment` are always "" (empty string). \
These fields are filled in later by HR staff, never by you, and never \
appear in the source CV.
7. `candidate_id` is always null. It is assigned by a separate backend \
system after your extraction runs.
7b. `applied_position` is always "" (empty string), even if the CV \
mentions a job title it targets or a cover letter names a role. HR \
assigns/edits this manually after upload — never infer or copy it from \
the CV text.
7c. `full_name` should be returned in standard title-case capitalization \
regardless of how it appears on the CV (e.g., "Jane Doe" whether the CV \
shows "JANE DOE", "jane doe", or "Jane Doe"). A downstream system also \
normalizes this, so approximate it — do not worry about rare surname \
capitalization conventions (e.g., "van der Berg", "O'Brien").
8. `extraction_confidence` is your own honest 0-1 estimate of how \
complete and unambiguous the extraction was for this specific document \
(e.g., lower it if the CV was sparse, poorly formatted, or ambiguous \
about dates/skills).
9. `raw_text_snippet` should be the first ~500 characters of the input \
text, verbatim, for debugging purposes only.
10. If a field genuinely cannot be found in the text, use an empty \
string "" (or empty array [] / 0 for numeric or list fields) — never \
fabricate a plausible-sounding value.
11. `summary` must be a concise 1-3 sentence synopsis built ONLY from \
information explicitly present in the CV text — never invent years of \
experience, achievements, skills, or seniority that aren't already \
stated or directly evidenced elsewhere in the document. If the CV has \
its own summary/objective section, base yours closely on it. `summary` \
must NEVER be an empty string: if the CV is sparse, write the shortest \
strictly-true sentence you can from whatever IS present (e.g., a single \
job title and company is enough for "Worked as {title} at {company}.").
12. Never reproduce garbled characters, encoding artifacts, or the \
Unicode replacement character (�) in any field, even if the source text \
contains them. If a word or character is unreadable/corrupted in the \
input, omit just that character or word rather than copying the garbled \
symbol into your output.
"""

_FEW_SHOT_INPUT = """John A. Rivera
Email: john.rivera@example.com | Phone: +1 555-0134
Applying for: Senior Backend Engineer

Summary: Backend engineer with 6+ years building distributed systems in \
Python and Go. Enjoys mentoring and API design.

Skills:
- Backend: Python, Go, FastAPI, gRPC
- Databases: PostgreSQL, Redis
- Cloud: AWS (Lambda, ECS), Terraform

Experience:
Acme Corp — Senior Backend Engineer (2021-03 to Present)
Led the migration of the payments service from a monolith to gRPC \
microservices, reducing p99 latency by 40%.

Globex Inc — Backend Engineer (2018-06 to 2021-02)
Built internal tooling APIs used by 50+ engineers.

Education:
B.Sc. Computer Science, University of Springfield, 2018

Current salary: not specified
Expected salary: $145,000
"""

_FEW_SHOT_OUTPUT = {
    "candidate_id": None,
    "full_name": "John A. Rivera",
    "email": "john.rivera@example.com",
    "phone": "+1 555-0134",
    "applied_position": "",
    "summary": "Backend engineer with 6+ years building distributed systems in Python and Go. Enjoys mentoring and API design.",
    "skills": [
        {"skill": "Backend", "tools": ["Python", "Go", "FastAPI", "gRPC"]},
        {"skill": "Databases", "tools": ["PostgreSQL", "Redis"]},
        {"skill": "Cloud", "tools": ["AWS (Lambda, ECS)", "Terraform"]},
    ],
    "experience": [
        {
            "company": "Acme Corp",
            "position": "Senior Backend Engineer",
            "start_date": "2021-03",
            "end_date": "Present",
            "description": "Led the migration of the payments service from a monolith to gRPC microservices, reducing p99 latency by 40%.",
        },
        {
            "company": "Globex Inc",
            "position": "Backend Engineer",
            "start_date": "2018-06",
            "end_date": "2021-02",
            "description": "Built internal tooling APIs used by 50+ engineers.",
        },
    ],
    "experience_total": 0,
    "current_salary": 0,
    "expected_salary": 145000,
    "education": [
        {
            "institution": "University of Springfield",
            "degree": "B.Sc.",
            "field": "Computer Science",
            "year": "2018",
        }
    ],
    "hr_comment": "",
    "line_manager_comment": "",
    "extraction_confidence": 0.93,
    "raw_text_snippet": _FEW_SHOT_INPUT[:500],
}


def build_messages(raw_cv_text: str) -> list[dict]:
    """Builds the chat message list for the extraction call, including the
    system prompt and a single few-shot example demonstrating the exact
    schema shape (particularly the nested `skills` structure)."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"CV TEXT:\n\"\"\"\n{_FEW_SHOT_INPUT}\n\"\"\""},
        {"role": "assistant", "content": json.dumps(_FEW_SHOT_OUTPUT, ensure_ascii=False)},
        {
            "role": "user",
            "content": (
                "Now extract the following CV text into the same JSON schema. "
                "Output JSON only, no other text.\n\nCV TEXT:\n\"\"\"\n"
                f"{raw_cv_text}\n\"\"\""
            ),
        },
    ]
