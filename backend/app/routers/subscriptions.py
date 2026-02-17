"""구독 요금제 라우터."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.subscription_plan import SubscriptionPlan
from app.models.user import User
from app.schemas.subscription import (
    SubscriptionPlanResponse,
    UpgradeRequest,
    UsageStatsResponse,
    UserSubscriptionResponse,
)
from app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("/plans", response_model=list[SubscriptionPlanResponse])
async def list_plans(db: AsyncSession = Depends(get_db)):
    """사용 가능한 구독 플랜 목록 조회."""
    result = await db.execute(
        select(SubscriptionPlan)
        .where(SubscriptionPlan.is_active == True)  # noqa: E712
        .order_by(SubscriptionPlan.price_monthly)
    )
    plans = result.scalars().all()

    return [
        SubscriptionPlanResponse(
            id=str(p.id),
            name=p.name,
            display_name=p.display_name,
            description=p.description,
            price_monthly=p.price_monthly,
            price_yearly=p.price_yearly,
            limits=p.limits,
            is_active=p.is_active,
            is_popular=p.is_popular,
        )
        for p in plans
    ]


@router.get("/my", response_model=UserSubscriptionResponse)
async def get_my_subscription(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """내 구독 정보 조회."""
    subscription = await SubscriptionService.get_or_create_free_subscription(
        db, str(user.id)
    )

    # 플랜 로드
    result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.id == subscription.plan_id)
    )
    plan = result.scalar_one()

    return UserSubscriptionResponse(
        id=str(subscription.id),
        user_id=str(subscription.user_id),
        plan=SubscriptionPlanResponse(
            id=str(plan.id),
            name=plan.name,
            display_name=plan.display_name,
            description=plan.description,
            price_monthly=plan.price_monthly,
            price_yearly=plan.price_yearly,
            limits=plan.limits,
            is_active=plan.is_active,
            is_popular=plan.is_popular,
        ),
        status=subscription.status,
        billing_cycle=subscription.billing_cycle,
        starts_at=subscription.starts_at,
        ends_at=subscription.ends_at,
        auto_renew=subscription.auto_renew,
        usage=subscription.usage,
        usage_reset_at=subscription.usage_reset_at,
    )


@router.get("/usage", response_model=UsageStatsResponse)
async def get_usage_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """사용량 통계 조회."""
    stats = await SubscriptionService.get_usage_stats(db, str(user.id))
    return UsageStatsResponse(**stats)


@router.post("/upgrade")
async def upgrade_plan(
    body: UpgradeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    플랜 업그레이드.

    실제 결제 시스템 연동은 나중에 구현.
    지금은 플랜만 변경.
    """
    from datetime import UTC, datetime, timedelta
    from uuid import UUID

    # 타겟 플랜 확인
    result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.id == UUID(body.plan_id))
    )
    target_plan = result.scalar_one_or_none()

    if not target_plan:
        raise HTTPException(status_code=404, detail="플랜을 찾을 수 없습니다.")

    if not target_plan.is_active:
        raise HTTPException(status_code=400, detail="비활성화된 플랜입니다.")

    # 현재 구독 조회
    subscription = await SubscriptionService.get_or_create_free_subscription(
        db, str(user.id)
    )

    # 구독 업데이트
    now = datetime.now(UTC)
    subscription.plan_id = target_plan.id
    subscription.billing_cycle = body.billing_cycle
    subscription.starts_at = now
    subscription.status = "active"

    # 종료 날짜 설정
    if body.billing_cycle == "monthly":
        subscription.ends_at = now + timedelta(days=30)
    else:  # yearly
        subscription.ends_at = now + timedelta(days=365)

    # 사용량 리셋
    subscription.usage = {}
    subscription.usage_reset_at = now

    await db.commit()
    await db.refresh(subscription)

    return {
        "message": "플랜이 업그레이드되었습니다.",
        "plan": target_plan.display_name,
        "billing_cycle": body.billing_cycle,
        "ends_at": subscription.ends_at.isoformat(),
    }


@router.post("/cancel")
async def cancel_subscription(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    구독 취소.

    즉시 취소되지 않고 현재 주기 종료 시 취소.
    """
    from datetime import UTC, datetime

    subscription = await SubscriptionService.get_or_create_free_subscription(
        db, str(user.id)
    )

    subscription.auto_renew = False
    subscription.cancelled_at = datetime.now(UTC)
    subscription.status = "cancelled"

    await db.commit()

    return {
        "message": "구독이 취소되었습니다. 현재 주기 종료 시까지 사용 가능합니다.",
        "ends_at": subscription.ends_at.isoformat(),
    }
