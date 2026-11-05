"""app/llm_client.py must not quietly substitute the mock extractor.

The mock invents a name, email and skills from a hash of the file. If a
deployment loses the real extractor (a missing COPY, a missing dependency) and
the dispatcher falls back to it silently, every upload fills the HR system with
plausible-looking fake applicants and nobody notices.
"""
import sys

import pytest

from app import llm_client


@pytest.fixture
def no_real_extractor(monkeypatch):
    monkeypatch.delenv("LLM_SERVICE_URL", raising=False)
    # A None entry in sys.modules makes `from extractor import ...` raise
    # ImportError - the same thing a missing dependency does.
    monkeypatch.setitem(sys.modules, "extractor", None)


def test_missing_extractor_is_an_error_not_a_mock(no_real_extractor, monkeypatch):
    monkeypatch.delenv("ALLOW_MOCK_EXTRACTION", raising=False)
    with pytest.raises(RuntimeError, match="CV extraction is unavailable"):
        llm_client.extract_candidate(b"%PDF-1.4 anything", filename="cv.pdf")


def test_mock_is_available_only_when_explicitly_allowed(no_real_extractor, monkeypatch):
    monkeypatch.setenv("ALLOW_MOCK_EXTRACTION", "true")
    out = llm_client.extract_candidate(b"%PDF-1.4 anything", filename="cv.pdf")
    assert "[MOCK EXTRACTION" in out["raw_text_snippet"]
