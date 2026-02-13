"""파일 라우터."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(prefix="/files", tags=["files"])


@router.get("/template")
async def download_template():
    """샘플 템플릿 다운로드."""
    template_path = Path(__file__).resolve().parent.parent.parent / "templates" / "sample_products.xlsx"
    if not template_path.exists():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="템플릿 파일을 찾을 수 없습니다.")

    return FileResponse(
        path=str(template_path),
        filename="sample_products.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
