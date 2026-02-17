"""환율 계산 유틸리티."""

from __future__ import annotations

import httpx

from richlychee.utils.logging import get_logger

logger = get_logger("utils.exchange_rate")

# 환율 캐시 (메모리 캐시, 프로덕션에서는 Redis 권장)
_exchange_rate_cache: dict[str, dict[str, float]] = {}


async def get_exchange_rate(from_currency: str, to_currency: str = "KRW") -> float:
    """
    환율 조회 (캐싱 지원).

    Args:
        from_currency: 원본 통화 (USD, JPY, EUR, CNY 등)
        to_currency: 목표 통화 (기본값: KRW)

    Returns:
        환율 (예: 1 USD = 1300 KRW)

    Raises:
        httpx.HTTPError: API 요청 실패 시
    """
    # 동일 통화
    if from_currency == to_currency:
        return 1.0

    # 캐시 확인
    if from_currency in _exchange_rate_cache:
        rates = _exchange_rate_cache[from_currency]
        if to_currency in rates:
            logger.debug(
                "환율 캐시 사용: %s → %s = %.4f",
                from_currency,
                to_currency,
                rates[to_currency],
            )
            return rates[to_currency]

    # API 호출: exchangerate-api.com (무료)
    url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
    logger.info("환율 API 호출: %s", url)

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

            # 전체 환율 데이터 캐싱
            rates = data.get("rates", {})
            _exchange_rate_cache[from_currency] = rates

            if to_currency not in rates:
                raise ValueError(f"환율 데이터에 {to_currency}가 없습니다.")

            rate = rates[to_currency]
            logger.info(
                "환율 조회 성공: %s → %s = %.4f",
                from_currency,
                to_currency,
                rate,
            )
            return rate

        except httpx.HTTPError as e:
            logger.error("환율 API 호출 실패: %s", e)
            # 폴백: 기본 환율 사용
            default_rates = {
                "USD": 1300.0,
                "JPY": 9.0,
                "EUR": 1400.0,
                "CNY": 180.0,
            }
            return default_rates.get(from_currency, 1.0)


async def convert_price(
    amount: int | float,
    from_currency: str,
    to_currency: str = "KRW",
) -> int:
    """
    가격 변환.

    Args:
        amount: 원본 가격
        from_currency: 원본 통화
        to_currency: 목표 통화

    Returns:
        변환된 가격 (정수)
    """
    if from_currency == to_currency:
        return int(amount)

    rate = await get_exchange_rate(from_currency, to_currency)
    converted = int(amount * rate)

    logger.debug(
        "가격 변환: %.2f %s → %d %s (환율: %.4f)",
        amount,
        from_currency,
        converted,
        to_currency,
        rate,
    )

    return converted


def clear_exchange_rate_cache():
    """환율 캐시 초기화 (테스트용)."""
    _exchange_rate_cache.clear()
    logger.info("환율 캐시 초기화 완료")
