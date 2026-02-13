"""사전 검증 (API 호출 전)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from richlychee.data.models import DeliveryFeeType, ProductCondition, ProductRow
from richlychee.data.transformer import _is_local_file, _is_url, _parse_image_list
from richlychee.utils.logging import get_logger

logger = get_logger("data.validator")


@dataclass
class ValidationError:
    """검증 오류 1건."""

    row: int
    field: str
    message: str

    def __str__(self) -> str:
        return f"[행 {self.row}] {self.field}: {self.message}"


@dataclass
class ValidationResult:
    """전체 검증 결과."""

    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    @property
    def total_errors(self) -> int:
        return len(self.errors)

    @property
    def total_warnings(self) -> int:
        return len(self.warnings)


def _validate_required_fields(row_idx: int, row: pd.Series, result: ValidationResult) -> None:
    """필수 필드 검증."""
    required = {
        "product_name": "상품명",
        "category_id": "카테고리 ID",
        "sale_price": "판매가",
    }

    for field_name, label in required.items():
        val = row.get(field_name)
        if val is None or (isinstance(val, str) and not val.strip()) or (isinstance(val, (int, float)) and pd.isna(val)):
            result.errors.append(
                ValidationError(row=row_idx, field=field_name, message=f"{label}은(는) 필수입니다")
            )


def _validate_price(row_idx: int, row: pd.Series, result: ValidationResult) -> None:
    """가격 검증."""
    price = row.get("sale_price", 0)
    if isinstance(price, (int, float)) and not pd.isna(price):
        if price <= 0:
            result.errors.append(
                ValidationError(row=row_idx, field="sale_price", message="판매가는 0보다 커야 합니다")
            )
        if price > 999_999_999:
            result.errors.append(
                ValidationError(row=row_idx, field="sale_price", message="판매가가 허용 범위를 초과합니다")
            )


def _validate_stock(row_idx: int, row: pd.Series, result: ValidationResult) -> None:
    """재고 검증."""
    stock = row.get("stock_quantity", 0)
    if isinstance(stock, (int, float)) and not pd.isna(stock):
        if stock < 0:
            result.errors.append(
                ValidationError(row=row_idx, field="stock_quantity", message="재고 수량은 0 이상이어야 합니다")
            )


def _validate_images(row_idx: int, row: pd.Series, result: ValidationResult) -> None:
    """이미지 검증."""
    rep_image = row.get("representative_image", "")
    if rep_image and isinstance(rep_image, str) and rep_image.strip():
        if _is_local_file(rep_image) and not Path(rep_image).exists():
            result.warnings.append(
                ValidationError(
                    row=row_idx,
                    field="representative_image",
                    message=f"로컬 이미지 파일이 존재하지 않습니다: {rep_image}",
                )
            )

    opt_images = row.get("optional_images", "")
    if opt_images and isinstance(opt_images, str):
        images = _parse_image_list(opt_images)
        if len(images) > 9:
            result.errors.append(
                ValidationError(
                    row=row_idx,
                    field="optional_images",
                    message=f"추가 이미지는 최대 9장입니다 (현재 {len(images)}장)",
                )
            )
        for img in images:
            if _is_local_file(img) and not Path(img).exists():
                result.warnings.append(
                    ValidationError(
                        row=row_idx,
                        field="optional_images",
                        message=f"로컬 이미지 파일이 존재하지 않습니다: {img}",
                    )
                )


def _validate_delivery(row_idx: int, row: pd.Series, result: ValidationResult) -> None:
    """배송 정보 검증."""
    fee_type = row.get("delivery_fee_type", "PAID")
    if fee_type and isinstance(fee_type, str) and fee_type.strip():
        try:
            DeliveryFeeType(fee_type.strip().upper())
        except ValueError:
            result.errors.append(
                ValidationError(
                    row=row_idx,
                    field="delivery_fee_type",
                    message=f"유효하지 않은 배송비 유형: {fee_type} (FREE, PAID, CONDITIONAL_FREE)",
                )
            )

    if fee_type and str(fee_type).strip().upper() == "CONDITIONAL_FREE":
        cond_amount = row.get("free_condition_amount")
        if cond_amount is None or (isinstance(cond_amount, float) and pd.isna(cond_amount)):
            result.errors.append(
                ValidationError(
                    row=row_idx,
                    field="free_condition_amount",
                    message="조건부 무료배송 시 무료배송 조건 금액은 필수입니다",
                )
            )


def _validate_product_condition(row_idx: int, row: pd.Series, result: ValidationResult) -> None:
    """상품 상태 검증."""
    condition = row.get("product_condition", "NEW")
    if condition and isinstance(condition, str) and condition.strip():
        try:
            ProductCondition(condition.strip().upper())
        except ValueError:
            result.errors.append(
                ValidationError(
                    row=row_idx,
                    field="product_condition",
                    message=f"유효하지 않은 상품 상태: {condition} (NEW, USED, REFURBISHED)",
                )
            )


def _validate_product_name(row_idx: int, row: pd.Series, result: ValidationResult) -> None:
    """상품명 길이 검증."""
    name = row.get("product_name", "")
    if isinstance(name, str) and len(name) > 100:
        result.errors.append(
            ValidationError(
                row=row_idx,
                field="product_name",
                message=f"상품명은 100자 이내여야 합니다 (현재 {len(name)}자)",
            )
        )


def validate_dataframe(df: pd.DataFrame) -> ValidationResult:
    """DataFrame 전체를 검증.

    Args:
        df: 정규화된 DataFrame.

    Returns:
        ValidationResult 객체.
    """
    result = ValidationResult()

    if df.empty:
        result.errors.append(
            ValidationError(row=0, field="", message="데이터가 비어있습니다")
        )
        return result

    for idx, row in df.iterrows():
        row_num = int(idx) + 2  # 엑셀 행 번호 (헤더=1행)

        _validate_required_fields(row_num, row, result)
        _validate_price(row_num, row, result)
        _validate_stock(row_num, row, result)
        _validate_images(row_num, row, result)
        _validate_delivery(row_num, row, result)
        _validate_product_condition(row_num, row, result)
        _validate_product_name(row_num, row, result)

    if result.is_valid:
        logger.info("검증 통과: %d개 행, 경고 %d건", len(df), result.total_warnings)
    else:
        logger.error(
            "검증 실패: 오류 %d건, 경고 %d건",
            result.total_errors,
            result.total_warnings,
        )

    return result
