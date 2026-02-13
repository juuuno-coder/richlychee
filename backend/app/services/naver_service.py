"""기존 richlychee 모듈 래핑 서비스."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from richlychee.api.categories import get_categories, search_category
from richlychee.api.client import NaverCommerceClient
from richlychee.api.images import upload_image, upload_images_batch
from richlychee.api.products import register_product, search_products
from richlychee.auth.session import AuthSession
from richlychee.config import Settings
from richlychee.data.reader import read_file
from richlychee.data.transformer import (
    collect_local_images,
    product_row_to_payload,
    row_to_product_row,
    transform_dataframe,
)
from richlychee.data.validator import validate_dataframe


class NaverService:
    """네이버 커머스 API 래핑 서비스 (동기 → 비동기)."""

    def __init__(self, client_id: str, client_secret: str):
        self._settings = Settings(
            naver_client_id=client_id,
            naver_client_secret=client_secret,
        )
        self._auth = AuthSession(self._settings)
        self._client = NaverCommerceClient(self._settings, self._auth)

    async def test_connection(self) -> bool:
        """인증 테스트."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._auth.test_connection)

    async def validate_file(self, file_path: str | Path) -> dict[str, Any]:
        """파일 읽기 + 유효성 검증."""
        loop = asyncio.get_event_loop()
        df = await loop.run_in_executor(None, read_file, str(file_path))
        result = await loop.run_in_executor(None, validate_dataframe, df)
        return {
            "total_rows": len(df),
            "is_valid": result.is_valid,
            "errors": [
                {"row": e.row, "field": e.field, "message": e.message}
                for e in result.errors
            ],
            "warnings": [
                {"row": w.row, "field": w.field, "message": w.message}
                for w in result.warnings
            ],
        }

    async def read_file(self, file_path: str | Path):
        """파일 읽기."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, read_file, str(file_path))

    async def upload_images(self, image_paths: list[str]) -> dict[str, str]:
        """이미지 일괄 업로드."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, upload_images_batch, self._client, image_paths
        )

    async def upload_image(self, image_path: str) -> str:
        """단일 이미지 업로드."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, upload_image, self._client, image_path
        )

    async def register_product(self, payload) -> dict[str, Any]:
        """단일 상품 등록."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, register_product, self._client, payload
        )

    async def search_products(
        self,
        product_name: str | None = None,
        seller_managed_code: str | None = None,
        page: int = 1,
        size: int = 50,
    ) -> dict[str, Any]:
        """상품 검색."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            search_products,
            self._client,
            product_name,
            seller_managed_code,
            page,
            size,
        )

    async def search_categories(self, keyword: str) -> list[dict[str, Any]]:
        """카테고리 검색."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, search_category, self._client, keyword
        )

    def get_sync_client(self) -> NaverCommerceClient:
        """동기 클라이언트 반환 (Celery 워커용)."""
        return self._client

    def get_sync_settings(self) -> Settings:
        """동기 설정 반환."""
        return self._settings
