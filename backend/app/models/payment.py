"""결제 내역 모델."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Payment(Base):
    """결제 내역."""

    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_subscriptions.id", ondelete="CASCADE")
    )

    # 포트원 결제 정보
    payment_id: Mapped[str] = mapped_column(String(100), unique=True)  # 포트원 payment_id
    order_id: Mapped[str] = mapped_column(String(100), unique=True)  # 주문 ID (merchant_uid)

    # 결제 금액
    amount: Mapped[int] = mapped_column(Integer)  # 결제 금액
    currency: Mapped[str] = mapped_column(String(10), default="KRW")

    # 결제 상태
    status: Mapped[str] = mapped_column(String(20))  # pending, paid, failed, cancelled, refunded
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)  # card, transfer, etc.

    # 결제 상세
    plan_name: Mapped[str] = mapped_column(String(50))  # 플랜명 (기록용)
    billing_cycle: Mapped[str] = mapped_column(String(20))  # monthly, yearly

    # 포트원 응답 데이터
    portone_response: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # 환불 정보
    refund_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    refunded_at: Mapped[datetime | None] = mapped_column(
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
    user = relationship("User", back_populates="payments")
    subscription = relationship("UserSubscription", back_populates="payments")
