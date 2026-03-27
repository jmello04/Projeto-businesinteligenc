"""Application settings loaded from environment variables via pydantic-settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralised configuration for Recife Data Hub.

    All sensitive fields (``api_key``) have no hardcoded defaults and must be
    provided via environment variable or ``.env`` file.  The application will
    raise a validation error on startup if they are absent.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────────────────────
    app_name: str = "Recife Data Hub"
    app_version: str = "1.0.0"
    debug: bool = False
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # ── Persistence ───────────────────────────────────────────────────────────
    database_url: str = "sqlite:///./recife_geo.db"

    # ── Security ──────────────────────────────────────────────────────────────
    api_key: str = Field(..., description="Bearer token required by X-Sistema-Token header")


@lru_cache
def get_settings() -> Settings:
    """Return the singleton Settings instance, loaded once and cached.

    Returns:
        Application-wide settings object.
    """
    return Settings()
