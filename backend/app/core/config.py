"""FastAPI 애플리케이션 설정."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """FastAPI 전용 설정. .env에서 로드."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql+asyncpg://richlychee:richlychee@localhost:5432/richlychee"

    # JWT
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # AES-256 encryption for Naver API secrets
    encryption_key: str = "change-me-32-byte-key-for-aes256"

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # File upload
    upload_dir: str = "uploads"
    max_upload_size_mb: int = 50

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # App
    debug: bool = False


_settings: AppSettings | None = None


def get_app_settings() -> AppSettings:
    """싱글턴 설정 반환."""
    global _settings
    if _settings is None:
        _settings = AppSettings()
    return _settings
