"""구독 요금제 관련 의존성."""

from __future__ import annotations

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.subscription_service import SubscriptionService


async def check_feature_limit(
    feature: str,
    increment: int = 1,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    기능 사용 제한 확인 의존성.

    사용법:
        @router.post("/crawl-jobs")
        async def create_crawl_job(
            ...,
            _: None = Depends(check_feature_limit("crawl_jobs_per_month"))
        ):
    """
    allowed, info = await SubscriptionService.check_limit(
        db, str(user.id), feature, increment
    )

    if not allowed:
        raise HTTPException(
            status_code=402,  # Payment Required
            detail={
                "error": "구독 플랜 제한에 도달했습니다.",
                "feature": feature,
                "limit": info["limit"],
                "current": info["current"],
                "message": f"현재 플랜에서는 월 {info['limit']}회까지 사용 가능합니다. 플랜을 업그레이드해주세요.",
            },
        )

    return None


def require_feature(feature: str, increment: int = 1):
    """
    기능 제한 확인 팩토리 함수.

    사용법:
        @router.post("/crawl-jobs")
        async def create_crawl_job(
            ...,
            _: None = Depends(require_feature("crawl_jobs_per_month"))
        ):
    """

    async def _check(
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        return await check_feature_limit(feature, increment, user, db)

    return _check
