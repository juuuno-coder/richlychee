"""구독 요금제 모델."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SubscriptionPlan(Base):
    """구독 요금제 플랜."""

    __tablename__ = "subscription_plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(50))  # Free, Basic, Pro, Enterprise
    display_name: Mapped[str] = mapped_column(String(100))  # 표시명
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 가격 정보
    price_monthly: Mapped[int] = mapped_column(Integer, default=0)  # 월 가격 (원)
    price_yearly: Mapped[int] = mapped_column(Integer, default=0)  # 연 가격 (원)

    # 기능 제한 (limits)
    limits: Mapped[dict] = mapped_column(JSON)  # 기능별 제한

    # 상태
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_popular: Mapped[bool] = mapped_column(Boolean, default=False)  # 인기 플랜 표시

    # 타임스탬프
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
