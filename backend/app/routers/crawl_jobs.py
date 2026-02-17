"""크롤링 작업 라우터."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.dependencies.subscription import require_feature
from app.models.crawl_job import CrawlJob, CrawlJobStatus
from app.models.crawled_product import CrawledProduct
from app.models.user import User
from app.schemas.crawl_job import (
    CrawlJobCreate,
    CrawlJobListResponse,
    CrawlJobResponse,
)
from app.schemas.crawled_product import (
    CrawledProductListResponse,
    CrawledProductResponse,
)

router = APIRouter(prefix="/crawl-jobs", tags=["crawl-jobs"])


@router.get("", response_model=CrawlJobListResponse)
async def list_crawl_jobs(
    status_filter: CrawlJobStatus | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """크롤링 작업 목록."""
    query = select(CrawlJob).where(CrawlJob.user_id == user.id)
    count_query = select(func.count(CrawlJob.id)).where(CrawlJob.user_id == user.id)

    if status_filter:
        query = query.where(CrawlJob.status == status_filter)
        count_query = count_query.where(CrawlJob.status == status_filter)

    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(CrawlJob.created_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(query)

    return CrawlJobListResponse(
        items=result.scalars().all(),
        total=total,
        page=page,
        size=size,
    )


@router.post("", response_model=CrawlJobResponse, status_code=status.HTTP_201_CREATED)
async def create_crawl_job(
    body: CrawlJobCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_feature("crawl_jobs_per_month")),
):
    """크롤링 작업 생성."""
    # URL 형식 간단 검증
    if not body.target_url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="유효한 URL을 입력해주세요.")

    job = CrawlJob(
        user_id=user.id,
        target_url=body.target_url,
        target_type=body.target_type,
        crawl_config=body.crawl_config,
        status=CrawlJobStatus.PENDING,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


@router.get("/{job_id}", response_model=CrawlJobResponse)
async def get_crawl_job(
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """크롤링 작업 상세."""
    return await _get_user_crawl_job(job_id, user.id, db)


@router.post("/{job_id}/start", response_model=CrawlJobResponse)
async def start_crawl_job(
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """크롤링 작업 시작 → Celery 큐 등록."""
    job = await _get_user_crawl_job(job_id, user.id, db)

    if job.status != CrawlJobStatus.PENDING:
        raise HTTPException(status_code=400, detail="PENDING 상태의 작업만 시작할 수 있습니다.")

    from app.tasks.crawling import run_crawl_job

    task = run_crawl_job.delay(str(job.id))
    job.celery_task_id = task.id
    job.status = CrawlJobStatus.RUNNING
    await db.commit()
    await db.refresh(job)
    return job


@router.post("/{job_id}/cancel", response_model=CrawlJobResponse)
async def cancel_crawl_job(
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """크롤링 작업 취소."""
    job = await _get_user_crawl_job(job_id, user.id, db)

    if job.status not in (CrawlJobStatus.PENDING, CrawlJobStatus.RUNNING):
        raise HTTPException(status_code=400, detail="진행중인 작업만 취소할 수 있습니다.")

    if job.celery_task_id:
        from app.tasks.celery_app import celery_app
        celery_app.control.revoke(job.celery_task_id, terminate=True)

    job.status = CrawlJobStatus.CANCELLED
    await db.commit()
    await db.refresh(job)
    return job


@router.get("/{job_id}/products", response_model=CrawledProductListResponse)
async def get_crawl_job_products(
    job_id: uuid.UUID,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """크롤링된 상품 목록."""
    await _get_user_crawl_job(job_id, user.id, db)

    query = select(CrawledProduct).where(CrawledProduct.crawl_job_id == job_id)
    count_query = select(func.count(CrawledProduct.id)).where(CrawledProduct.crawl_job_id == job_id)

    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(CrawledProduct.crawled_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(query)

    return CrawledProductListResponse(
        items=result.scalars().all(),
        total=total,
        page=page,
        size=size,
    )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_crawl_job(
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """크롤링 작업 삭제."""
    job = await _get_user_crawl_job(job_id, user.id, db)

    if job.status == CrawlJobStatus.RUNNING:
        raise HTTPException(status_code=400, detail="진행중인 작업은 삭제할 수 없습니다.")

    await db.delete(job)
    await db.commit()


async def _get_user_crawl_job(
    job_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession
) -> CrawlJob:
    """사용자 크롤링 작업 조회 (권한 검증 포함)."""
    result = await db.execute(
        select(CrawlJob).where(CrawlJob.id == job_id, CrawlJob.user_id == user_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="크롤링 작업을 찾을 수 없습니다.")
    return job
