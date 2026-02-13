"""카테고리 라우터."""

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

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/search")
async def search_categories(
    keyword: str = Query(..., min_length=1),
    credential_id: str = Query(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """카테고리 검색."""
    import uuid as _uuid

    cred_result = await db.execute(
        select(NaverCredential).where(
            NaverCredential.id == _uuid.UUID(credential_id),
            NaverCredential.user_id == user.id,
        )
    )
    cred = cred_result.scalar_one_or_none()
    if not cred:
        raise HTTPException(status_code=404, detail="자격증명을 찾을 수 없습니다.")

    secret = decrypt_secret(cred.naver_client_secret)
    service = NaverService(cred.naver_client_id, secret)
    results = await service.search_categories(keyword)
    return results
