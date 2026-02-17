"""가격 변동 이력 모델."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PriceHistory(Base):
    """상품 가격 변동 이력."""

    __tablename__ = "price_histories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    crawled_product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crawled_products.id", ondelete="CASCADE")
    )

    # 가격 정보
    price: Mapped[int] = mapped_column(Integer)  # KRW
    currency: Mapped[str] = mapped_column(String(10), default="KRW")
    original_price: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 원본 통화 가격

    # 변동 정보
    price_change: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 이전 대비 변동
    price_change_percent: Mapped[float | None] = mapped_column(Float, nullable=True)  # 변동률 (%)

    # 체크 시간
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    # Relationships
    crawled_product = relationship("CrawledProduct", back_populates="price_histories")


class PriceAlert(Base):
    """가격 알림 설정."""

    __tablename__ = "price_alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    crawled_product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crawled_products.id", ondelete="CASCADE")
    )

    # 알림 조건
    alert_type: Mapped[str] = mapped_column(String(20))  # 'below', 'above', 'change'
    target_price: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 목표 가격
    change_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)  # 변동률 임계값 (%)

    # 알림 상태
    is_active: Mapped[bool] = mapped_column(default=True)
    triggered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    # Relationships
    user = relationship("User", back_populates="price_alerts")
    crawled_product = relationship("CrawledProduct")
