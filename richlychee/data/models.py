"""Pydantic 데이터 모델 - 네이버 커머스 API 상품 페이로드 구조."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ProductCondition(str, Enum):
    """상품 상태."""

    NEW = "NEW"
    USED = "USED"
    REFURBISHED = "REFURBISHED"


class DeliveryType(str, Enum):
    """배송 유형."""

    DELIVERY = "DELIVERY"
    DIRECT = "DIRECT"  # 직접 전달


class DeliveryFeeType(str, Enum):
    """배송비 유형."""

    FREE = "FREE"
    PAID = "PAID"
    CONDITIONAL_FREE = "CONDITIONAL_FREE"


class ImageInfo(BaseModel):
    """이미지 정보."""

    url: str = Field(..., description="이미지 URL (네이버 CDN)")
    order: int = Field(default=0, ge=0, description="이미지 순서 (0부터)")


class OptionValue(BaseModel):
    """옵션 값."""

    id: str | None = None
    value: str = Field(..., min_length=1, description="옵션 값 (예: 빨강, L)")


class ProductOption(BaseModel):
    """상품 옵션."""

    name: str = Field(..., min_length=1, description="옵션명 (예: 색상, 사이즈)")
    values: list[OptionValue] = Field(default_factory=list)


class OptionCombination(BaseModel):
    """옵션 조합 (개별 SKU)."""

    options: dict[str, str] = Field(..., description="옵션명:옵션값 매핑")
    stock_quantity: int = Field(..., ge=0, description="재고 수량")
    price: int = Field(..., ge=0, description="판매가")
    seller_managed_code: str | None = Field(default=None, description="판매자 관리 코드")
    use_yn: bool = Field(default=True, description="사용 여부")


class DeliveryInfo(BaseModel):
    """배송 정보."""

    delivery_type: DeliveryType = Field(default=DeliveryType.DELIVERY)
    delivery_fee_type: DeliveryFeeType = Field(default=DeliveryFeeType.PAID)
    base_fee: int = Field(default=0, ge=0, description="기본 배송비")
    free_condition_amount: int | None = Field(
        default=None, ge=0, description="무료 배송 조건 금액"
    )
    return_fee: int = Field(default=0, ge=0, description="반품 배송비")
    exchange_fee: int = Field(default=0, ge=0, description="교환 배송비")
    delivery_company: str | None = Field(default=None, description="택배사 코드")

    @field_validator("free_condition_amount")
    @classmethod
    def validate_conditional_free(cls, v: int | None, info: Any) -> int | None:
        fee_type = info.data.get("delivery_fee_type")
        if fee_type == DeliveryFeeType.CONDITIONAL_FREE and v is None:
            raise ValueError("조건부 무료배송 시 free_condition_amount는 필수입니다")
        return v


class DetailAttribute(BaseModel):
    """상품 상세 속성."""

    attribute_seq: int = Field(..., description="속성 시퀀스 번호")
    attribute_value_seq: int | None = Field(default=None, description="속성 값 시퀀스 번호")
    custom_value: str | None = Field(default=None, description="사용자 정의 값")


class SeoInfo(BaseModel):
    """SEO 정보."""

    page_title: str | None = Field(default=None, max_length=60, description="페이지 제목")
    meta_description: str | None = Field(
        default=None, max_length=160, description="메타 설명"
    )
    seller_tags: list[str] = Field(default_factory=list, description="판매자 태그")


class ProductPayload(BaseModel):
    """네이버 커머스 API 상품 등록 페이로드."""

    name: str = Field(..., min_length=1, max_length=100, description="상품명")
    category_id: str = Field(..., description="카테고리 ID")
    sale_price: int = Field(..., gt=0, description="판매가")
    stock_quantity: int = Field(..., ge=0, description="재고 수량")

    # 상품 상태
    product_condition: ProductCondition = Field(default=ProductCondition.NEW)

    # 이미지
    representative_image: ImageInfo | None = Field(default=None, description="대표 이미지")
    optional_images: list[ImageInfo] = Field(
        default_factory=list, max_length=9, description="추가 이미지 (최대 9장)"
    )

    # 상세 설명
    detail_content: str = Field(default="", description="상품 상세 설명 (HTML)")

    # 옵션
    options: list[ProductOption] = Field(default_factory=list, description="옵션 목록")
    option_combinations: list[OptionCombination] = Field(
        default_factory=list, description="옵션 조합"
    )

    # 배송
    delivery_info: DeliveryInfo = Field(default_factory=DeliveryInfo)

    # 부가 정보
    seller_managed_code: str | None = Field(default=None, description="판매자 관리 코드")
    brand: str | None = Field(default=None, description="브랜드")
    manufacturer: str | None = Field(default=None, description="제조사")
    origin_area: str | None = Field(default=None, description="원산지")
    detail_attributes: list[DetailAttribute] = Field(
        default_factory=list, description="상세 속성"
    )
    seo_info: SeoInfo = Field(default_factory=SeoInfo, description="SEO 정보")

    @field_validator("seller_tags", mode="before", check_fields=False)
    @classmethod
    def _validate_tags(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [t.strip() for t in v.split(",") if t.strip()]
        return v or []


class ProductRow(BaseModel):
    """스프레드시트 1행에 대응하는 원시 데이터."""

    product_name: str = Field(..., description="상품명")
    category_id: str = Field(..., description="카테고리 ID")
    sale_price: int = Field(..., gt=0, description="판매가")
    stock_quantity: int = Field(default=0, ge=0, description="재고 수량")
    detail_content: str = Field(default="", description="상세 설명 (HTML)")

    # 이미지 (로컬 경로 또는 URL, 쉼표 구분)
    representative_image: str = Field(default="", description="대표 이미지")
    optional_images: str = Field(default="", description="추가 이미지 (쉼표 구분)")

    # 옵션 (쉼표 구분 문자열)
    option1_name: str = Field(default="", description="옵션1 이름")
    option1_value: str = Field(default="", description="옵션1 값")
    option2_name: str = Field(default="", description="옵션2 이름")
    option2_value: str = Field(default="", description="옵션2 값")

    # 배송
    delivery_fee_type: str = Field(default="PAID", description="배송비 유형")
    base_delivery_fee: int = Field(default=0, ge=0, description="기본 배송비")
    free_condition_amount: int | None = Field(default=None, description="무료배송 조건 금액")
    return_fee: int = Field(default=0, ge=0, description="반품 배송비")
    exchange_fee: int = Field(default=0, ge=0, description="교환 배송비")

    # 부가
    seller_managed_code: str = Field(default="", description="판매자 관리 코드")
    brand: str = Field(default="", description="브랜드")
    manufacturer: str = Field(default="", description="제조사")
    origin_area: str = Field(default="", description="원산지")
    seller_tags: str = Field(default="", description="태그 (쉼표 구분)")

    product_condition: str = Field(default="NEW", description="상품 상태")
