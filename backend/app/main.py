"""FastAPI 앱 진입점."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_app_settings
from app.routers import (
    auth,
    categories,
    crawl_jobs,
    crawled_products,
    credentials,
    files,
    jobs,
    payments,
    products,
    quick_crawl,
    subscriptions,
    users,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 이벤트."""
    # startup
    yield
    # shutdown
    from app.core.database import get_engine
    engine = get_engine()
    if engine:
        await engine.dispose()


def create_app() -> FastAPI:
    settings = get_app_settings()

    app = FastAPI(
        title="Richlychee API",
        description="네이버 스마트스토어 대량 상품 등록 API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    prefix = "/api/v1"
    app.include_router(auth.router, prefix=prefix)
    app.include_router(users.router, prefix=prefix)
    app.include_router(credentials.router, prefix=prefix)
    app.include_router(subscriptions.router, prefix=prefix)
    app.include_router(payments.router, prefix=prefix)
    app.include_router(jobs.router, prefix=prefix)
    app.include_router(crawl_jobs.router, prefix=prefix)
    app.include_router(crawled_products.router, prefix=prefix)
    app.include_router(quick_crawl.router, prefix=prefix)
    app.include_router(files.router, prefix=prefix)
    app.include_router(categories.router, prefix=prefix)
    app.include_router(products.router, prefix=prefix)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
