import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All runtime config. Reads backend/.env if present; every value has a
    working default so the mock backend runs with no .env file at all."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    database_url: str = "sqlite:///./data/dev.db"
    cors_origins: str = "http://localhost:5173,http://localhost:5174"
    upload_dir: str = "./data/uploads"
    seed_file: str = "../shared-contracts/mock-candidates.json"
    api_base_url: str = "http://localhost:8000"
    max_upload_mb: int = 10

    # ---- Auth (single Admin/HR account) ----
    auth_username: str = "admin"
    auth_password: str = "password123"
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480  # 8h

    # ---- File storage. Empty connection string (the default) -> local disk,
    # zero setup. Set AZURE_STORAGE_CONNECTION_STRING to switch to Azure Blob -
    # see app/storage.py. Never hardcode the real value here. ----
    azure_storage_connection_string: str = ""
    azure_storage_container_name: str = "resumes"
    resume_sas_expiry_minutes: int = 60  # how long a resolved resume link stays valid

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def using_azure_storage(self) -> bool:
        return bool(self.azure_storage_connection_string)


settings = Settings()


def ensure_dirs() -> None:
    """Create the local data / upload folders before anything touches them.
    Skips the upload folder entirely when Azure Blob is configured - nothing
    is ever written to local disk in that mode."""
    if not settings.using_azure_storage:
        os.makedirs(settings.upload_dir, exist_ok=True)
    if settings.database_url.startswith("sqlite:///"):
        db_path = settings.database_url.replace("sqlite:///", "", 1)
        parent = os.path.dirname(db_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
