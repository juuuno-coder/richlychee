"""크롤링 프리셋 서비스."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crawl_preset import CrawlPreset


class CrawlPresetService:
    """크롤링 프리셋 관리 서비스."""

    # 기본 프리셋 (주요 쇼핑몰)
    DEFAULT_PRESETS = [
        {
            "name": "쿠팡",
            "site_url": "https://www.coupang.com",
            "url_pattern": r"coupang\.com",
            "crawler_type": "dynamic",
            "crawl_config": {
                "item_selector": ".search-product",
                "title_selector": ".name",
                "price_selector": ".price-value",
                "image_selector": "img.search-product-wrap-img",
                "link_selector": "a.search-product-link",
            },
            "description": "쿠팡 상품 페이지 크롤링",
        },
        {
            "name": "11번가",
            "site_url": "https://www.11st.co.kr",
            "url_pattern": r"11st\.co\.kr",
            "crawler_type": "static",
            "crawl_config": {
                "item_selector": ".c_card",
                "title_selector": ".c_card__name",
                "price_selector": ".c_card__price",
                "image_selector": "img",
                "link_selector": "a",
            },
            "description": "11번가 상품 페이지 크롤링",
        },
        {
            "name": "Amazon US",
            "site_url": "https://www.amazon.com",
            "url_pattern": r"amazon\.com",
            "crawler_type": "dynamic",
            "crawl_config": {
                "item_selector": "[data-component-type='s-search-result']",
                "title_selector": "h2 a span",
                "price_selector": ".a-price-whole",
                "image_selector": ".s-image",
                "link_selector": "h2 a",
            },
            "description": "Amazon US 상품 검색 결과 크롤링",
        },
        {
            "name": "eBay",
            "site_url": "https://www.ebay.com",
            "url_pattern": r"ebay\.com",
            "crawler_type": "static",
            "crawl_config": {
                "item_selector": ".s-item",
                "title_selector": ".s-item__title",
                "price_selector": ".s-item__price",
                "image_selector": ".s-item__image-img",
                "link_selector": ".s-item__link",
            },
            "description": "eBay 상품 검색 결과 크롤링",
        },
        {
            "name": "AliExpress",
            "site_url": "https://www.aliexpress.com",
            "url_pattern": r"aliexpress\.com",
            "crawler_type": "dynamic",
            "crawl_config": {
                "item_selector": "[data-item-id]",
                "title_selector": ".multi--titleText--nXeOvyr",
                "price_selector": ".multi--price-sale--U-S0jtj",
                "image_selector": "img",
                "link_selector": "a",
            },
            "description": "AliExpress 상품 검색 결과 크롤링",
        },
    ]

    @staticmethod
    async def find_preset_by_url(db: AsyncSession, url: str) -> CrawlPreset | None:
        """
        URL로 프리셋 찾기.

        Args:
            db: 데이터베이스 세션
            url: 크롤링 대상 URL

        Returns:
            매칭되는 프리셋 또는 None
        """
        # 모든 활성 프리셋 조회
        result = await db.execute(
            select(CrawlPreset).where(CrawlPreset.is_active == True)  # noqa: E712
        )
        presets = result.scalars().all()

        # URL 패턴 매칭
        for preset in presets:
            if re.search(preset.url_pattern, url):
                return preset

        return None

    @staticmethod
    async def auto_detect_config(url: str) -> dict | None:
        """
        URL로 크롤러 설정 자동 감지.

        Args:
            url: 크롤링 대상 URL

        Returns:
            자동 감지된 설정 또는 None
        """
        domain = urlparse(url).netloc.lower()

        # 기본 프리셋에서 매칭
        for preset in CrawlPresetService.DEFAULT_PRESETS:
            if re.search(preset["url_pattern"], domain):
                return {
                    "crawler_type": preset["crawler_type"],
                    "crawl_config": preset["crawl_config"],
                    "preset_name": preset["name"],
                }

        return None

    @staticmethod
    async def initialize_default_presets(db: AsyncSession):
        """기본 프리셋 초기화 (DB에 저장)."""
        for preset_data in CrawlPresetService.DEFAULT_PRESETS:
            # 이미 존재하는지 확인
            result = await db.execute(
                select(CrawlPreset).where(CrawlPreset.name == preset_data["name"])
            )
            existing = result.scalar_one_or_none()

            if not existing:
                preset = CrawlPreset(
                    name=preset_data["name"],
                    site_url=preset_data["site_url"],
                    url_pattern=preset_data["url_pattern"],
                    crawler_type=preset_data["crawler_type"],
                    crawl_config=preset_data["crawl_config"],
                    description=preset_data.get("description"),
                    is_public=True,
                )
                db.add(preset)

        await db.commit()
