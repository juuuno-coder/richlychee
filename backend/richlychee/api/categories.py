"""카테고리 조회 API."""

from __future__ import annotations

from typing import Any

from richlychee.api.client import NaverCommerceClient
from richlychee.utils.logging import get_logger

logger = get_logger("api.categories")


def get_categories(client: NaverCommerceClient) -> list[dict[str, Any]]:
    """전체 카테고리 목록 조회.

    Returns:
        카테고리 dict 리스트.
    """
    resp = client.get("categories")
    resp.raise_for_status()

    categories = resp.json()
    logger.info("카테고리 %d개 조회", len(categories))
    return categories


def search_category(
    client: NaverCommerceClient,
    keyword: str,
) -> list[dict[str, Any]]:
    """키워드로 카테고리 검색.

    Args:
        keyword: 검색 키워드.

    Returns:
        매칭 카테고리 리스트.
    """
    resp = client.get("categories", params={"keyword": keyword})
    resp.raise_for_status()

    results = resp.json()
    logger.info("카테고리 검색 '%s': %d건", keyword, len(results))
    return results


def get_category_attributes(
    client: NaverCommerceClient,
    category_id: str,
) -> dict[str, Any]:
    """특정 카테고리의 상세 속성 조회.

    Args:
        category_id: 카테고리 ID.

    Returns:
        카테고리 속성 dict.
    """
    resp = client.get(f"categories/{category_id}/attributes")
    resp.raise_for_status()

    return resp.json()
