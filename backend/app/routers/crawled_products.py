"""크롤링된 상품 라우터."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.crawled_product import CrawledProduct
from app.models.job import Job, JobStatus
from app.models.user import User
from app.schemas.crawled_product import (
    CrawledProductListResponse,
    CrawledProductResponse,
    CrawledProductUpdate,
    PriceAdjustmentRequest,
    RegisterCrawledRequest,
)
from app.schemas.job import JobResponse

router = APIRouter(prefix="/crawled-products", tags=["crawled-products"])


@router.get("", response_model=CrawledProductListResponse)
async def list_crawled_products(
    crawl_job_id: uuid.UUID | None = Query(None),
    is_registered: bool | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """크롤링된 상품 목록 (필터: crawl_job_id, is_registered)."""
    query = select(CrawledProduct).where(CrawledProduct.user_id == user.id)
    count_query = select(func.count(CrawledProduct.id)).where(CrawledProduct.user_id == user.id)

    if crawl_job_id:
        query = query.where(CrawledProduct.crawl_job_id == crawl_job_id)
        count_query = count_query.where(CrawledProduct.crawl_job_id == crawl_job_id)

    if is_registered is not None:
        query = query.where(CrawledProduct.is_registered == is_registered)
        count_query = count_query.where(CrawledProduct.is_registered == is_registered)

    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(CrawledProduct.crawled_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(query)

    return CrawledProductListResponse(
        items=result.scalars().all(),
        total=total,
        page=page,
        size=size,
    )


@router.get("/{id}", response_model=CrawledProductResponse)
async def get_crawled_product(
    id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """크롤링된 상품 상세 조회."""
    return await _get_user_product(id, user.id, db)


@router.put("/{id}", response_model=CrawledProductResponse)
async def update_crawled_product(
    id: uuid.UUID,
    body: CrawledProductUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """크롤링된 상품 수정 (product_name, sale_price, category_id 등)."""
    product = await _get_user_product(id, user.id, db)

    # 수정 가능한 필드만 업데이트
    if body.product_name is not None:
        product.product_name = body.product_name
    if body.sale_price is not None:
        product.sale_price = body.sale_price
    if body.category_id is not None:
        product.category_id = body.category_id
    if body.stock_quantity is not None:
        product.stock_quantity = body.stock_quantity
    if body.detail_content is not None:
        product.detail_content = body.detail_content
    if body.representative_image is not None:
        product.representative_image = body.representative_image
    if body.optional_images is not None:
        product.optional_images = body.optional_images

    from datetime import UTC, datetime
    product.updated_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(product)
    return product


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_crawled_product(
    id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """크롤링된 상품 삭제."""
    product = await _get_user_product(id, user.id, db)
    await db.delete(product)
    await db.commit()


@router.post("/adjust-price")
async def adjust_price(
    body: PriceAdjustmentRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """선택된 상품 가격 일괄 조정."""
    if not body.product_ids:
        raise HTTPException(status_code=400, detail="조정할 상품을 선택해주세요.")

    # 사용자 소유 상품인지 확인
    result = await db.execute(
        select(CrawledProduct).where(
            CrawledProduct.id.in_(body.product_ids),
            CrawledProduct.user_id == user.id,
        )
    )
    products = result.scalars().all()

    if len(products) != len(body.product_ids):
        raise HTTPException(status_code=404, detail="일부 상품을 찾을 수 없습니다.")

    # 가격 조정 로직
    for product in products:
        original_price = product.sale_price or product.original_price

        if body.adjustment_type == "percentage":
            # 퍼센트 기반 조정 (예: 10% 인상 = +10.0)
            adjusted_price = int(original_price * (1 + body.adjustment_value / 100))
        elif body.adjustment_type == "fixed":
            # 고정 금액 조정
            adjusted_price = original_price + int(body.adjustment_value)
        else:
            raise HTTPException(status_code=400, detail="지원하지 않는 조정 타입입니다.")

        product.sale_price = max(adjusted_price, 0)  # 음수 방지
        product.price_adjustment_type = body.adjustment_type
        product.price_adjustment_value = body.adjustment_value

    await db.commit()

    return {
        "message": f"{len(products)}개 상품의 가격이 조정되었습니다.",
        "adjusted_count": len(products),
    }


@router.post("/register", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def register_crawled_products(
    body: RegisterCrawledRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """크롤링된 상품으로 Job 생성 및 시작."""
    if not body.product_ids:
        raise HTTPException(status_code=400, detail="등록할 상품을 선택해주세요.")

    # 자격증명 확인
    from app.models.naver_credential import NaverCredential
    cred_result = await db.execute(
        select(NaverCredential).where(
            NaverCredential.id == body.credential_id,
            NaverCredential.user_id == user.id,
        )
    )
    cred = cred_result.scalar_one_or_none()
    if not cred:
        raise HTTPException(status_code=404, detail="자격증명을 찾을 수 없습니다.")

    # 상품 조회
    result = await db.execute(
        select(CrawledProduct).where(
            CrawledProduct.id.in_(body.product_ids),
            CrawledProduct.user_id == user.id,
        )
    )
    products = result.scalars().all()

    if not products:
        raise HTTPException(status_code=404, detail="선택된 상품이 없습니다.")

    # 필수 필드 검증
    for p in products:
        if not p.product_name or not p.sale_price:
            raise HTTPException(
                status_code=400,
                detail=f"상품 '{p.original_title}'에 필수 필드가 누락되었습니다.",
            )

    # Job 생성
    job = Job(
        user_id=user.id,
        credential_id=body.credential_id,
        status=JobStatus.PENDING,
        source_type="crawled",
        crawled_product_ids=[str(p.id) for p in products],
        original_filename="crawled_products.xlsx",
        stored_file_path="",
        dry_run=body.dry_run,
        total_rows=len(products),
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Celery 태스크 시작
    from app.tasks.registration import run_registration
    task = run_registration.delay(str(job.id))

    job.celery_task_id = task.id
    job.status = JobStatus.VALIDATING
    await db.commit()
    await db.refresh(job)

    return job


@router.get("/export")
async def export_crawled_products(
    crawl_job_id: uuid.UUID | None = Query(None),
    is_registered: bool | None = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """크롤링된 상품 엑셀 내보내기."""
    import io

    import pandas as pd
    from fastapi.responses import StreamingResponse

    query = select(CrawledProduct).where(CrawledProduct.user_id == user.id)

    if crawl_job_id:
        query = query.where(CrawledProduct.crawl_job_id == crawl_job_id)
    if is_registered is not None:
        query = query.where(CrawledProduct.is_registered == is_registered)

    result = await db.execute(query.order_by(CrawledProduct.crawled_at))
    products = result.scalars().all()

    rows = [
        {
            "ID": str(p.id),
            "원본 제목": p.original_title,
            "원본 가격": p.original_price,
            "통화": p.original_currency,
            "상품명": p.product_name or "",
            "판매가": p.sale_price or 0,
            "재고": p.stock_quantity,
            "카테고리ID": p.category_id or "",
            "등록 여부": "O" if p.is_registered else "X",
            "원본 URL": p.original_url,
            "크롤링 시간": p.crawled_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for p in products
    ]
    df = pd.DataFrame(rows)
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    buf.seek(0)

    filename = f"crawled_products_{crawl_job_id or 'all'}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


async def _get_user_product(
    product_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession
) -> CrawledProduct:
    """사용자 상품 조회 (권한 검증 포함)."""
    result = await db.execute(
        select(CrawledProduct).where(
            CrawledProduct.id == product_id,
            CrawledProduct.user_id == user_id,
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")
    return product
