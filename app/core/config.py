from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Recife Data Hub"
    app_version: str = "1.0.0"
    debug: bool = False
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    database_url: str = "sqlite:///./recife_geo.db"
    api_key: str = "recife-secret-2025"


@lru_cache
def get_settings() -> Settings:
    return Settings()
