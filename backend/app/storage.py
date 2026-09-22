"""File storage abstraction.

LocalDiskStorage is the zero-setup default (writes to <upload_dir>/, served via
the /files static mount). AzureBlobStorage is the real deployment target.

Which one is active is picked ONLY from environment variables (see config.py) -
`storage = build_storage()` below never hardcodes a credential or connection
string. Set AZURE_STORAGE_CONNECTION_STRING in the server's .env to switch.

F1 (round 4) added three things:
  * a hard account guard - if AZURE_STORAGE_ACCOUNT_NAME is set and the
    connection string points somewhere else, the app refuses to start rather
    than quietly writing resumes into the wrong storage account;
  * loud startup logging + `describe()`, surfaced on /health, so the rest of the
    team can see which account they are hitting without reading anyone's .env;
  * versioned blob paths ("<candidate_id>/v<n>/<filename>") so a re-upload (F4)
    never overwrites the CV that was screened last month.
"""
from __future__ import annotations

import logging
import mimetypes
import os
import shutil
from datetime import datetime, timedelta, timezone
from typing import Protocol

from .config import settings

log = logging.getLogger("app.storage")


def blob_path_for(candidate_id: str, version_no: int, filename: str) -> str:
    """The storage key for one uploaded CV. Every version keeps its own folder,
    and everything for a candidate stays under a single `<candidate_id>/` prefix
    so delete() can still wipe the lot with one prefix scan."""
    safe_name = os.path.basename(filename).replace("\\", "_") or "resume"
    return f"{candidate_id}/v{max(1, int(version_no))}/{safe_name}"


class Storage(Protocol):
    """Common shape both backends implement - routers only ever call this."""

    def save(self, candidate_id: str, filename: str, content: bytes,
             version_no: int = 1) -> dict: ...
    def delete(self, candidate_id: str) -> None: ...
    def resolve_url(self, candidate_id: str, filename: str) -> str: ...
    def resolve_path_url(self, blob_path: str) -> str: ...
    def describe(self) -> dict: ...


