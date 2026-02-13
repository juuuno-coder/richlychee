"""작업 라우터."""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_app_settings
from app.core.database import get_db
from app.core.security import decrypt_secret
from app.dependencies import get_current_user
from app.models.job import Job, JobStatus
from app.models.naver_credential import NaverCredential
from app.models.product_result import ProductResult
from app.models.user import User
from app.schemas.job import (
    JobListResponse,
    JobResponse,
    ProductResultListResponse,
    ProductResultResponse,
)
from app.services.naver_service import NaverService

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=JobListResponse)
async def list_jobs(
    status_filter: JobStatus | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """작업 목록."""
    query = select(Job).where(Job.user_id == user.id)
    count_query = select(func.count(Job.id)).where(Job.user_id == user.id)

    if status_filter:
        query = query.where(Job.status == status_filter)
        count_query = count_query.where(Job.status == status_filter)

    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(Job.created_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(query)

    return JobListResponse(
        items=result.scalars().all(),
        total=total,
        page=page,
        size=size,
    )


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    file: UploadFile,
    credential_id: uuid.UUID,
    dry_run: bool = False,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """작업 생성 (파일 업로드 + 자동 검증)."""
    settings = get_app_settings()

    # 자격증명 확인
    cred_result = await db.execute(
        select(NaverCredential).where(
            NaverCredential.id == credential_id,
            NaverCredential.user_id == user.id,
        )
    )
    cred = cred_result.scalar_one_or_none()
    if not cred:
        raise HTTPException(status_code=404, detail="자격증명을 찾을 수 없습니다.")

    # 파일 확장자 확인
    filename = file.filename or "upload.xlsx"
    suffix = Path(filename).suffix.lower()
    if suffix not in (".xlsx", ".csv"):
        raise HTTPException(status_code=400, detail="xlsx 또는 csv 파일만 업로드할 수 있습니다.")

    # 파일 저장
    upload_dir = Path(settings.upload_dir) / str(user.id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4()}{suffix}"
    stored_path = upload_dir / stored_name

    with open(stored_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # 검증
    secret = decrypt_secret(cred.naver_client_secret)
    service = NaverService(cred.naver_client_id, secret)
    validation = await service.validate_file(str(stored_path))

    job = Job(
        user_id=user.id,
        credential_id=credential_id,
        status=JobStatus.PENDING if validation["is_valid"] else JobStatus.FAILED,
        original_filename=filename,
        stored_file_path=str(stored_path),
        dry_run=dry_run,
        total_rows=validation["total_rows"],
        validation_errors=validation["errors"] if validation["errors"] else None,
        validation_warnings=validation["warnings"] if validation["warnings"] else None,
        error_message="검증 실패" if not validation["is_valid"] else None,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """작업 상세."""
    return await _get_user_job(job_id, user.id, db)


@router.post("/{job_id}/start", response_model=JobResponse)
async def start_job(
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """작업 실행 → Celery 큐 등록."""
    job = await _get_user_job(job_id, user.id, db)
    if job.status != JobStatus.PENDING:
        raise HTTPException(status_code=400, detail="PENDING 상태의 작업만 시작할 수 있습니다.")

    from app.tasks.registration import run_registration

    task = run_registration.delay(str(job.id))
    job.celery_task_id = task.id
    job.status = JobStatus.VALIDATING
    await db.commit()
    await db.refresh(job)
    return job


@router.post("/{job_id}/cancel", response_model=JobResponse)
async def cancel_job(
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """작업 취소."""
    job = await _get_user_job(job_id, user.id, db)
    active = {JobStatus.PENDING, JobStatus.VALIDATING, JobStatus.UPLOADING, JobStatus.RUNNING}
    if job.status not in active:
        raise HTTPException(status_code=400, detail="진행중인 작업만 취소할 수 있습니다.")

    if job.celery_task_id:
        from app.tasks.celery_app import celery_app
        celery_app.control.revoke(job.celery_task_id, terminate=True)

    job.status = JobStatus.CANCELLED
    await db.commit()
    await db.refresh(job)
    return job


@router.get("/{job_id}/results", response_model=ProductResultListResponse)
async def get_job_results(
    job_id: uuid.UUID,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    success: bool | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """작업 결과 목록."""
    await _get_user_job(job_id, user.id, db)

    query = select(ProductResult).where(ProductResult.job_id == job_id)
    count_query = select(func.count(ProductResult.id)).where(ProductResult.job_id == job_id)

    if success is not None:
        query = query.where(ProductResult.success == success)
        count_query = count_query.where(ProductResult.success == success)

    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(ProductResult.row_index).offset((page - 1) * size).limit(size)
    result = await db.execute(query)

    return ProductResultListResponse(items=result.scalars().all(), total=total, page=page, size=size)


@router.get("/{job_id}/results/export")
async def export_job_results(
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """결과 엑셀 다운로드."""
    import io

    import pandas as pd
    from fastapi.responses import StreamingResponse

    job = await _get_user_job(job_id, user.id, db)
    result = await db.execute(
        select(ProductResult).where(ProductResult.job_id == job_id).order_by(ProductResult.row_index)
    )
    results = result.scalars().all()

    rows = [
        {
            "행": r.row_index + 1,
            "상품명": r.product_name,
            "결과": "성공" if r.success else "실패",
            "상품ID": r.naver_product_id or "",
            "오류": r.error_message or "",
        }
        for r in results
    ]
    df = pd.DataFrame(rows)
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="results_{job.id}.xlsx"'},
    )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """작업 삭제."""
    job = await _get_user_job(job_id, user.id, db)
    active = {JobStatus.VALIDATING, JobStatus.UPLOADING, JobStatus.RUNNING}
    if job.status in active:
        raise HTTPException(status_code=400, detail="진행중인 작업은 삭제할 수 없습니다.")
    await db.delete(job)
    await db.commit()


async def _get_user_job(
    job_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession
) -> Job:
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.user_id == user_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
    return job
