"""네이버 API 자격증명 라우터."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decrypt_secret, encrypt_secret
from app.dependencies import get_current_user
from app.models.naver_credential import NaverCredential
from app.models.user import User
from app.schemas.credential import (
    CredentialCreate,
    CredentialResponse,
    CredentialUpdate,
    CredentialVerifyResponse,
)
from app.services.naver_service import NaverService

router = APIRouter(prefix="/credentials", tags=["credentials"])


@router.get("", response_model=list[CredentialResponse])
async def list_credentials(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """자격증명 목록."""
    result = await db.execute(
        select(NaverCredential).where(NaverCredential.user_id == user.id)
    )
    return result.scalars().all()


@router.post("", response_model=CredentialResponse, status_code=status.HTTP_201_CREATED)
async def create_credential(
    body: CredentialCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """자격증명 등록."""
    cred = NaverCredential(
        user_id=user.id,
        label=body.label,
        naver_client_id=body.naver_client_id,
        naver_client_secret=encrypt_secret(body.naver_client_secret),
    )
    db.add(cred)
    await db.commit()
    await db.refresh(cred)
    return cred


@router.patch("/{credential_id}", response_model=CredentialResponse)
async def update_credential(
    credential_id: uuid.UUID,
    body: CredentialUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """자격증명 수정."""
    cred = await _get_user_credential(credential_id, user.id, db)
    if body.label is not None:
        cred.label = body.label
    if body.naver_client_id is not None:
        cred.naver_client_id = body.naver_client_id
    if body.naver_client_secret is not None:
        cred.naver_client_secret = encrypt_secret(body.naver_client_secret)
        cred.is_verified = False
    await db.commit()
    await db.refresh(cred)
    return cred


@router.delete("/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credential(
    credential_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """자격증명 삭제."""
    cred = await _get_user_credential(credential_id, user.id, db)
    await db.delete(cred)
    await db.commit()


@router.post("/{credential_id}/verify", response_model=CredentialVerifyResponse)
async def verify_credential(
    credential_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """자격증명 인증 테스트."""
    cred = await _get_user_credential(credential_id, user.id, db)
    secret = decrypt_secret(cred.naver_client_secret)

    service = NaverService(cred.naver_client_id, secret)
    try:
        ok = await service.test_connection()
    except Exception as e:
        return CredentialVerifyResponse(success=False, message=str(e))

    if ok:
        cred.is_verified = True
        cred.last_verified_at = datetime.now(UTC)
        await db.commit()
        return CredentialVerifyResponse(success=True, message="인증 성공")

    return CredentialVerifyResponse(success=False, message="인증 실패")


async def _get_user_credential(
    credential_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> NaverCredential:
    result = await db.execute(
        select(NaverCredential).where(
            NaverCredential.id == credential_id,
            NaverCredential.user_id == user_id,
        )
    )
    cred = result.scalar_one_or_none()
    if not cred:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="자격증명을 찾을 수 없습니다.")
    return cred
