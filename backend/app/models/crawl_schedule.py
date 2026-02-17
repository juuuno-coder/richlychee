"""크롤링 스케줄 모델."""

from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ScheduleFrequency(str, enum.Enum):
    """스케줄 주기."""

    HOURLY = "HOURLY"  # 매시간
    DAILY = "DAILY"  # 매일
    WEEKLY = "WEEKLY"  # 매주
    MONTHLY = "MONTHLY"  # 매월


class CrawlSchedule(Base):
    """크롤링 스케줄."""

    __tablename__ = "crawl_schedules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )

    # 스케줄 설정
    name: Mapped[str] = mapped_column(String(200))  # "Amazon 신상품 모니터링"
    target_url: Mapped[str] = mapped_column(String(1000))
    target_type: Mapped[str] = mapped_column(String(20), default="static")
    crawl_config: Mapped[dict] = mapped_column(JSON)

    # 주기 설정
    frequency: Mapped[str] = mapped_column(
        String(20), default="DAILY"  # HOURLY, DAILY, WEEKLY, MONTHLY
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # 실행 통계
    total_runs: Mapped[int] = mapped_column(Integer, default=0)
    last_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # 타임스탬프
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    # Relationships
    user = relationship("User", back_populates="crawl_schedules")
