"""데이터 추출 헬퍼 함수."""

from __future__ import annotations

import re


def parse_price(price_str: str) -> int:
    """
    가격 문자열 → 정수 변환.

    Examples:
        "₩29,900" → 29900
        "$29.90" → 2990
        "¥2,990" → 2990
        "29.900원" → 29900

    Args:
        price_str: 가격 문자열

    Returns:
        정수형 가격 (소수점 제거)
    """
    # 숫자와 소수점만 남기고 제거
    cleaned = re.sub(r'[^\d.]', '', price_str)

    if not cleaned:
        return 0

    # 소수점 제거 (예: "29.90" → "2990")
    cleaned = cleaned.replace('.', '')

    try:
        return int(cleaned)
    except ValueError:
        return 0


def detect_currency(price_str: str) -> str:
    """
    통화 기호 감지.

    Args:
        price_str: 가격 문자열

    Returns:
        통화 코드 ('KRW', 'USD', 'JPY', 'EUR', 'CNY')
    """
    if "₩" in price_str or "원" in price_str:
        return "KRW"
    elif "$" in price_str:
        return "USD"
    elif "¥" in price_str or "円" in price_str:
        return "JPY"
    elif "€" in price_str:
        return "EUR"
    elif "¥" in price_str or "元" in price_str:
        return "CNY"

    return "KRW"  # 기본값


def clean_text(text: str) -> str:
    """
    텍스트 정리 (공백, 줄바꿈 제거).

    Args:
        text: 원본 텍스트

    Returns:
        정리된 텍스트
    """
    if not text:
        return ""

    # 여러 공백을 하나로, 앞뒤 공백 제거
    return re.sub(r'\s+', ' ', text).strip()


def extract_image_url(img_element, base_url: str = "") -> str | None:
    """
    이미지 요소에서 URL 추출 (src, data-src 등).

    Args:
        img_element: BeautifulSoup 이미지 요소
        base_url: 상대 URL 변환을 위한 베이스 URL

    Returns:
        이미지 URL 또는 None
    """
    # src 또는 data-src 속성에서 URL 추출
    url = img_element.get("src") or img_element.get("data-src") or img_element.get("data-original")

    if not url:
        return None

    # 상대 URL을 절대 URL로 변환
    if url.startswith("//"):
        return "https:" + url
    elif url.startswith("/") and base_url:
        from urllib.parse import urljoin
        return urljoin(base_url, url)

    return url
