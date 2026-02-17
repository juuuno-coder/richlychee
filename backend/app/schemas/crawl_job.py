"""크롤링 작업 스키마."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.crawl_job import CrawlJobStatus


class CrawlJobCreate(BaseModel):
    """크롤링 작업 생성 요청."""

    target_url: str = Field(..., description="크롤링 대상 URL")
    target_type: str = Field(default="static", description="크롤러 타입 (static/dynamic)")
    crawl_config: dict | None = Field(
        default=None,
        description="크롤링 설정 (셀렉터, 페이지네이션 등)",
        examples=[
            {
                "item_selector": ".product-item",
                "title_selector": ".title",
                "price_selector": ".price",
                "image_selector": "img",
            }
        ],
    )


class CrawlJobResponse(BaseModel):
    """크롤링 작업 응답."""

    id: uuid.UUID
    user_id: uuid.UUID
    status: CrawlJobStatus
    target_url: str
    target_type: str
    crawl_config: dict | None = None
    total_items: int
    crawled_items: int
    success_count: int
    failure_count: int
    celery_task_id: str | None = None
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None

    model_config = {"from_attributes": True}

    @property
    def progress_percent(self) -> float:
        """진행률 계산."""
        if self.total_items == 0:
            return 0.0
        return round(self.crawled_items / self.total_items * 100, 1)


class CrawlJobListResponse(BaseModel):
    """크롤링 작업 목록 응답."""

    items: list[CrawlJobResponse]
    total: int
    page: int = Field(default=1)
    size: int = Field(default=20)
