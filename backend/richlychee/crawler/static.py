"""정적 페이지 크롤러 (BeautifulSoup4)."""

from __future__ import annotations

import httpx
from bs4 import BeautifulSoup

from richlychee.crawler.base import BaseCrawler
from richlychee.crawler.extractor import (
    clean_text,
    detect_currency,
    extract_image_url,
    parse_price,
)


class StaticCrawler(BaseCrawler):
    """BeautifulSoup을 사용한 정적 HTML 페이지 크롤러."""

    async def crawl(self) -> list[dict]:
        """
        BeautifulSoup으로 정적 페이지 크롤링.

        Returns:
            상품 정보 리스트
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            try:
                resp = await client.get(self.url, headers=headers)
                resp.raise_for_status()
            except httpx.HTTPError as e:
                raise RuntimeError(f"HTTP 요청 실패: {e}") from e

            # HTML 파싱
            soup = BeautifulSoup(resp.text, "lxml")

            # config에서 셀렉터 읽기
            item_selector = self.config.get("item_selector", ".product-item")
            items = soup.select(item_selector)

            if not items:
                return []

            # 각 상품 아이템 추출
            products = []
            for item in items:
                try:
                    product = self.extract_product(item)
                    if product and product.get("title"):  # 필수 필드 검증
                        products.append(product)
                except Exception as e:
                    # 개별 상품 파싱 실패는 무시하고 계속
                    print(f"상품 추출 실패: {e}")
                    continue

            return products

    def extract_product(self, element) -> dict:
        """
        HTML 요소에서 상품 정보 추출.

        Args:
            element: BeautifulSoup element

        Returns:
            상품 정보 딕셔너리
        """
        # 셀렉터 읽기 (기본값 제공)
        title_selector = self.config.get("title_selector", ".title")
        price_selector = self.config.get("price_selector", ".price")
        image_selector = self.config.get("image_selector", "img")
        link_selector = self.config.get("link_selector", "a")

        # 제목 추출
        title_elem = element.select_one(title_selector)
        title = clean_text(title_elem.text) if title_elem else ""

        # 가격 추출
        price_elem = element.select_one(price_selector)
        if price_elem:
            price_text = clean_text(price_elem.text)
            price = parse_price(price_text)
            currency = detect_currency(price_text)
        else:
            price = 0
            currency = "KRW"

        # 이미지 추출 (여러 개)
        image_elems = element.select(image_selector)
        images = []
        for img in image_elems:
            img_url = extract_image_url(img, self.url)
            if img_url and img_url.startswith("http"):
                images.append(img_url)

        # 링크 추출
        link_elem = element.select_one(link_selector)
        url = ""
        if link_elem and link_elem.has_attr("href"):
            url = link_elem["href"]
            # 상대 URL → 절대 URL 변환
            if url.startswith("/"):
                from urllib.parse import urljoin
                url = urljoin(self.url, url)

        return {
            "title": title,
            "price": price,
            "currency": currency,
            "images": images,
            "url": url,
        }
