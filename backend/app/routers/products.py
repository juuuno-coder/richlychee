"""상품 라우터."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decrypt_secret
from app.dependencies import get_current_user
from app.models.naver_credential import NaverCredential
from app.models.user import User
from app.services.naver_service import NaverService

router = APIRouter(prefix="/products", tags=["products"])


@router.get("")
async def list_products(
    credential_id: str = Query(...),
    product_name: str | None = None,
    seller_managed_code: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """등록 상품 조회."""
    import uuid

    cred_result = await db.execute(
        select(NaverCredential).where(
            NaverCredential.id == uuid.UUID(credential_id),
            NaverCredential.user_id == user.id,
        )
    )
    cred = cred_result.scalar_one_or_none()
    if not cred:
        raise HTTPException(status_code=404, detail="자격증명을 찾을 수 없습니다.")

    secret = decrypt_secret(cred.naver_client_secret)
    service = NaverService(cred.naver_client_id, secret)
    return await service.search_products(
        product_name=product_name,
        seller_managed_code=seller_managed_code,
        page=page,
        size=size,
    )
