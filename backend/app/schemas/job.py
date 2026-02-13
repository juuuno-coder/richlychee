"""작업 스키마."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.job import JobStatus


class JobCreate(BaseModel):
    credential_id: uuid.UUID
    dry_run: bool = False


class JobResponse(BaseModel):
    id: uuid.UUID
    status: JobStatus
    original_filename: str
    dry_run: bool
    total_rows: int
    processed_rows: int
    success_count: int
    failure_count: int
    validation_errors: dict | None = None
    validation_warnings: dict | None = None
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None

    model_config = {"from_attributes": True}

    @property
    def progress_percent(self) -> float:
        if self.total_rows == 0:
            return 0.0
        return round(self.processed_rows / self.total_rows * 100, 1)


class JobListResponse(BaseModel):
    items: list[JobResponse]
    total: int
    page: int
    size: int


class ProductResultResponse(BaseModel):
    id: uuid.UUID
    row_index: int
    product_name: str
    success: bool
    naver_product_id: str | None = None
    error_message: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductResultListResponse(BaseModel):
    items: list[ProductResultResponse]
    total: int
    page: int = Field(default=1)
    size: int = Field(default=50)
