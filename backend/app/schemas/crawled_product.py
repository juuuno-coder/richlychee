"""크롤링된 상품 스키마."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CrawledProductResponse(BaseModel):
    """크롤링된 상품 응답."""

    id: uuid.UUID
    crawl_job_id: uuid.UUID
    user_id: uuid.UUID

    # 원본 데이터
    original_title: str
    original_price: int
    original_currency: str
    original_images: list[str]
    original_url: str
    original_data: dict | None = None

    # 가공된 데이터
    product_name: str | None = None
    sale_price: int | None = None
    exchange_rate: float | None = None
    category_id: str | None = None
    stock_quantity: int = 0
    detail_content: str | None = None
    representative_image: str | None = None
    optional_images: str | None = None

    # 가격 조정 정보
    price_adjustment_type: str | None = None
    price_adjustment_value: float | None = None

    # 재등록 상태
    is_registered: bool = False
    job_id: uuid.UUID | None = None
    naver_product_id: str | None = None

    # 타임스탬프
    crawled_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CrawledProductListResponse(BaseModel):
    """크롤링된 상품 목록 응답."""

    items: list[CrawledProductResponse]
    total: int
    page: int = Field(default=1)
    size: int = Field(default=50)


class CrawledProductUpdate(BaseModel):
    """크롤링된 상품 수정 요청."""

    product_name: str | None = None
    sale_price: int | None = None
    category_id: str | None = None
    stock_quantity: int | None = None
    detail_content: str | None = None
    representative_image: str | None = None
    optional_images: str | None = None


class PriceAdjustmentRequest(BaseModel):
    """가격 조정 요청."""

    product_ids: list[uuid.UUID] = Field(..., description="조정할 상품 ID 리스트")
    adjustment_type: str = Field(..., description="조정 타입 (percentage/fixed)")
    adjustment_value: float = Field(..., description="조정 값")


class RegisterCrawledRequest(BaseModel):
    """크롤링된 상품 재등록 요청."""

    product_ids: list[uuid.UUID] = Field(..., description="등록할 상품 ID 리스트")
    credential_id: uuid.UUID = Field(..., description="네이버 자격증명 ID")
    dry_run: bool = Field(default=False, description="실제 등록 없이 테스트")
