# llm-service — CV Extraction Engine (Member 4)

Owns: `extract_candidate(file_bytes: bytes, filename: str | None = None) -> dict`

## Files
| File | Purpose |
|---|---|
| `extractor.py` | Public entry point — orchestrates the full pipeline. **This is the only file Member 3 imports from.** |
| `pdf_docx_reader.py` | Raw text extraction from PDF/DOCX. |
| `prompt.py` | System prompt + few-shot example (enforces nested `skills`/`experience` shape). |
| `llm_client.py` | Azure OpenAI call wrapper (JSON mode, retry). |
| `schema.py` | Pydantic model = the frozen contract. Also the "repair" layer. |
| `experience_calc.py` | Computes `experience_total` from parsed dates — never trusts the LLM's arithmetic. |
| `fallback.py` | Hardcoded, always-valid fallback candidate (confidence=0.0) for when extraction can't complete. |
| `run_test_harness.py` | Day 5 test harness — run against `sample_cvs/`. |

## Setup
```bash
cd llm-service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
Fill in `.env` at the repo root (see main README.md Section 4) with:
```
CV_SCORING_PROVIDER=azure_openai
AZURE_OPENAI_ENDPOINT=https://<your-resource-name>.openai.azure.com/
AZURE_OPENAI_API_KEY=<key>
AZURE_OPENAI_DEPLOYMENT=<deployment-name>
```

## Run the test harness
```bash
python run_test_harness.py
```
Drop 5-10 real/synthetic CVs (`.pdf`/`.docx`) into `sample_cvs/` first.

## Integration with Member 3 (backend)
```python
# inside backend/app/routers/candidates.py, roughly:
import sys
sys.path.append("../llm-service")  # or install as a local package
from extractor import extract_candidate

@router.post("/api/candidates/upload")
async def upload_candidate(file: UploadFile):
    file_bytes = await file.read()
    extracted = extract_candidate(file_bytes, filename=file.filename)
    extracted["candidate_id"] = str(uuid4())  # backend assigns this
    # ... persist `extracted` to Postgres ...
    return extracted
```

## Guarantees
- **Never raises** for expected failure modes (bad file, LLM/provider errors, malformed JSON) — always returns a schema-valid dict.
- `hr_comment`, `line_manager_comment`, `applied_position` always `""`; `candidate_id` always `null`.
- `full_name` is always returned in ALL CAPS (enforced in `schema.py`, holds even if the LLM ignores the prompt instruction).
- `experience_total` is always computed by `experience_calc.py`, never by the LLM.
- Fallback responses are flagged with `extraction_confidence: 0.0` so the dashboard (Member 1) can visually surface them for manual review.

## Recent changes
- `full_name`: capitalization is now forced to uppercase at the schema level.
- `applied_position`: always returned as `""` — HR assigns this manually after upload; it's never inferred from the CV, since a resume doesn't reliably state which specific open role it's targeting.
