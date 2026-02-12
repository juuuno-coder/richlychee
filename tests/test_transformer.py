"""변환기 테스트."""

from __future__ import annotations

import pandas as pd
import pytest

from richlychee.data.models import ProductRow
from richlychee.data.transformer import (
    collect_local_images,
    product_row_to_payload,
    row_to_product_row,
    transform_dataframe,
)


class TestRowToProductRow:
    """행 → ProductRow 변환 테스트."""

    def test_basic_conversion(self, sample_dataframe: pd.DataFrame):
        """기본 변환."""
        row = sample_dataframe.iloc[0]
        product_row = row_to_product_row(row)

        assert isinstance(product_row, ProductRow)
        assert product_row.product_name == "테스트 상품 1"
        assert product_row.sale_price == 15000
        assert product_row.category_id == "50000000"

    def test_empty_optional_fields(self, sample_dataframe: pd.DataFrame):
        """선택 필드가 비어있는 행."""
        row = sample_dataframe.iloc[1]
        product_row = row_to_product_row(row)

        assert product_row.option1_name == ""
        assert product_row.option1_value == ""


class TestProductRowToPayload:
    """ProductRow → ProductPayload 변환 테스트."""

    def test_basic_payload(self):
        """기본 페이로드 생성."""
        row = ProductRow(
            product_name="테스트 상품",
            category_id="50000000",
            sale_price=10000,
            stock_quantity=50,
        )
        payload = product_row_to_payload(row)

        assert payload.name == "테스트 상품"
        assert payload.sale_price == 10000
        assert payload.stock_quantity == 50
        assert len(payload.options) == 0

    def test_with_single_option(self):
        """단일 옵션 있는 페이로드."""
        row = ProductRow(
            product_name="옵션 상품",
            category_id="50000000",
            sale_price=15000,
            stock_quantity=100,
            option1_name="색상",
            option1_value="빨강,파랑,초록",
        )
        payload = product_row_to_payload(row)

        assert len(payload.options) == 1
        assert payload.options[0].name == "색상"
        assert len(payload.options[0].values) == 3
        assert len(payload.option_combinations) == 3

    def test_with_two_options(self):
        """두 옵션 조합 페이로드."""
        row = ProductRow(
            product_name="조합 상품",
            category_id="50000000",
            sale_price=20000,
            stock_quantity=50,
            option1_name="색상",
            option1_value="빨강,파랑",
            option2_name="사이즈",
            option2_value="S,M,L",
        )
        payload = product_row_to_payload(row)

        assert len(payload.options) == 2
        # 2 * 3 = 6 조합
        assert len(payload.option_combinations) == 6

    def test_image_url_mapping(self):
        """이미지 URL 매핑 적용."""
        row = ProductRow(
            product_name="이미지 상품",
            category_id="50000000",
            sale_price=10000,
            representative_image="local/img.jpg",
        )
        url_map = {"local/img.jpg": "https://cdn.example.com/uploaded.jpg"}
        payload = product_row_to_payload(row, image_url_map=url_map)

        assert payload.representative_image is not None
        assert payload.representative_image.url == "https://cdn.example.com/uploaded.jpg"

    def test_delivery_info(self):
        """배송 정보 변환."""
        row = ProductRow(
            product_name="배송 상품",
            category_id="50000000",
            sale_price=10000,
            delivery_fee_type="FREE",
            base_delivery_fee=0,
        )
        payload = product_row_to_payload(row)

        assert payload.delivery_info.delivery_fee_type.value == "FREE"
        assert payload.delivery_info.base_fee == 0


class TestTransformDataframe:
    """DataFrame 전체 변환 테스트."""

    def test_transform_all_rows(self, sample_dataframe: pd.DataFrame):
        """전체 행 변환."""
        payloads = transform_dataframe(sample_dataframe)

        assert len(payloads) == 2
        assert payloads[0].name == "테스트 상품 1"
        assert payloads[1].name == "테스트 상품 2"

    def test_empty_dataframe(self):
        """빈 DataFrame."""
        df = pd.DataFrame()
        payloads = transform_dataframe(df)
        assert len(payloads) == 0


class TestCollectLocalImages:
    """로컬 이미지 수집 테스트."""

    def test_collect_urls_ignored(self):
        """URL은 수집하지 않음."""
        df = pd.DataFrame([{
            "representative_image": "https://example.com/img.jpg",
            "optional_images": "https://example.com/img2.jpg",
        }])
        images = collect_local_images(df)
        assert len(images) == 0

    def test_collect_local_paths(self):
        """로컬 경로 수집."""
        df = pd.DataFrame([{
            "representative_image": "images/product1.jpg",
            "optional_images": "images/opt1.png,images/opt2.jpg",
        }])
        images = collect_local_images(df)
        assert len(images) == 3
