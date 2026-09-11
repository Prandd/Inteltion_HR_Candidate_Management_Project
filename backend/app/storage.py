"""File storage abstraction.

LocalDiskStorage is the zero-setup default (writes to <upload_dir>/, served via
the /files static mount). AzureBlobStorage is the real deployment target.

Which one is active is picked ONLY from environment variables (see config.py) -
`storage = build_storage()` below never hardcodes a credential or connection
string. Set AZURE_STORAGE_CONNECTION_STRING in the server's .env to switch.
"""
from __future__ import annotations

import mimetypes
import os
import shutil
from datetime import datetime, timedelta, timezone
from typing import Protocol

from .config import settings


class Storage(Protocol):
    """Common shape both backends implement - routers only ever call this."""

    def save(self, candidate_id: str, filename: str, content: bytes) -> dict: ...
    def delete(self, candidate_id: str) -> None: ...
    def resolve_url(self, candidate_id: str, filename: str) -> str: ...


class LocalDiskStorage:
    """Writes uploaded CVs to <upload_dir>/<candidate_id>/<filename> and serves
    them back through the /files static mount. Active whenever
    AZURE_STORAGE_CONNECTION_STRING is unset - the default, zero-setup path."""

    def __init__(self, base_dir: str) -> None:
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def save(self, candidate_id: str, filename: str, content: bytes) -> dict:
        safe_name = os.path.basename(filename).replace("\\", "_") or "resume"
        folder = os.path.join(self.base_dir, candidate_id)
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, safe_name)
        with open(path, "wb") as fh:
            fh.write(content)
        return {
            "url": self.resolve_url(candidate_id, safe_name),
            "filename": safe_name,
            "path": path,
        }

    def delete(self, candidate_id: str) -> None:
        shutil.rmtree(os.path.join(self.base_dir, candidate_id), ignore_errors=True)

    def resolve_url(self, candidate_id: str, filename: str) -> str:
        return f"{settings.api_base_url}/files/{candidate_id}/{filename}"


def _parse_connection_string(conn_str: str) -> dict[str, str]:
    """`Key=Value;Key=Value;...` -> dict. Used only to pull AccountName /
    AccountKey back out for SAS signing - the azure-storage-blob SDK doesn't
    expose them from a client built via from_connection_string()."""
    return dict(part.split("=", 1) for part in conn_str.split(";") if part and "=" in part)


class AzureBlobStorage:
    """Real deployment target. Credentials come ONLY from
    AZURE_STORAGE_CONNECTION_STRING / AZURE_STORAGE_CONTAINER_NAME (env) -
    never hardcoded, never logged.

    Resumes are personal data (PDPA) - the container is NOT made public.
    resolve_url() hands out a short-lived, read-only SAS link instead of a
    permanent public URL; `save()` still records that link as `resume_url` for
    convenience, but callers wanting a guaranteed-fresh link should re-request
    it via GET /api/candidates/{id}/resume-url, which calls resolve_url() live.
    """

    def __init__(self, connection_string: str, container_name: str) -> None:
        from azure.core.exceptions import ResourceExistsError
        from azure.storage.blob import BlobServiceClient

        self.container_name = container_name
        self._parts = _parse_connection_string(connection_string)
        self._client = BlobServiceClient.from_connection_string(connection_string)
        self._container = self._client.get_container_client(container_name)
        try:
            self._container.create_container()
        except ResourceExistsError:
            pass

    def _blob_client(self, candidate_id: str, filename: str):
        return self._container.get_blob_client(f"{candidate_id}/{filename}")

    def save(self, candidate_id: str, filename: str, content: bytes) -> dict:
        from azure.storage.blob import ContentSettings

        safe_name = os.path.basename(filename).replace("\\", "_") or "resume"
        content_type = mimetypes.guess_type(safe_name)[0] or "application/octet-stream"
        self._blob_client(candidate_id, safe_name).upload_blob(
            content, overwrite=True, content_settings=ContentSettings(content_type=content_type)
        )
        return {
            "url": self.resolve_url(candidate_id, safe_name),
            "filename": safe_name,
            "path": f"{candidate_id}/{safe_name}",
        }

    def delete(self, candidate_id: str) -> None:
        for blob in self._container.list_blobs(name_starts_with=f"{candidate_id}/"):
            self._container.delete_blob(blob.name)

    def resolve_url(self, candidate_id: str, filename: str) -> str:
        from azure.storage.blob import BlobSasPermissions, generate_blob_sas

        account_name = self._parts.get("AccountName", "")
        account_key = self._parts.get("AccountKey", "")
        sas = generate_blob_sas(
            account_name=account_name,
            container_name=self.container_name,
            blob_name=f"{candidate_id}/{filename}",
            account_key=account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.now(timezone.utc)
            + timedelta(minutes=settings.resume_sas_expiry_minutes),
        )
        return f"{self._blob_client(candidate_id, filename).url}?{sas}"


def build_storage() -> Storage:
    if settings.using_azure_storage:
        try:
            return AzureBlobStorage(
                settings.azure_storage_connection_string,
                settings.azure_storage_container_name,
            )
        except Exception as exc:  # bad creds / no network - don't crash the API
            print(f"[storage] Azure Blob init failed ({exc}); falling back to local disk")
    return LocalDiskStorage(settings.upload_dir)


storage = build_storage()
