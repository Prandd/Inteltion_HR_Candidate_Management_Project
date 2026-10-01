"""F1 - the account guardrail. Pure unit tests, no Azure account needed.

These cover the check itself. The thing they CANNOT cover is the one the round
actually needs: a real end-to-end write against a live storage account. See the
note in backend/CHANGELOG.md.
"""
import pytest

from app.config import settings
from app.storage import (
    LocalDiskStorage,
    StorageAccountMismatch,
    blob_path_for,
    check_account,
    describe_line,
    parse_account_name,
)

OURS = (
    "DefaultEndpointsProtocol=https;AccountName=inteltionhrdev;"
    "AccountKey=Zm9vYmFyYmF6;EndpointSuffix=core.windows.net"
)
THEIRS = (
    "DefaultEndpointsProtocol=https;AccountName=inteltioncorp;"
    "AccountKey=Zm9vYmFyYmF6;EndpointSuffix=core.windows.net"
)


def test_account_name_is_parsed_without_leaking_the_key():
    assert parse_account_name(OURS) == "inteltionhrdev"
    assert "AccountKey" not in parse_account_name(OURS)


def test_expected_account_passes(monkeypatch):
    monkeypatch.setattr(settings, "azure_storage_account_name", "inteltionhrdev")
    assert check_account(OURS) == "inteltionhrdev"


def test_unexpected_account_refuses_to_start(monkeypatch):
    monkeypatch.setattr(settings, "azure_storage_account_name", "inteltionhrdev")
    with pytest.raises(StorageAccountMismatch) as exc:
        check_account(THEIRS)
    assert "inteltioncorp" in str(exc.value)
    assert "AccountKey" not in str(exc.value), "the key must never reach a log line"


def test_company_account_is_blocked_unless_explicitly_allowed(monkeypatch):
    monkeypatch.setattr(settings, "azure_storage_account_name", "")
    monkeypatch.setattr(settings, "company_storage_account_name", "inteltioncorp")
    monkeypatch.setattr(settings, "allow_company_storage", False)
    with pytest.raises(StorageAccountMismatch):
        check_account(THEIRS)

    monkeypatch.setattr(settings, "allow_company_storage", True)
    assert check_account(THEIRS) == "inteltioncorp"


def test_no_expectation_configured_means_no_guard(monkeypatch):
    """Nobody has provisioned anything yet - the default must still boot."""
    monkeypatch.setattr(settings, "azure_storage_account_name", "")
    monkeypatch.setattr(settings, "company_storage_account_name", "")
    assert check_account(OURS) == "inteltionhrdev"


def test_versioned_blob_paths_never_collide():
    assert blob_path_for("0000001", 1, "cv.pdf") == "0000001/v1/cv.pdf"
    assert blob_path_for("0000001", 2, "cv.pdf") == "0000001/v2/cv.pdf"
    # Path traversal in a filename must not escape the candidate's prefix.
    assert blob_path_for("0000001", 1, "../../etc/passwd") == "0000001/v1/passwd"
    assert blob_path_for("0000001", 1, "") == "0000001/v1/resume"


def test_local_disk_describe_reports_the_backend(tmp_path):
    described = LocalDiskStorage(str(tmp_path)).describe()
    assert described["backend"] == "local_disk"
    assert "path" in described


def test_startup_banner_names_the_backend(tmp_path):
    """The banner is what tells a deploy it is writing to the wrong place. It is
    emitted from the app lifespan, not from build_storage() - at import time
    logging has no handler yet and the line vanished."""
    line = describe_line(LocalDiskStorage(str(tmp_path)))
    assert line.startswith("STORAGE: LocalDisk path=")

    class _FakeAzure:
        def describe(self):
            return {"backend": "azure_blob", "account": "inteltionhrdev",
                    "container": "resumes"}

    line = describe_line(_FakeAzure())
    assert line == "STORAGE: AzureBlob account=inteltionhrdev container=resumes"


def test_the_app_lifespan_actually_logs_the_banner(client, caplog):
    """Regression guard for the real bug: the banner was being written before
    logging had a handler, so nothing ever reached the log."""
    import logging as _logging

    from app.storage import log_active_storage

    with caplog.at_level(_logging.INFO, logger="app.storage"):
        log_active_storage()
    assert any(r.message.startswith("STORAGE: ") for r in caplog.records)
