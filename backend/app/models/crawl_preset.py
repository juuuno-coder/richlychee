"""크롤링 프리셋 모델."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CrawlPreset(Base):
    """크롤링 프리셋 (주요 쇼핑몰별 설정)."""

    __tablename__ = "crawl_presets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100))  # "Amazon US", "쿠팡", "11번가"
    site_url: Mapped[str] = mapped_column(String(500))  # 사이트 기본 URL
    url_pattern: Mapped[str] = mapped_column(String(500))  # URL 패턴 (정규식)

    # 크롤러 설정
    crawler_type: Mapped[str] = mapped_column(String(20), default="static")  # static/dynamic
    crawl_config: Mapped[dict] = mapped_column(JSON)  # 셀렉터 등

    # 메타데이터
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)  # 모든 사용자 공유 여부

    # 사용 통계
    usage_count: Mapped[int] = mapped_column(default=0)
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )
