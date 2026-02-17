"""사용자 구독 정보 모델."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserSubscription(Base):
    """사용자 구독 정보."""

    __tablename__ = "user_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subscription_plans.id", ondelete="RESTRICT")
    )

    # 구독 상태
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, cancelled, expired
    billing_cycle: Mapped[str] = mapped_column(String(20), default="monthly")  # monthly, yearly

    # 구독 기간
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # 자동 갱신
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True)

    # 사용량 추적 (현재 주기)
    usage: Mapped[dict] = mapped_column(JSON, default=dict)  # 기능별 사용량
    usage_reset_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    # 결제 정보 (나중에 확장 가능)
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_payment_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # 타임스탬프
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    user = relationship("User", back_populates="subscription")
    plan = relationship("SubscriptionPlan")
    payments = relationship("Payment", back_populates="subscription", cascade="all, delete")
