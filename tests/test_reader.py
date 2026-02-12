"""데이터 리더 테스트."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from richlychee.data.reader import read_file


class TestReadFile:
    """파일 읽기 테스트."""

    def test_read_xlsx(self, tmp_xlsx: Path):
        """엑셀 파일 읽기."""
        df = read_file(tmp_xlsx)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "product_name" in df.columns
        assert "sale_price" in df.columns

    def test_read_csv(self, tmp_csv: Path):
        """CSV 파일 읽기."""
        df = read_file(tmp_csv)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "product_name" in df.columns

    def test_file_not_found(self):
        """존재하지 않는 파일."""
        with pytest.raises(FileNotFoundError):
            read_file("nonexistent_file.xlsx")

    def test_unsupported_format(self, tmp_path: Path):
        """지원하지 않는 파일 형식."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("hello")

        with pytest.raises(ValueError, match="지원하지 않는 파일 형식"):
            read_file(txt_file)

    def test_korean_column_normalization(self, tmp_path: Path):
        """한글 컬럼명 정규화."""
        df = pd.DataFrame([{
            "상품명": "테스트",
            "카테고리ID": "50000000",
            "판매가": 10000,
            "재고수량": 10,
        }])
        xlsx_path = tmp_path / "korean.xlsx"
        df.to_excel(xlsx_path, index=False, engine="openpyxl")

        result = read_file(xlsx_path)

        assert "product_name" in result.columns
        assert "category_id" in result.columns
        assert "sale_price" in result.columns
        assert "stock_quantity" in result.columns
        assert result.iloc[0]["product_name"] == "테스트"

    def test_numeric_columns_cleaned(self, tmp_path: Path):
        """숫자 컬럼 결측값이 0으로 치환."""
        df = pd.DataFrame([{
            "product_name": "테스트",
            "category_id": "50000000",
            "sale_price": None,
            "stock_quantity": None,
        }])
        xlsx_path = tmp_path / "nulls.xlsx"
        df.to_excel(xlsx_path, index=False, engine="openpyxl")

        result = read_file(xlsx_path)

        assert result.iloc[0]["sale_price"] == 0
        assert result.iloc[0]["stock_quantity"] == 0
