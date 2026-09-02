import os

from .config import settings


class LocalDiskStorage:
    """Writes uploaded CVs to <upload_dir>/<candidate_id>/<filename> and serves
    them back through the /files static mount. Day-6+: add an AzureBlobStorage
    class with the same .save() signature and pick it via an env flag."""

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
            "url": f"{settings.api_base_url}/files/{candidate_id}/{safe_name}",
            "filename": safe_name,
            "path": path,
        }


storage = LocalDiskStorage(settings.upload_dir)
