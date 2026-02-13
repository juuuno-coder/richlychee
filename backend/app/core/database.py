"""SQLAlchemy 비동기 세션 설정."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_app_settings


class Base(DeclarativeBase):
    """ORM 모델 베이스 클래스."""


_engine = None
_session_factory = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_app_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            pool_pre_ping=True,
        )
    return _engine


def get_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 의존성: DB 세션."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        await session.close()
