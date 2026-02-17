"""동적 페이지 크롤러 (Playwright)."""

from __future__ import annotations

from playwright.async_api import async_playwright

from richlychee.crawler.base import BaseCrawler
from richlychee.crawler.extractor import (
    clean_text,
    detect_currency,
    parse_price,
)


class DynamicCrawler(BaseCrawler):
    """Playwright를 사용한 동적 JavaScript 페이지 크롤러."""

    async def crawl(self) -> list[dict]:
        """
        Playwright로 동적 페이지 크롤링.

        Returns:
            상품 정보 리스트
        """
        async with async_playwright() as p:
            # 브라우저 실행
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                ]
            )
            page = await browser.new_page()

            # User-Agent 설정
            await page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/120.0.0.0 Safari/537.36"
            })

            try:
                # 페이지 로드
                await page.goto(self.url, wait_until="networkidle", timeout=30000)

                # 셀렉터 대기
                item_selector = self.config.get("item_selector", ".product-item")
                await page.wait_for_selector(item_selector, timeout=10000)

                # 상품 요소 찾기
                items = await page.query_selector_all(item_selector)

                products = []
                for item in items:
                    try:
                        product = await self.extract_product(item)
                        if product and product.get("title"):
                            products.append(product)
                    except Exception as e:
                        print(f"상품 추출 실패: {e}")
                        continue

                return products

            finally:
                await browser.close()

    async def extract_product(self, element) -> dict:
        """
        Playwright 요소에서 상품 정보 추출.

        Args:
            element: Playwright ElementHandle

        Returns:
            상품 정보 딕셔너리
        """
        # 셀렉터 읽기
        title_selector = self.config.get("title_selector", ".title")
        price_selector = self.config.get("price_selector", ".price")
        image_selector = self.config.get("image_selector", "img")
        link_selector = self.config.get("link_selector", "a")

        # 제목 추출
        title_elem = await element.query_selector(title_selector)
        title = ""
        if title_elem:
            title_text = await title_elem.inner_text()
            title = clean_text(title_text)

        # 가격 추출
        price = 0
        currency = "KRW"
        price_elem = await element.query_selector(price_selector)
        if price_elem:
            price_text = await price_elem.inner_text()
            price_text = clean_text(price_text)
            price = parse_price(price_text)
            currency = detect_currency(price_text)

        # 이미지 추출
        images = []
        image_elems = await element.query_selector_all(image_selector)
        for img in image_elems:
            img_url = await img.get_attribute("src")
            if not img_url:
                img_url = await img.get_attribute("data-src")
            if img_url and img_url.startswith("http"):
                images.append(img_url)

        # 링크 추출
        url = ""
        link_elem = await element.query_selector(link_selector)
        if link_elem:
            href = await link_elem.get_attribute("href")
            if href:
                # 상대 URL → 절대 URL 변환
                if href.startswith("/"):
                    from urllib.parse import urljoin
                    url = urljoin(self.url, href)
                else:
                    url = href

        return {
            "title": title,
            "price": price,
            "currency": currency,
            "images": images,
            "url": url,
        }
