from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


def _read_bool(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False

    raise ValueError(f"{name} must be a boolean value")


class Settings(BaseModel):
    app_name: str = Field(default="Local Athena API")
    app_version: str = Field(default="0.1.0")
    athena_base_url: str = Field(default="https://athena.ohdsi.org")
    athena_timeout_seconds: int = Field(default=30, ge=1)
    cache_ttl_days: int = Field(default=7, ge=1)
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/athena_cache.sqlite3"
    )
    playwright_headless: bool = Field(default=True)
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="./logs/athena_api.log")
    project_root: Path = Field(default=PROJECT_ROOT)

    @field_validator("athena_base_url")
    @classmethod
    def normalize_athena_base_url(cls, value: str) -> str:
        value = value.strip().rstrip("/")
        if not value.startswith(("http://", "https://")):
            raise ValueError("ATHENA_BASE_URL must start with http:// or https://")
        return value

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("DATABASE_URL cannot be empty")
        if not value.startswith("sqlite+aiosqlite:///"):
            raise ValueError("DATABASE_URL must use sqlite+aiosqlite for this stage")
        return value

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        value = value.strip().upper()
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if value not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of: {', '.join(sorted(allowed))}")
        return value

    @property
    def data_dir(self) -> Path:
        return self.project_root / "data"

    @property
    def log_path(self) -> Path:
        path = Path(self.log_file)
        if not path.is_absolute():
            path = self.project_root / path
        return path


@lru_cache
def get_settings() -> Settings:
    load_dotenv(ENV_FILE)

    return Settings(
        athena_base_url=os.getenv("ATHENA_BASE_URL", "https://athena.ohdsi.org"),
        athena_timeout_seconds=int(os.getenv("ATHENA_TIMEOUT_SECONDS", "30")),
        cache_ttl_days=int(os.getenv("CACHE_TTL_DAYS", "7")),
        database_url=os.getenv(
            "DATABASE_URL", "sqlite+aiosqlite:///./data/athena_cache.sqlite3"
        ),
        playwright_headless=_read_bool("PLAYWRIGHT_HEADLESS", True),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_file=os.getenv("LOG_FILE", "./logs/athena_api.log"),
    )
