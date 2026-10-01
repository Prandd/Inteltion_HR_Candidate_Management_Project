"""MOCK CV extraction engine.

Stand-in for Member 4's real function in `llm-service/`.
Frozen interface (agreed Day 1):

    extract_candidate(file_bytes: bytes) -> dict   # matches shared-contracts/schema.json

Day 6 integration = change ONE import in app/routers/candidates.py:

    from ..extraction import extract_candidate          # <- remove this
    from llm_service.extract import extract_candidate    # <- add the real one

Nothing else changes as long as the returned dict still matches the schema.

This mock is a PURE FUNCTION of the file bytes: same bytes in, same candidate
out, every time, in every process. Nothing here calls an unseeded random number
generator. `random.Random(seed)` is used only as a deterministic table lookup -
a way to pick "which name, which skills" from the fixture lists - and `seed` is
the SHA-256 of the file.

That matters beyond tidiness. F4 decides whether a CV belongs to an existing
candidate by comparing the extracted email, so an extractor that answers
differently for the same file would file one person under two records - exactly
the bug F4 exists to fix.
"""
from __future__ import annotations

import hashlib
import random

_FIRST = ["Somchai", "Ariya", "Nattapong", "Kanya", "Thanakorn",
          "Pimchanok", "Chalermsak", "Warunee", "Peerapat", "Sasithorn"]
_LAST = ["Srisai", "Wong", "Chaicharoen", "Rattanakul", "Boonmee",
         "Intira", "Phumipat", "Kittisak"]
_POSITIONS = ["Backend Engineer", "Data Engineer", "Frontend Engineer",
              "Machine Learning Engineer", "DevOps Engineer", "Full-Stack Developer"]
_SKILLS = [
    ("Python", ["FastAPI", "Django", "pandas"]),
    ("JavaScript", ["React", "Node.js", "TypeScript"]),
    ("SQL", ["PostgreSQL", "BigQuery", "MySQL"]),
    ("Cloud", ["Azure", "AWS", "GCP"]),
    ("Data Engineering", ["Airflow", "dbt", "Spark"]),
    ("DevOps", ["Docker", "Kubernetes", "Terraform"]),
]
_COMPANIES = ["Inteltion", "SCB TechX", "Agoda", "LINE MAN Wongnai",
              "KBTG", "Sertis", "Pomelo", "Ascend Money"]
_UNIS = ["Chulalongkorn University", "Chiang Mai University",
         "Kasetsart University", "Thammasat University", "KMUTT"]
_EDU_FIELDS = ["Computer Engineering", "Computer Science",
               "Information Technology", "Data Science", "Software Engineering"]

def _mock_candidate(seed: int) -> dict:
    rnd = random.Random(seed)
    first, last = rnd.choice(_FIRST), rnd.choice(_LAST)
    position = rnd.choice(_POSITIONS)

    skills = [
        {"skill": name, "tools": rnd.sample(tools, rnd.randint(1, len(tools)))}
        for name, tools in rnd.sample(_SKILLS, rnd.randint(1, 4))
    ]

    years_total = rnd.randint(1, 12)
    n_exp = rnd.randint(1, 3)
    experience = []
    end_year = 2026
    for i in range(n_exp):
        span = max(1, rnd.randint(1, years_total // n_exp + 1))
        start_year = end_year - span
        experience.append({
            "company": rnd.choice(_COMPANIES),
            "position": position if i == 0 else rnd.choice(_POSITIONS),
            "start_date": f"{start_year}-{rnd.randint(1, 12):02d}",
            "end_date": "Present" if i == 0 else f"{end_year}-{rnd.randint(1, 12):02d}",
            "description": (
                f"Built {rnd.choice(['payments', 'search', 'data pipelines', 'internal tools', 'ML services'])} "
                f"with {', '.join(skills[0]['tools'][:2]) or skills[0]['skill']}."
            ),
        })
        end_year = start_year

    has_salary = rnd.random() > 0.35
    return {
        "full_name": f"{first} {last}",
        # Taken straight off the seed, not drawn from `rnd`: the email is the
        # identity key F4 matches on, so it should be readable as a plain
        # function of the file rather than as one more draw from a generator.
        # The suffix also widens the name space from 80 combinations (10 first
        # names x 8 last names) to 8000, so two unrelated mock CVs are unlikely
        # to collide on email and get merged into a single candidate.
        "email": f"{first.lower()}.{last.lower()}{seed % 100:02d}@example.com",
        "phone": f"08{rnd.randint(10_000_000, 99_999_999)}",
        "location": rnd.choice(
            ["Bangkok, Thailand", "Chiang Mai, Thailand", "Remote", "Nonthaburi, Thailand"]
        ),
        "applied_position": position,
        "summary": (
            f"{position} with {years_total} years of experience. "
            f"Strong in {skills[0]['skill']}, comfortable across the stack."
        ),
        "skills": skills,
        "experience": experience,
        "experience_total": float(years_total),
        "current_salary": float(rnd.randint(4, 12) * 10_000) if has_salary else 0.0,
        "expected_salary": float(rnd.randint(6, 16) * 10_000) if has_salary else 0.0,
        "education": [{
            "institution": rnd.choice(_UNIS),
            "degree": rnd.choice(["B.Eng.", "B.Sc.", "M.Sc."]),
            "field": rnd.choice(_EDU_FIELDS),
            "year": str(2026 - years_total - rnd.randint(0, 2)),
        }],
        "hr_comment": "",
        "line_manager_comment": "",
        "extraction_confidence": round(rnd.uniform(0.72, 0.98), 2),
        "raw_text_snippet": (
            f"[MOCK EXTRACTION seed={seed}] Real parsing arrives from llm-service on Day 6."
        ),
        "status": "New",
    }


def extract_candidate(file_bytes: bytes, filename: str | None = None) -> dict:
    """Return a schema-valid candidate dict. Mock: the file is not parsed, but
    the output is DERIVED from its bytes.

    Signature matches Member 4's real llm-service function exactly
    (extractor.py: `extract_candidate(file_bytes, filename=None) -> dict`),
    so the Day 6 swap is a one-line import change. Member 4's output does
    NOT include `location` / `status` - the backend adds those (status
    defaults to "New", location stays "" until HR fills it).

    The seed is the content hash, not a random number. Round 4 made this matter:
    F4 decides "same candidate" from the extracted email, so re-uploading the
    same CV has to yield the same person. A random seed made every re-upload
    look like a new applicant, which is precisely the bug F4 exists to fix - and
    it would have made the feature impossible to test or demo.
    """
    seed = int.from_bytes(hashlib.sha256(file_bytes).digest()[:8], "big")
    return _mock_candidate(seed)
