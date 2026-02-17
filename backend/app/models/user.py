"""사용자 모델."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    name: Mapped[str] = mapped_column(String(100), default="")
    provider: Mapped[str] = mapped_column(String(20), default="email")  # email/naver/kakao
    provider_account_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    credentials = relationship("NaverCredential", back_populates="user", cascade="all, delete")
    jobs = relationship("Job", back_populates="user", cascade="all, delete")
    crawl_jobs = relationship("CrawlJob", back_populates="user", cascade="all, delete")
    crawled_products = relationship("CrawledProduct", back_populates="user", cascade="all, delete")
    crawl_schedules = relationship("CrawlSchedule", back_populates="user", cascade="all, delete")
    price_alerts = relationship("PriceAlert", back_populates="user", cascade="all, delete")
    subscription = relationship("UserSubscription", back_populates="user", uselist=False, cascade="all, delete")
    payments = relationship("Payment", back_populates="user", cascade="all, delete")
