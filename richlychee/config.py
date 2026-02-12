"""설정 로딩 (.env + settings.yaml)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_CONFIG_DIR = _PROJECT_ROOT / "config"


def _load_yaml() -> dict[str, Any]:
    """settings.yaml 파일을 읽어 dict로 반환."""
    yaml_path = _CONFIG_DIR / "settings.yaml"
    if yaml_path.exists():
        with open(yaml_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


_yaml = _load_yaml()


class ApiSettings(BaseSettings):
    """네이버 커머스 API 접속 설정."""

    base_url: str = _yaml.get("api", {}).get(
        "base_url", "https://api.commerce.naver.com/external/v1"
    )
    token_url: str = _yaml.get("api", {}).get(
        "token_url", "https://api.commerce.naver.com/external/v1/oauth2/token"
    )
    timeout: int = _yaml.get("api", {}).get("timeout", 30)
    max_retries: int = _yaml.get("api", {}).get("max_retries", 3)
    retry_backoff_factor: float = _yaml.get("api", {}).get("retry_backoff_factor", 1.0)


class RateLimitSettings(BaseSettings):
    """레이트 리밋 설정."""

    requests_per_second: int = _yaml.get("rate_limit", {}).get("requests_per_second", 10)
    burst_max: int = _yaml.get("rate_limit", {}).get("burst_max", 15)


class RegistrationSettings(BaseSettings):
    """대량 등록 설정."""

    batch_size: int = _yaml.get("registration", {}).get("batch_size", 50)
    stop_on_error: bool = _yaml.get("registration", {}).get("stop_on_error", False)
    image_upload_timeout: int = _yaml.get("registration", {}).get("image_upload_timeout", 60)


class OutputSettings(BaseSettings):
    """출력 설정."""

    report_dir: str = _yaml.get("output", {}).get("report_dir", "output")
    report_format: str = _yaml.get("output", {}).get("report_format", "xlsx")


class Settings(BaseSettings):
    """애플리케이션 전체 설정. .env 파일에서 시크릿을 로드."""

    model_config = SettingsConfigDict(
        env_file=str(_PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 시크릿 (.env)
    naver_client_id: str = Field(default="", alias="NAVER_CLIENT_ID")
    naver_client_secret: str = Field(default="", alias="NAVER_CLIENT_SECRET")

    # 하위 설정
    api: ApiSettings = Field(default_factory=ApiSettings)
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)
    registration: RegistrationSettings = Field(default_factory=RegistrationSettings)
    output: OutputSettings = Field(default_factory=OutputSettings)


def get_settings() -> Settings:
    """싱글턴 설정 객체 반환."""
    return Settings()
