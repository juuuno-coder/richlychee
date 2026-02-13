"""스프레드시트 → API 페이로드 변환."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from richlychee.data.models import (
    DeliveryFeeType,
    DeliveryInfo,
    ImageInfo,
    OptionCombination,
    ProductCondition,
    ProductOption,
    ProductPayload,
    ProductRow,
    OptionValue,
    SeoInfo,
)
from richlychee.utils.logging import get_logger

logger = get_logger("data.transformer")


def _parse_image_list(image_str: str) -> list[str]:
    """쉼표 구분 이미지 경로/URL을 리스트로 파싱."""
    if not image_str or not image_str.strip():
        return []
    return [img.strip() for img in image_str.split(",") if img.strip()]


def _is_url(path: str) -> bool:
    """URL인지 로컬 경로인지 판별."""
    return path.startswith("http://") or path.startswith("https://")


def _is_local_file(path: str) -> bool:
    """로컬 파일 경로인지 확인."""
    return not _is_url(path) and Path(path).suffix.lower() in {
        ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp",
    }


def row_to_product_row(row: pd.Series) -> ProductRow:
    """DataFrame 행을 ProductRow 모델로 변환."""
    data = {}
    for field in ProductRow.model_fields:
        if field in row.index:
            val = row[field]
            # pandas NA 처리
            if pd.isna(val):
                continue
            data[field] = val

    return ProductRow(**data)


def product_row_to_payload(
    row: ProductRow,
    image_url_map: dict[str, str] | None = None,
) -> ProductPayload:
    """ProductRow를 API 페이로드 모델로 변환.

    Args:
        row: 원시 데이터 행.
        image_url_map: 로컬 경로 → CDN URL 매핑 (이미지 업로드 후).

    Returns:
        ProductPayload 객체.
    """
    image_url_map = image_url_map or {}

    # 대표 이미지
    rep_image = None
    if row.representative_image:
        url = image_url_map.get(row.representative_image, row.representative_image)
        if _is_url(url):
            rep_image = ImageInfo(url=url, order=0)

    # 추가 이미지
    opt_images = []
    for i, img_path in enumerate(_parse_image_list(row.optional_images)):
        url = image_url_map.get(img_path, img_path)
        if _is_url(url):
            opt_images.append(ImageInfo(url=url, order=i + 1))

    # 옵션
    options: list[ProductOption] = []
    option_combinations: list[OptionCombination] = []

    if row.option1_name and row.option1_value:
        values1 = [v.strip() for v in row.option1_value.split(",") if v.strip()]
        options.append(
            ProductOption(
                name=row.option1_name,
                values=[OptionValue(value=v) for v in values1],
            )
        )

        if row.option2_name and row.option2_value:
            values2 = [v.strip() for v in row.option2_value.split(",") if v.strip()]
            options.append(
                ProductOption(
                    name=row.option2_name,
                    values=[OptionValue(value=v) for v in values2],
                )
            )

            # 옵션 조합 생성
            for v1 in values1:
                for v2 in values2:
                    option_combinations.append(
                        OptionCombination(
                            options={row.option1_name: v1, row.option2_name: v2},
                            stock_quantity=row.stock_quantity,
                            price=row.sale_price,
                        )
                    )
        else:
            # 단일 옵션 조합
            for v1 in values1:
                option_combinations.append(
                    OptionCombination(
                        options={row.option1_name: v1},
                        stock_quantity=row.stock_quantity,
                        price=row.sale_price,
                    )
                )

    # 배송 정보
    delivery_info = DeliveryInfo(
        delivery_fee_type=DeliveryFeeType(row.delivery_fee_type) if row.delivery_fee_type else DeliveryFeeType.PAID,
        base_fee=row.base_delivery_fee,
        free_condition_amount=int(row.free_condition_amount) if row.free_condition_amount else None,
        return_fee=row.return_fee,
        exchange_fee=row.exchange_fee,
    )

    # SEO
    seo_info = SeoInfo(
        seller_tags=[t.strip() for t in row.seller_tags.split(",") if t.strip()]
        if row.seller_tags
        else [],
    )

    # 상품 상태
    condition = ProductCondition.NEW
    if row.product_condition:
        try:
            condition = ProductCondition(row.product_condition.upper())
        except ValueError:
            pass

    return ProductPayload(
        name=row.product_name,
        category_id=row.category_id,
        sale_price=row.sale_price,
        stock_quantity=row.stock_quantity,
        product_condition=condition,
        representative_image=rep_image,
        optional_images=opt_images,
        detail_content=row.detail_content,
        options=options,
        option_combinations=option_combinations,
        delivery_info=delivery_info,
        seller_managed_code=row.seller_managed_code or None,
        brand=row.brand or None,
        manufacturer=row.manufacturer or None,
        origin_area=row.origin_area or None,
        seo_info=seo_info,
    )


def transform_dataframe(
    df: pd.DataFrame,
    image_url_map: dict[str, str] | None = None,
) -> list[ProductPayload]:
    """DataFrame 전체를 API 페이로드 리스트로 변환.

    Args:
        df: 정규화된 DataFrame.
        image_url_map: 로컬 경로 → CDN URL 매핑.

    Returns:
        ProductPayload 리스트.
    """
    payloads: list[ProductPayload] = []

    for idx, raw_row in df.iterrows():
        try:
            row = row_to_product_row(raw_row)
            payload = product_row_to_payload(row, image_url_map)
            payloads.append(payload)
        except Exception as e:
            logger.warning("행 %s 변환 실패: %s", idx, e)

    logger.info("총 %d개 상품 페이로드 생성", len(payloads))
    return payloads


def collect_local_images(df: pd.DataFrame) -> list[str]:
    """DataFrame에서 업로드가 필요한 로컬 이미지 경로 수집."""
    images: set[str] = set()

    for _, row in df.iterrows():
        rep = row.get("representative_image", "")
        if rep and isinstance(rep, str) and _is_local_file(rep):
            images.add(rep)

        opt = row.get("optional_images", "")
        if opt and isinstance(opt, str):
            for img in _parse_image_list(opt):
                if _is_local_file(img):
                    images.add(img)

    return sorted(images)
