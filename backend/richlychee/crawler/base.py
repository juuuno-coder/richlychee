"""크롤러 베이스 클래스."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseCrawler(ABC):
    """모든 크롤러의 베이스 클래스."""

    def __init__(self, url: str, config: dict | None = None):
        """
        Args:
            url: 크롤링 대상 URL
            config: 크롤링 설정 (셀렉터, 페이지네이션 등)
        """
        self.url = url
        self.config = config or {}

    @abstractmethod
    async def crawl(self) -> list[dict]:
        """
        크롤링 실행 → 원시 데이터 리스트 반환.

        Returns:
            크롤링된 상품 정보 리스트
        """
        pass

    @abstractmethod
    def extract_product(self, raw_data: Any) -> dict:
        """
        원시 데이터 → 상품 정보 변환.

        Args:
            raw_data: 크롤러별 원시 데이터 (HTML element, JSON 등)

        Returns:
            상품 정보 딕셔너리 {title, price, images, url, ...}
        """
        pass
