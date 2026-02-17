"""크롤링된 상품 모델."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CrawledProduct(Base):
    __tablename__ = "crawled_products"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    crawl_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crawl_jobs.id", ondelete="CASCADE")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )

    # 원본 데이터 (크롤링된 그대로)
    original_title: Mapped[str] = mapped_column(Text)
    original_price: Mapped[int] = mapped_column(Integer)
    original_currency: Mapped[str] = mapped_column(String(10), default="KRW")
    original_images: Mapped[list | None] = mapped_column(JSON, nullable=True)  # JSON array
    original_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_url: Mapped[str] = mapped_column(String(1000))
    original_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # 추가 메타데이터

    # 가공된 데이터 (재등록용)
    product_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sale_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    exchange_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    category_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0)
    detail_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    representative_image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    optional_images: Mapped[str | None] = mapped_column(Text, nullable=True)  # 쉼표 구분

    # 가격 조정 정보
    price_adjustment_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    price_adjustment_value: Mapped[float | None] = mapped_column(Float, nullable=True)

    # 재등록 상태
    is_registered: Mapped[bool] = mapped_column(Boolean, default=False)
    job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True
    )
    naver_product_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # 타임스탬프
    crawled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    crawl_job = relationship("CrawlJob", back_populates="products")
    user = relationship("User", back_populates="crawled_products")
    registration_job = relationship("Job", foreign_keys=[job_id])
    price_histories = relationship("PriceHistory", back_populates="crawled_product", cascade="all, delete")
