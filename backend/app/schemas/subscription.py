"""구독 요금제 스키마."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SubscriptionPlanResponse(BaseModel):
    """구독 플랜 응답."""

    id: str
    name: str
    display_name: str
    description: str | None
    price_monthly: int
    price_yearly: int
    limits: dict
    is_active: bool
    is_popular: bool


class UserSubscriptionResponse(BaseModel):
    """사용자 구독 응답."""

    id: str
    user_id: str
    plan: SubscriptionPlanResponse
    status: str
    billing_cycle: str
    starts_at: datetime
    ends_at: datetime
    auto_renew: bool
    usage: dict
    usage_reset_at: datetime


class UsageStatsResponse(BaseModel):
    """사용량 통계 응답."""

    plan: dict
    limits: dict
    usage: dict
    usage_reset_at: str
    features: dict


class UpgradeRequest(BaseModel):
    """플랜 업그레이드 요청."""

    plan_id: str
    billing_cycle: str = "monthly"  # monthly, yearly


class FeatureLimitCheck(BaseModel):
    """기능 제한 체크 응답."""

    allowed: bool
    limit: int
    current: int
    after: int
    remaining: int
    message: str | None = None