class LocalDiskStorage:
    """Writes uploaded CVs to <upload_dir>/<candidate_id>/v<n>/<filename> and
    serves them back through the /files static mount. Active whenever
    AZURE_STORAGE_CONNECTION_STRING is unset - the default, zero-setup path."""

    def __init__(self, base_dir: str) -> None:
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def save(self, candidate_id: str, filename: str, content: bytes,
             version_no: int = 1) -> dict:
        rel = blob_path_for(candidate_id, version_no, filename)
        path = os.path.join(self.base_dir, *rel.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(content)
        return {
            "url": self.resolve_path_url(rel),
            "filename": rel.rsplit("/", 1)[-1],
            "path": rel,
        }

    def delete(self, candidate_id: str) -> None:
        shutil.rmtree(os.path.join(self.base_dir, candidate_id), ignore_errors=True)

    def resolve_url(self, candidate_id: str, filename: str) -> str:
        """Legacy, un-versioned layout - kept for seeded rows written before F4."""
        return f"{settings.api_base_url}/files/{candidate_id}/{filename}"

    def resolve_path_url(self, blob_path: str) -> str:
        return f"{settings.api_base_url}/files/{blob_path}"

    def describe(self) -> dict:
        return {"backend": "local_disk", "path": os.path.abspath(self.base_dir)}


def _parse_connection_string(conn_str: str) -> dict[str, str]:
    """`Key=Value;Key=Value;...` -> dict. Used only to pull AccountName /
    AccountKey back out for SAS signing - the azure-storage-blob SDK doesn't
    expose them from a client built via from_connection_string()."""
    return dict(part.split("=", 1) for part in conn_str.split(";") if part and "=" in part)


def parse_account_name(conn_str: str) -> str:
    """AccountName out of a connection string, "" if it has none. Never logs or
    returns AccountKey."""
    return _parse_connection_string(conn_str).get("AccountName", "")


class StorageAccountMismatch(RuntimeError):
    """Raised when the connection string points at an unexpected account. This
    is deliberately NOT caught by build_storage()'s fallback - writing personal
    data to the wrong Azure subscription is worse than not booting."""


def check_account(conn_str: str) -> str:
    """F1 guardrail. Returns the account name the connection string points at,
    or raises StorageAccountMismatch."""
    actual = parse_account_name(conn_str)
    expected = settings.azure_storage_account_name.strip()
    company = settings.company_storage_account_name.strip()

    if company and actual == company and not settings.allow_company_storage:
        raise StorageAccountMismatch(
            f"Connection string points at the company storage account '{actual}', "
            f"which we do not own yet. Set ALLOW_COMPANY_STORAGE=true only once "
            f"Inteltion has granted access. Refusing to start."
        )
    if expected and actual != expected:
        raise StorageAccountMismatch(
            f"Storage account mismatch: connection string points at '{actual}', "
            f"expected '{expected}'. Refusing to start."
        )
    return actual


class AzureBlobStorage:
    """Real deployment target. Credentials come ONLY from
    AZURE_STORAGE_CONNECTION_STRING / AZURE_STORAGE_CONTAINER_NAME (env) -
    never hardcoded, never logged.

    Resumes are personal data (PDPA) - the container is NOT made public.
    resolve_url() hands out a short-lived, read-only SAS link instead of a
    permanent public URL; `save()` still records that link as `resume_url` for
    convenience, but callers wanting a guaranteed-fresh link should re-request
    it via GET /api/candidates/{id}/resume-url, which resolves it live.
    """

    def __init__(self, connection_string: str, container_name: str) -> None:
        from azure.core.exceptions import ResourceExistsError
        from azure.storage.blob import BlobServiceClient

        self.account_name = check_account(connection_string)
        self.container_name = container_name
        self._parts = _parse_connection_string(connection_string)
        self._client = BlobServiceClient.from_connection_string(connection_string)
        self._container = self._client.get_container_client(container_name)
        try:
            # Private by default - no public_access argument. PDPA requirement.
            self._container.create_container()
        except ResourceExistsError:
            pass

    def _blob_client(self, blob_path: str):
        return self._container.get_blob_client(blob_path)

    def save(self, candidate_id: str, filename: str, content: bytes,
             version_no: int = 1) -> dict:
        from azure.storage.blob import ContentSettings

        rel = blob_path_for(candidate_id, version_no, filename)
        safe_name = rel.rsplit("/", 1)[-1]
        content_type = mimetypes.guess_type(safe_name)[0] or "application/octet-stream"
        self._blob_client(rel).upload_blob(
            content, overwrite=True,
            content_settings=ContentSettings(content_type=content_type),
        )
        return {"url": self.resolve_path_url(rel), "filename": safe_name, "path": rel}

    def delete(self, candidate_id: str) -> None:
        for blob in self._container.list_blobs(name_starts_with=f"{candidate_id}/"):
            self._container.delete_blob(blob.name)

    def resolve_url(self, candidate_id: str, filename: str) -> str:
        """Legacy, un-versioned layout - kept for rows written before F4."""
        return self.resolve_path_url(f"{candidate_id}/{filename}")

    def resolve_path_url(self, blob_path: str) -> str:
        from azure.storage.blob import BlobSasPermissions, generate_blob_sas

        sas = generate_blob_sas(
            account_name=self._parts.get("AccountName", ""),
            container_name=self.container_name,
            blob_name=blob_path,
            account_key=self._parts.get("AccountKey", ""),
            permission=BlobSasPermissions(read=True),
            expiry=datetime.now(timezone.utc)
            + timedelta(minutes=settings.resume_sas_expiry_minutes),
        )
        return f"{self._blob_client(blob_path).url}?{sas}"

    def describe(self) -> dict:
        # Account + container name only. The key never leaves config.
        return {
            "backend": "azure_blob",
            "account": self.account_name,
            "container": self.container_name,
        }


# Set when Azure was configured but we fell back to local disk anyway. The
# whole point of F1 is that this state is never silent, so it is recorded here
# and re-reported from the app's lifespan - see `log_active_storage()`.
DEGRADED_REASON: str = ""


def describe_line(active: "Storage") -> str:
    """The one-line startup banner, e.g.
    `STORAGE: AzureBlob account=inteltionhrdev container=resumes`."""
    described = active.describe()
    if described.get("backend") == "azure_blob":
        return (
            f"STORAGE: AzureBlob account={described.get('account', '?')} "
            f"container={described.get('container', '?')}"
        )
    return f"STORAGE: LocalDisk path={described.get('path', '?')}"


def log_active_storage() -> None:
    """Emit the storage banner.

    Called from the FastAPI lifespan, NOT from build_storage(). `storage` is
    built at import time, which on a normal boot happens before
    logging.basicConfig() has installed a handler - so anything build_storage()
    logs goes nowhere. That silently defeated the entire point of logging it.
    """
    log.info("%s", describe_line(storage))
    if DEGRADED_REASON:
        log.warning(
            "STORAGE: Azure Blob was configured but init failed (%s) - RUNNING ON "
            "LOCAL DISK. Uploaded CVs land on this container's ephemeral "
            "filesystem and disappear when it restarts.", DEGRADED_REASON,
        )


def build_storage() -> Storage:
    global DEGRADED_REASON

    if settings.using_azure_storage:
        try:
            return AzureBlobStorage(
                settings.azure_storage_connection_string,
                settings.azure_storage_container_name,
            )
        except StorageAccountMismatch:
            # Never fall back past this - see StorageAccountMismatch.
            raise
        except Exception as exc:  # bad creds / no network - don't crash the API
            DEGRADED_REASON = str(exc)
    return LocalDiskStorage(settings.upload_dir)


storage = build_storage()
