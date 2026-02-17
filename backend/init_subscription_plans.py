"""Initialize subscription plans."""

import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import get_app_settings
from app.services.subscription_service import SubscriptionService

async def init_plans():
    """Initialize subscription plans in database."""
    from app.models.subscription_plan import SubscriptionPlan

    settings = get_app_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # Check if plans already exist
        result = await session.execute(
            select(SubscriptionPlan)
        )
        existing = result.scalars().all()

        if existing:
            print(f"✓ {len(existing)}개의 플랜이 이미 존재합니다.")
            for plan in existing:
                print(f"  - {plan.display_name} ({plan.price_monthly:,}원/월)")
            return

        # Initialize default plans
        print("기본 구독 플랜 초기화 중...")
        plans = await SubscriptionService.initialize_default_plans(session)

        print(f"\n✓ {len(plans)}개의 기본 플랜이 생성되었습니다:")
        for plan in plans:
            print(f"\n  [{plan.display_name}]")
            print(f"    - 월 가격: {plan.price_monthly:,}원")
            print(f"    - 연 가격: {plan.price_yearly:,}원")
            print(f"    - 월 크롤링: {plan.limits.get('crawl_jobs_per_month', 0)}회")
            print(f"    - 월 등록: {plan.limits.get('product_registrations_per_month', 0)}개")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_plans())
