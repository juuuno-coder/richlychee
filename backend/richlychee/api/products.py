"""상품 등록/조회 API."""

from __future__ import annotations

from typing import Any

from richlychee.api.client import NaverCommerceClient
from richlychee.data.models import ProductPayload
from richlychee.utils.logging import get_logger

logger = get_logger("api.products")


def _payload_to_dict(payload: ProductPayload) -> dict[str, Any]:
    """ProductPayload를 네이버 API 형식의 dict로 변환."""
    data: dict[str, Any] = {
        "originProduct": {
            "statusType": "SALE",
            "saleType": "NEW",
            "leafCategoryId": payload.category_id,
            "name": payload.name,
            "detailContent": payload.detail_content,
            "saleStartDate": "",
            "saleEndDate": "",
            "salePrice": payload.sale_price,
            "stockQuantity": payload.stock_quantity,
            "deliveryInfo": {
                "deliveryType": payload.delivery_info.delivery_type.value,
                "deliveryAttributeType": "NORMAL",
                "deliveryFee": {
                    "deliveryFeeType": payload.delivery_info.delivery_fee_type.value,
                    "baseFee": payload.delivery_info.base_fee,
                    "returnFee": payload.delivery_info.return_fee,
                    "exchangeFee": payload.delivery_info.exchange_fee,
                },
            },
            "detailAttribute": {
                "naverShoppingSearchInfo": {
                    "manufacturerName": payload.manufacturer or "",
                    "brandName": payload.brand or "",
                    "modelName": "",
                },
                "originAreaInfo": {
                    "originAreaCode": "00",
                    "content": payload.origin_area or "상세설명참조",
                    "plural": False,
                },
                "sellerCodeInfo": {
                    "sellerManagementCode": payload.seller_managed_code or "",
                },
                "productCondition": payload.product_condition.value,
            },
        },
    }

    # 조건부 무료배송 금액
    if (
        payload.delivery_info.delivery_fee_type.value == "CONDITIONAL_FREE"
        and payload.delivery_info.free_condition_amount
    ):
        data["originProduct"]["deliveryInfo"]["deliveryFee"][
            "freeConditionalAmount"
        ] = payload.delivery_info.free_condition_amount

    # 대표 이미지
    if payload.representative_image:
        data["originProduct"]["images"] = {
            "representativeImage": {"url": payload.representative_image.url},
        }
        if payload.optional_images:
            data["originProduct"]["images"]["optionalImages"] = [
                {"url": img.url} for img in payload.optional_images
            ]

    # 옵션
    if payload.options and payload.option_combinations:
        option_info: dict[str, Any] = {
            "optionCombinationSortType": "CREATE",
            "optionCombinationGroupNames": {},
            "optionCombinations": [],
        }

        for i, opt in enumerate(payload.options):
            key = f"optionGroupName{i + 1}"
            option_info["optionCombinationGroupNames"][key] = opt.name

        for combo in payload.option_combinations:
            combo_data: dict[str, Any] = {
                "stockQuantity": combo.stock_quantity,
                "price": combo.price,
                "usable": combo.use_yn,
            }
            for i, (name, value) in enumerate(combo.options.items()):
                combo_data[f"optionName{i + 1}"] = value

            if combo.seller_managed_code:
                combo_data["sellerManagementCode"] = combo.seller_managed_code

            option_info["optionCombinations"].append(combo_data)

        data["originProduct"]["optionInfo"] = option_info

    # SEO 태그
    if payload.seo_info and payload.seo_info.seller_tags:
        data["originProduct"]["detailAttribute"]["sellerTags"] = [
            {"code": 0, "text": tag} for tag in payload.seo_info.seller_tags[:10]
        ]

    return data


def register_product(client: NaverCommerceClient, payload: ProductPayload) -> dict[str, Any]:
    """상품을 네이버 스마트스토어에 등록.

    Args:
        client: HTTP 클라이언트.
        payload: 상품 페이로드.

    Returns:
        API 응답 dict.

    Raises:
        requests.HTTPError: 등록 실패 시.
    """
    data = _payload_to_dict(payload)
    logger.info("상품 등록: %s", payload.name)

    resp = client.post("products", json=data)
    resp.raise_for_status()

    result = resp.json()
    product_id = result.get("smartstoreChannelProduct", {}).get("channelProductNo")
    logger.info("상품 등록 완료: %s (ID: %s)", payload.name, product_id)

    return result


def search_products(
    client: NaverCommerceClient,
    *,
    product_name: str | None = None,
    seller_managed_code: str | None = None,
    page: int = 1,
    size: int = 50,
) -> dict[str, Any]:
    """등록된 상품 목록 조회.

    Args:
        client: HTTP 클라이언트.
        product_name: 상품명 검색어.
        seller_managed_code: 판매자 관리 코드 검색.
        page: 페이지 번호.
        size: 페이지 크기.

    Returns:
        API 응답 dict.
    """
    params: dict[str, Any] = {
        "page": page,
        "size": size,
    }
    if product_name:
        params["productName"] = product_name
    if seller_managed_code:
        params["sellerManagementCode"] = seller_managed_code

    resp = client.get("products/search", params=params)
    resp.raise_for_status()

    return resp.json()
