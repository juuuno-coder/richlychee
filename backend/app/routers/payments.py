"""포트원 결제 관련 API."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.payment import Payment
from app.models.user import User
from app.schemas.payment import (
    PaymentCancelRequest,
    PaymentCancelResponse,
    PaymentListResponse,
    PaymentPrepareRequest,
    PaymentPrepareResponse,
    PaymentResponse,
    PaymentVerifyRequest,
    PaymentVerifyResponse,
)
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])
settings = get_settings()


def get_payment_service() -> PaymentService:
    """포트원 결제 서비스 인스턴스 반환."""
    return PaymentService(
        api_key=settings.PORTONE_API_KEY,
        api_secret=settings.PORTONE_API_SECRET,
    )


@router.post("/prepare", response_model=PaymentPrepareResponse)
async def prepare_payment(
    body: PaymentPrepareRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    payment_service: Annotated[PaymentService, Depends(get_payment_service)],
):
    """
    결제 준비.

    - 구독 플랜 조회 및 금액 계산
    - Payment 레코드 생성
    - 클라이언트에서 사용할 결제 정보 반환
    """
    try:
        result = await payment_service.prepare_payment(
            db=db,
            user_id=str(user.id),
            plan_id=body.plan_id,
            billing_cycle=body.billing_cycle,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/verify", response_model=PaymentVerifyResponse)
async def verify_payment(
    body: PaymentVerifyRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    payment_service: Annotated[PaymentService, Depends(get_payment_service)],
):
    """
    결제 검증.

    - 포트원 API로 결제 상태 조회
    - 금액 및 상태 검증
    - 구독 활성화
    """
    try:
        result = await payment_service.verify_payment(
            db=db,
            payment_id=body.payment_id,
            portone_payment_id=body.portone_payment_id,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cancel", response_model=PaymentCancelResponse)
async def cancel_payment(
    body: PaymentCancelRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    payment_service: Annotated[PaymentService, Depends(get_payment_service)],
):
    """
    결제 취소/환불.

    - 포트원 API로 결제 취소 요청
    - Payment 상태 업데이트
    """
    try:
        result = await payment_service.cancel_payment(
            db=db,
            payment_id=body.payment_id,
            reason=body.reason,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history", response_model=PaymentListResponse)
async def get_payment_history(
    page: int = 1,
    size: int = 20,
    user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """
    결제 내역 조회.

    - 현재 사용자의 결제 내역 반환
    - 최신순 정렬
    """
    offset = (page - 1) * size

    # 총 개수 조회
    count_stmt = select(Payment).where(Payment.user_id == user.id)
    count_result = await db.execute(count_stmt)
    total = len(count_result.scalars().all())

    # 목록 조회
    stmt = (
        select(Payment)
        .where(Payment.user_id == user.id)
        .order_by(Payment.created_at.desc())
        .offset(offset)
        .limit(size)
    )
    result = await db.execute(stmt)
    payments = result.scalars().all()

    return PaymentListResponse(
        items=[PaymentResponse.model_validate(p) for p in payments],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment_detail(
    payment_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """결제 상세 조회."""
    stmt = select(Payment).where(
        Payment.id == payment_id,
        Payment.user_id == user.id,
    )
    result = await db.execute(stmt)
    payment = result.scalar_one_or_none()

    if not payment:
        raise HTTPException(status_code=404, detail="결제 내역을 찾을 수 없습니다.")

    return PaymentResponse.model_validate(payment)
