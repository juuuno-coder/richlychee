"""공통 테스트 설정."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest

from richlychee.config import Settings


@pytest.fixture
def sample_settings() -> Settings:
    """테스트용 기본 설정."""
    return Settings(
        naver_client_id="test_client_id",
        naver_client_secret="$2b$10$test_bcrypt_salt_placeholder",
    )


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """테스트용 샘플 DataFrame."""
    return pd.DataFrame([
        {
            "product_name": "테스트 상품 1",
            "category_id": "50000000",
            "sale_price": 15000,
            "stock_quantity": 100,
            "detail_content": "<p>상세 설명입니다</p>",
            "representative_image": "https://example.com/img1.jpg",
            "optional_images": "https://example.com/img2.jpg,https://example.com/img3.jpg",
            "option1_name": "색상",
            "option1_value": "빨강,파랑",
            "option2_name": "사이즈",
            "option2_value": "S,M,L",
            "delivery_fee_type": "PAID",
            "base_delivery_fee": 3000,
            "free_condition_amount": None,
            "return_fee": 3000,
            "exchange_fee": 3000,
            "seller_managed_code": "TEST-001",
            "brand": "테스트브랜드",
            "manufacturer": "테스트제조사",
            "origin_area": "국산",
            "seller_tags": "테스트,샘플",
            "product_condition": "NEW",
        },
        {
            "product_name": "테스트 상품 2",
            "category_id": "50000001",
            "sale_price": 25000,
            "stock_quantity": 50,
            "detail_content": "<p>두번째 상품</p>",
            "representative_image": "https://example.com/img4.jpg",
            "optional_images": "",
            "option1_name": "",
            "option1_value": "",
            "option2_name": "",
            "option2_value": "",
            "delivery_fee_type": "FREE",
            "base_delivery_fee": 0,
            "free_condition_amount": None,
            "return_fee": 3000,
            "exchange_fee": 3000,
            "seller_managed_code": "TEST-002",
            "brand": "",
            "manufacturer": "",
            "origin_area": "중국",
            "seller_tags": "",
            "product_condition": "NEW",
        },
    ])


@pytest.fixture
def tmp_xlsx(sample_dataframe: pd.DataFrame, tmp_path: Path) -> Path:
    """임시 엑셀 파일 생성."""
    file_path = tmp_path / "test_products.xlsx"
    sample_dataframe.to_excel(file_path, index=False, engine="openpyxl")
    return file_path


@pytest.fixture
def tmp_csv(sample_dataframe: pd.DataFrame, tmp_path: Path) -> Path:
    """임시 CSV 파일 생성."""
    file_path = tmp_path / "test_products.csv"
    sample_dataframe.to_csv(file_path, index=False, encoding="utf-8-sig")
    return file_path
