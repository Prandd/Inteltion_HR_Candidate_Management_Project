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

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()


def ensure_dirs() -> None:
    """Create the local data / upload folders before anything touches them."""
    os.makedirs(settings.upload_dir, exist_ok=True)
    if settings.database_url.startswith("sqlite:///"):
        db_path = settings.database_url.replace("sqlite:///", "", 1)
        parent = os.path.dirname(db_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
