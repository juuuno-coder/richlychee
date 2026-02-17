"""구독 요금제 서비스."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription_plan import SubscriptionPlan
from app.models.user import User
from app.models.user_subscription import UserSubscription


class SubscriptionService:
    """구독 요금제 관리 서비스."""

    # 기본 플랜 정의
    DEFAULT_PLANS = [
        {
            "name": "free",
            "display_name": "Free",
            "description": "개인 사용자를 위한 무료 플랜",
            "price_monthly": 0,
            "price_yearly": 0,
            "limits": {
                "crawl_jobs_per_month": 10,  # 월 크롤링 작업 수
                "products_per_crawl": 50,  # 크롤링당 상품 수
                "product_registrations_per_month": 100,  # 월 상품 등록 수
                "concurrent_crawls": 1,  # 동시 크롤링 작업
                "schedules": 1,  # 스케줄 수
                "price_alerts": 5,  # 가격 알림 수
                "stored_products": 500,  # 저장 가능한 상품 수
            },
        },
        {
            "name": "basic",
            "display_name": "Basic",
            "description": "소규모 셀러를 위한 기본 플랜",
            "price_monthly": 29000,
            "price_yearly": 290000,  # 2개월 할인
            "limits": {
                "crawl_jobs_per_month": 100,
                "products_per_crawl": 200,
                "product_registrations_per_month": 1000,
                "concurrent_crawls": 3,
                "schedules": 5,
                "price_alerts": 20,
                "stored_products": 5000,
            },
        },
        {
            "name": "pro",
            "display_name": "Pro",
            "description": "중규모 셀러를 위한 프로 플랜",
            "price_monthly": 79000,
            "price_yearly": 790000,  # 2개월 할인
            "limits": {
                "crawl_jobs_per_month": 500,
                "products_per_crawl": 1000,
                "product_registrations_per_month": 5000,
                "concurrent_crawls": 10,
                "schedules": 20,
                "price_alerts": 100,
                "stored_products": 50000,
            },
        },
        {
            "name": "enterprise",
            "display_name": "Enterprise",
            "description": "대규모 셀러를 위한 엔터프라이즈 플랜",
            "price_monthly": 199000,
            "price_yearly": 1990000,  # 2개월 할인
            "limits": {
                "crawl_jobs_per_month": -1,  # 무제한
                "products_per_crawl": -1,  # 무제한
                "product_registrations_per_month": -1,  # 무제한
                "concurrent_crawls": 50,
                "schedules": -1,  # 무제한
                "price_alerts": -1,  # 무제한
                "stored_products": -1,  # 무제한
            },
        },
    ]

    @staticmethod
    async def initialize_default_plans(db: AsyncSession) -> list[SubscriptionPlan]:
        """기본 플랜 초기화 (DB에 저장)."""
        plans = []
        for plan_data in SubscriptionService.DEFAULT_PLANS:
            # 이미 존재하는지 확인
            result = await db.execute(
                select(SubscriptionPlan).where(SubscriptionPlan.name == plan_data["name"])
            )
            existing = result.scalar_one_or_none()

            if not existing:
                plan = SubscriptionPlan(
                    name=plan_data["name"],
                    display_name=plan_data["display_name"],
                    description=plan_data["description"],
                    price_monthly=plan_data["price_monthly"],
                    price_yearly=plan_data["price_yearly"],
                    limits=plan_data["limits"],
                    is_active=True,
                    is_popular=(plan_data["name"] == "pro"),  # Pro가 인기 플랜
                )
                db.add(plan)
                plans.append(plan)
            else:
                plans.append(existing)

        await db.commit()
        return plans

    @staticmethod
    async def get_or_create_free_subscription(
        db: AsyncSession, user_id: str
    ) -> UserSubscription:
        """
        사용자의 구독 정보 조회, 없으면 Free 플랜으로 생성.

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID

        Returns:
            사용자 구독 정보
        """
        from uuid import UUID

        # 기존 구독 조회
        result = await db.execute(
            select(UserSubscription).where(UserSubscription.user_id == UUID(user_id))
        )
        subscription = result.scalar_one_or_none()

        if subscription:
            return subscription

        # Free 플랜 조회
        result = await db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.name == "free")
        )
        free_plan = result.scalar_one_or_none()

        if not free_plan:
            raise ValueError("Free 플랜이 초기화되지 않았습니다.")

        # Free 구독 생성
        now = datetime.now(UTC)
        subscription = UserSubscription(
            user_id=UUID(user_id),
            plan_id=free_plan.id,
            status="active",
            billing_cycle="monthly",
            starts_at=now,
            ends_at=now + timedelta(days=365 * 100),  # 무제한
            usage={},
            usage_reset_at=now,
            auto_renew=True,
        )
        db.add(subscription)
        await db.commit()
        await db.refresh(subscription)
        return subscription

    @staticmethod
    async def check_limit(
        db: AsyncSession, user_id: str, feature: str, increment: int = 1
    ) -> tuple[bool, dict[str, Any]]:
        """
        기능 사용 제한 확인 및 사용량 증가.

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            feature: 기능 키 (예: 'crawl_jobs_per_month')
            increment: 증가량 (기본값 1)

        Returns:
            (허용 여부, 제한 정보)
        """
        subscription = await SubscriptionService.get_or_create_free_subscription(
            db, user_id
        )

        # 플랜 로드
        result = await db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.id == subscription.plan_id)
        )
        plan = result.scalar_one()

        # 사용량 리셋 확인 (월별 리셋)
        now = datetime.now(UTC)
        if now > subscription.usage_reset_at + timedelta(days=30):
            subscription.usage = {}
            subscription.usage_reset_at = now
            await db.commit()

        # 제한 확인
        limit = plan.limits.get(feature, 0)
        current_usage = subscription.usage.get(feature, 0)

        if limit == -1:  # 무제한
            allowed = True
        elif current_usage + increment > limit:
            allowed = False
        else:
            allowed = True

        # 사용량 증가 (허용된 경우)
        if allowed:
            subscription.usage[feature] = current_usage + increment
            await db.commit()

            # 사용량 경고 이메일 (80% 도달 시)
            if limit != -1:  # 무제한이 아닌 경우
                usage_percent = ((current_usage + increment) / limit) * 100
                if 80 <= usage_percent < 100 and current_usage / limit * 100 < 80:
                    # 80% 처음 도달 시
                    try:
                        from app.services.email_service import EmailService
                        from app.core.config import get_app_settings

                        settings = get_app_settings()
                        email_service = EmailService(
                            smtp_host=settings.SMTP_HOST,
                            smtp_port=settings.SMTP_PORT,
                            smtp_user=settings.SMTP_USER,
                            smtp_password=settings.SMTP_PASSWORD,
                            from_email=settings.FROM_EMAIL,
                        )

                        # 사용자 조회
                        user_result = await db.execute(
                            select(User).where(User.id == subscription.user_id)
                        )
                        user = user_result.scalar_one()

                        # 경고 이메일 발송
                        email_service.send_usage_warning(
                            to_email=settings.NOTIFICATION_EMAIL,
                            user_name=user.name,
                            feature_name=feature,
                            usage_percent=int(usage_percent),
                            current_usage=current_usage + increment,
                            limit=limit,
                        )
                    except Exception as e:
                        print(f"사용량 경고 이메일 발송 실패: {e}")
        else:
            # 한도 도달 이메일
            try:
                from app.services.email_service import EmailService
                from app.core.config import get_app_settings

                settings = get_app_settings()
                email_service = EmailService(
                    smtp_host=settings.SMTP_HOST,
                    smtp_port=settings.SMTP_PORT,
                    smtp_user=settings.SMTP_USER,
                    smtp_password=settings.SMTP_PASSWORD,
                    from_email=settings.FROM_EMAIL,
                )

                # 사용자 조회
                user_result = await db.execute(
                    select(User).where(User.id == subscription.user_id)
                )
                user = user_result.scalar_one()

                # 한도 도달 이메일 발송
                email_service.send_usage_limit_reached(
                    to_email=settings.NOTIFICATION_EMAIL,
                    user_name=user.name,
                    feature_name=feature,
                    limit=limit,
                )
            except Exception as e:
                print(f"한도 도달 이메일 발송 실패: {e}")

        return allowed, {
            "limit": limit,
            "current": current_usage,
            "after": current_usage + increment if allowed else current_usage,
            "remaining": limit - (current_usage + increment) if limit != -1 else -1,
        }

    @staticmethod
    async def get_usage_stats(db: AsyncSession, user_id: str) -> dict:
        """
        사용자의 사용량 통계 조회.

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID

        Returns:
            사용량 통계
        """
        subscription = await SubscriptionService.get_or_create_free_subscription(
            db, user_id
        )

        # 플랜 로드
        result = await db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.id == subscription.plan_id)
        )
        plan = result.scalar_one()

        stats = {
            "plan": {
                "name": plan.name,
                "display_name": plan.display_name,
                "is_popular": plan.is_popular,
            },
            "limits": plan.limits,
            "usage": subscription.usage,
            "usage_reset_at": subscription.usage_reset_at.isoformat(),
            "features": {},
        }

        # 기능별 사용률 계산
        for feature, limit in plan.limits.items():
            current = subscription.usage.get(feature, 0)
            if limit == -1:
                usage_percent = 0  # 무제한
            else:
                usage_percent = (current / limit * 100) if limit > 0 else 0

            stats["features"][feature] = {
                "limit": limit,
                "current": current,
                "remaining": limit - current if limit != -1 else -1,
                "usage_percent": round(usage_percent, 2),
            }

        return stats
