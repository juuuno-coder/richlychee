"""Initialize default crawling presets."""

import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import get_app_settings
from app.services.crawl_preset_service import CrawlPresetService

async def init_presets():
    """Initialize default presets in database."""
    from app.models.crawl_preset import CrawlPreset

    settings = get_app_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # Check if presets already exist
        result = await session.execute(
            select(CrawlPreset)
        )
        existing = result.scalars().all()

        if existing:
            print(f"✓ {len(existing)}개의 프리셋이 이미 존재합니다.")
            for preset in existing:
                print(f"  - {preset.name}")
            return

        # Initialize default presets
        print("기본 프리셋 초기화 중...")
        await CrawlPresetService.initialize_default_presets(session)

        # Query again to get created presets
        result = await session.execute(select(CrawlPreset))
        presets = result.scalars().all()

        print(f"✓ {len(presets)}개의 기본 프리셋이 생성되었습니다:")
        for preset in presets:
            print(f"  - {preset.name} ({preset.site_url})")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_presets())
