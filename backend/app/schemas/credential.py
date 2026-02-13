"""네이버 API 자격증명 스키마."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CredentialCreate(BaseModel):
    label: str = Field(default="기본", max_length=100)
    naver_client_id: str = Field(min_length=1, max_length=255)
    naver_client_secret: str = Field(min_length=1, max_length=255)


class CredentialUpdate(BaseModel):
    label: str | None = Field(None, max_length=100)
    naver_client_id: str | None = Field(None, max_length=255)
    naver_client_secret: str | None = Field(None, max_length=255)


class CredentialResponse(BaseModel):
    id: uuid.UUID
    label: str
    naver_client_id: str
    is_verified: bool
    last_verified_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CredentialVerifyResponse(BaseModel):
    success: bool
    message: str
