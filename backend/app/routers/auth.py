"""인증 라우터."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from jwt.exceptions import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    SocialLoginRequest,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """이메일 회원가입."""
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 등록된 이메일입니다.",
        )

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        name=body.name,
        provider="email",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """이메일 로그인."""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 계정입니다.",
        )

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """토큰 갱신."""
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise InvalidTokenError("Not a refresh token")
        user_id = payload["sub"]
    except (InvalidTokenError, KeyError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 리프레시 토큰입니다.",
        ) from exc

    from uuid import UUID
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="사용자를 찾을 수 없습니다.")

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/social/{provider}", response_model=TokenResponse)
async def social_login(
    provider: str,
    body: SocialLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """소셜 로그인 (네이버/카카오)."""
    import httpx

    if provider not in ("naver", "kakao"):
        raise HTTPException(status_code=400, detail="지원하지 않는 소셜 로그인입니다.")

    # 소셜 프로필 조회
    async with httpx.AsyncClient() as client:
        if provider == "naver":
            resp = await client.get(
                "https://openapi.naver.com/v1/nid/me",
                headers={"Authorization": f"Bearer {body.access_token}"},
            )
            data = resp.json().get("response", {})
            social_id = data.get("id")
            email = data.get("email")
            name = data.get("name", "")
            avatar = data.get("profile_image")
        else:  # kakao
            resp = await client.get(
                "https://kapi.kakao.com/v2/user/me",
                headers={"Authorization": f"Bearer {body.access_token}"},
            )
            data = resp.json()
            social_id = str(data.get("id"))
            account = data.get("kakao_account", {})
            email = account.get("email")
            name = account.get("profile", {}).get("nickname", "")
            avatar = account.get("profile", {}).get("profile_image_url")

    if not email:
        raise HTTPException(status_code=400, detail="소셜 계정에서 이메일을 가져올 수 없습니다.")

    # 기존 사용자 확인
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            email=email,
            name=name,
            provider=provider,
            provider_account_id=social_id,
            avatar_url=avatar,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )
