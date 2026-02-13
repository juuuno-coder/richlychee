"""엑셀/CSV 파일 읽기."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from richlychee.utils.logging import get_logger

logger = get_logger("data.reader")

# 스프레드시트 컬럼 → 내부 필드명 매핑
_COLUMN_MAP: dict[str, str] = {
    "상품명": "product_name",
    "카테고리ID": "category_id",
    "카테고리": "category_id",
    "판매가": "sale_price",
    "재고수량": "stock_quantity",
    "재고": "stock_quantity",
    "상세설명": "detail_content",
    "대표이미지": "representative_image",
    "추가이미지": "optional_images",
    "옵션1이름": "option1_name",
    "옵션1값": "option1_value",
    "옵션2이름": "option2_name",
    "옵션2값": "option2_value",
    "배송비유형": "delivery_fee_type",
    "기본배송비": "base_delivery_fee",
    "무료배송조건금액": "free_condition_amount",
    "반품배송비": "return_fee",
    "교환배송비": "exchange_fee",
    "판매자관리코드": "seller_managed_code",
    "브랜드": "brand",
    "제조사": "manufacturer",
    "원산지": "origin_area",
    "태그": "seller_tags",
    "상품상태": "product_condition",
}


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """컬럼명을 내부 필드명으로 정규화."""
    # 공백 제거
    df.columns = df.columns.str.strip()

    # 한글 매핑 적용
    rename = {}
    for col in df.columns:
        if col in _COLUMN_MAP:
            rename[col] = _COLUMN_MAP[col]
        else:
            # snake_case로 이미 되어있으면 그대로
            rename[col] = col.lower().replace(" ", "_")

    df = df.rename(columns=rename)
    return df


def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """결측값 처리 및 타입 변환."""
    # 문자열이어야 하는 컬럼을 강제 변환 (엑셀에서 숫자로 읽히는 경우 대비)
    str_force_cols = ["category_id", "seller_managed_code"]
    for col in str_force_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).replace("nan", "")

    # 문자열 컬럼의 NaN을 빈 문자열로 치환
    str_cols = df.select_dtypes(include=["object", "string"]).columns
    df[str_cols] = df[str_cols].fillna("")

    # 숫자 컬럼의 NaN을 0으로 치환
    num_cols = ["sale_price", "stock_quantity", "base_delivery_fee", "return_fee", "exchange_fee"]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # free_condition_amount는 None 허용
    if "free_condition_amount" in df.columns:
        df["free_condition_amount"] = pd.to_numeric(
            df["free_condition_amount"], errors="coerce"
        )
        df["free_condition_amount"] = df["free_condition_amount"].where(
            df["free_condition_amount"].notna(), other=None
        )

    return df


def read_file(path: str | Path) -> pd.DataFrame:
    """엑셀(.xlsx) 또는 CSV 파일을 읽어 정규화된 DataFrame 반환.

    Args:
        path: 입력 파일 경로.

    Returns:
        정규화된 DataFrame.

    Raises:
        FileNotFoundError: 파일이 존재하지 않을 때.
        ValueError: 지원하지 않는 파일 형식일 때.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {path}")

    ext = path.suffix.lower()

    if ext == ".xlsx":
        logger.info("엑셀 파일 읽기: %s", path.name)
        df = pd.read_excel(path, engine="openpyxl")
    elif ext == ".csv":
        logger.info("CSV 파일 읽기: %s", path.name)
        df = pd.read_csv(path, encoding="utf-8-sig")
    else:
        raise ValueError(f"지원하지 않는 파일 형식: {ext} (.xlsx 또는 .csv만 지원)")

    logger.info("총 %d행 읽음", len(df))

    df = _normalize_columns(df)
    df = _clean_dataframe(df)

    return df
