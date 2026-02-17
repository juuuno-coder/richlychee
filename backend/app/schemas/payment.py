"""포트원 결제 관련 스키마."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PaymentPrepareRequest(BaseModel):
    """결제 준비 요청."""

    plan_id: str = Field(..., description="구독 플랜 ID")
    billing_cycle: str = Field(..., description="결제 주기 (monthly/yearly)")


class PaymentPrepareResponse(BaseModel):
    """결제 준비 응답."""

    order_id: str
    payment_id: str
    amount: int
    currency: str
    plan_name: str
    billing_cycle: str
    customer_name: str
    customer_email: str


class PaymentVerifyRequest(BaseModel):
    """결제 검증 요청."""

    payment_id: str = Field(..., description="내부 결제 ID")
    portone_payment_id: str = Field(..., description="포트원 payment_id")


class PaymentVerifyResponse(BaseModel):
    """결제 검증 응답."""

    success: bool
    status: str
    message: str


class PaymentCancelRequest(BaseModel):
    """결제 취소 요청."""

    payment_id: str = Field(..., description="결제 ID")
    reason: str = Field(..., description="취소 사유")


class PaymentCancelResponse(BaseModel):
    """결제 취소 응답."""

    success: bool
    message: str


class PaymentResponse(BaseModel):
    """결제 내역 응답."""

    id: UUID
    user_id: UUID
    subscription_id: UUID
    payment_id: str
    order_id: str
    amount: int
    currency: str
    status: str
    payment_method: str | None
    plan_name: str
    billing_cycle: str
    refund_reason: str | None
    created_at: datetime
    refunded_at: datetime | None

    class Config:
        from_attributes = True


class PaymentListResponse(BaseModel):
    """결제 내역 목록 응답."""

    items: list[PaymentResponse]
    total: int
    page: int
    size: int
