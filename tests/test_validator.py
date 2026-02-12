"""검증기 테스트."""

from __future__ import annotations

import pandas as pd
import pytest

from richlychee.data.validator import validate_dataframe


class TestValidateDataframe:
    """DataFrame 검증 테스트."""

    def test_valid_data(self, sample_dataframe: pd.DataFrame):
        """유효한 데이터."""
        result = validate_dataframe(sample_dataframe)
        assert result.is_valid

    def test_empty_dataframe(self):
        """빈 DataFrame."""
        df = pd.DataFrame()
        result = validate_dataframe(df)

        assert not result.is_valid
        assert result.total_errors == 1

    def test_missing_product_name(self):
        """상품명 누락."""
        df = pd.DataFrame([{
            "product_name": "",
            "category_id": "50000000",
            "sale_price": 10000,
        }])
        result = validate_dataframe(df)

        assert not result.is_valid
        errors = [e for e in result.errors if e.field == "product_name"]
        assert len(errors) > 0

    def test_missing_category(self):
        """카테고리 누락."""
        df = pd.DataFrame([{
            "product_name": "테스트",
            "category_id": "",
            "sale_price": 10000,
        }])
        result = validate_dataframe(df)
        assert not result.is_valid

    def test_zero_price(self):
        """판매가 0."""
        df = pd.DataFrame([{
            "product_name": "테스트",
            "category_id": "50000000",
            "sale_price": 0,
        }])
        result = validate_dataframe(df)
        assert not result.is_valid

    def test_negative_stock(self):
        """음수 재고."""
        df = pd.DataFrame([{
            "product_name": "테스트",
            "category_id": "50000000",
            "sale_price": 10000,
            "stock_quantity": -1,
        }])
        result = validate_dataframe(df)
        assert not result.is_valid

    def test_too_many_optional_images(self):
        """추가 이미지 초과."""
        images = ",".join(f"https://example.com/img{i}.jpg" for i in range(10))
        df = pd.DataFrame([{
            "product_name": "테스트",
            "category_id": "50000000",
            "sale_price": 10000,
            "optional_images": images,
        }])
        result = validate_dataframe(df)
        assert not result.is_valid

    def test_invalid_delivery_fee_type(self):
        """잘못된 배송비 유형."""
        df = pd.DataFrame([{
            "product_name": "테스트",
            "category_id": "50000000",
            "sale_price": 10000,
            "delivery_fee_type": "INVALID",
        }])
        result = validate_dataframe(df)
        assert not result.is_valid

    def test_conditional_free_without_amount(self):
        """조건부 무료배송에 금액 누락."""
        df = pd.DataFrame([{
            "product_name": "테스트",
            "category_id": "50000000",
            "sale_price": 10000,
            "delivery_fee_type": "CONDITIONAL_FREE",
            "free_condition_amount": None,
        }])
        result = validate_dataframe(df)
        assert not result.is_valid

    def test_product_name_too_long(self):
        """상품명 100자 초과."""
        df = pd.DataFrame([{
            "product_name": "가" * 101,
            "category_id": "50000000",
            "sale_price": 10000,
        }])
        result = validate_dataframe(df)
        assert not result.is_valid

    def test_invalid_product_condition(self):
        """잘못된 상품 상태."""
        df = pd.DataFrame([{
            "product_name": "테스트",
            "category_id": "50000000",
            "sale_price": 10000,
            "product_condition": "BROKEN",
        }])
        result = validate_dataframe(df)
        assert not result.is_valid

    def test_warnings_for_missing_local_images(self, tmp_path):
        """존재하지 않는 로컬 이미지에 대한 경고."""
        df = pd.DataFrame([{
            "product_name": "테스트",
            "category_id": "50000000",
            "sale_price": 10000,
            "representative_image": "nonexistent/image.jpg",
        }])
        result = validate_dataframe(df)

        # 경고이므로 검증은 통과
        assert result.is_valid
        assert result.total_warnings > 0

    def test_price_too_high(self):
        """판매가 초과."""
        df = pd.DataFrame([{
            "product_name": "테스트",
            "category_id": "50000000",
            "sale_price": 9_999_999_999,
        }])
        result = validate_dataframe(df)
        assert not result.is_valid
