"""크롤링 작업 모델."""

from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CrawlJobStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class CrawlJob(Base):
    __tablename__ = "crawl_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    status: Mapped[CrawlJobStatus] = mapped_column(
        Enum(CrawlJobStatus), default=CrawlJobStatus.PENDING
    )
    target_url: Mapped[str] = mapped_column(String(1000))
    target_type: Mapped[str] = mapped_column(String(20), default="static")  # 'static' | 'dynamic'
    crawl_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # 진행 상황
    total_items: Mapped[int] = mapped_column(Integer, default=0)
    crawled_items: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)

    # Celery
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 타임스탬프
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user = relationship("User", back_populates="crawl_jobs")
    products = relationship("CrawledProduct", back_populates="crawl_job", cascade="all, delete")
