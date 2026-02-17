"""원클릭 크롤링 라우터."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.crawl_job import CrawlJob, CrawlJobStatus
from app.models.user import User
from app.schemas.crawl_job import CrawlJobResponse
from app.services.crawl_preset_service import CrawlPresetService

router = APIRouter(prefix="/quick-crawl", tags=["quick-crawl"])


class QuickCrawlRequest(BaseModel):
    """원클릭 크롤링 요청."""

    url: str
    auto_start: bool = True  # 자동 시작 여부


class QuickCrawlResponse(BaseModel):
    """원클릭 크롤링 응답."""

    job: CrawlJobResponse
    detected_site: str | None = None
    used_preset: str | None = None


@router.post("", response_model=QuickCrawlResponse)
async def quick_crawl(
    body: QuickCrawlRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    URL만 입력하면 자동으로 크롤링 시작.

    1. URL로 프리셋 자동 감지
    2. 크롤링 작업 생성
    3. (옵션) 자동 시작
    """
    # URL 형식 검증
    if not body.url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="유효한 URL을 입력해주세요.")

    # 프리셋 자동 감지
    detected_config = await CrawlPresetService.auto_detect_config(body.url)

    if not detected_config:
        # 감지 실패 시 기본 정적 크롤러 사용
        detected_config = {
            "crawler_type": "static",
            "crawl_config": {
                "item_selector": ".product, .item, [class*='product']",
                "title_selector": "h1, h2, h3, .title, [class*='title']",
                "price_selector": ".price, [class*='price']",
                "image_selector": "img",
                "link_selector": "a",
            },
            "preset_name": "일반 (자동 감지)",
        }

    # 크롤링 작업 생성
    job = CrawlJob(
        user_id=user.id,
        target_url=body.url,
        target_type=detected_config["crawler_type"],
        crawl_config=detected_config["crawl_config"],
        status=CrawlJobStatus.PENDING,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # 자동 시작
    if body.auto_start:
        from app.tasks.crawling import run_crawl_job

        task = run_crawl_job.delay(str(job.id))
        job.celery_task_id = task.id
        job.status = CrawlJobStatus.RUNNING
        await db.commit()
        await db.refresh(job)

    # DB 프리셋 업데이트 (사용 통계)
    preset = await CrawlPresetService.find_preset_by_url(db, body.url)
    if preset:
        from datetime import UTC, datetime
        preset.usage_count += 1
        preset.last_used_at = datetime.now(UTC)
        await db.commit()

    return QuickCrawlResponse(
        job=job,
        detected_site=detected_config.get("preset_name"),
        used_preset=detected_config.get("preset_name"),
    )


@router.get("/presets")
async def list_presets(
    db: AsyncSession = Depends(get_db),
):
    """사용 가능한 크롤링 프리셋 목록."""
    from app.models.crawl_preset import CrawlPreset
    from sqlalchemy import select

    result = await db.execute(
        select(CrawlPreset).where(CrawlPreset.is_active == True)  # noqa: E712
        .order_by(CrawlPreset.usage_count.desc())
    )
    presets = result.scalars().all()

    return {
        "presets": [
            {
                "id": str(p.id),
                "name": p.name,
                "site_url": p.site_url,
                "description": p.description,
                "crawler_type": p.crawler_type,
                "usage_count": p.usage_count,
            }
            for p in presets
        ]
    }


@router.post("/detect")
async def detect_crawler_config(url: str):
    """URL로 크롤러 설정 자동 감지 (테스트용)."""
    config = await CrawlPresetService.auto_detect_config(url)

    if not config:
        raise HTTPException(
            status_code=404,
            detail="자동 감지 실패. 수동으로 설정을 입력해주세요.",
        )

    return config
