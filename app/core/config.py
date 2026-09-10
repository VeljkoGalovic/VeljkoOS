"""Application configuration, read from the environment."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings, sourced from environment variables or a local .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "VeljkoOS Core"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Must use the asyncpg driver prefix; the sync psycopg driver will not work
    # with the asyncio engine in app.core.database.
    DATABASE_URL: str = "postgresql+asyncpg://veljko:veljko@localhost:5432/veljkoos"


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings instance."""
    return Settings()


settings = get_settings()
