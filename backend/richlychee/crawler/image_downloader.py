"""이미지 다운로드 및 업로드 모듈."""

from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

import aiofiles
import httpx

from richlychee.utils.logging import get_logger

if TYPE_CHECKING:
    from richlychee.api.client import NaverCommerceClient

logger = get_logger("crawler.image_downloader")


async def download_image(url: str, save_path: Path) -> Path:
    """
    단일 이미지 다운로드.

    Args:
        url: 이미지 URL
        save_path: 저장할 로컬 경로

    Returns:
        저장된 파일 경로

    Raises:
        httpx.HTTPError: 다운로드 실패 시
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()

        # 디렉토리 생성
        save_path.parent.mkdir(parents=True, exist_ok=True)

        # 비동기 파일 쓰기
        async with aiofiles.open(save_path, "wb") as f:
            await f.write(resp.content)

    logger.debug("이미지 다운로드 완료: %s → %s", url, save_path.name)
    return save_path


async def download_images_batch(
    image_urls: list[str],
    temp_dir: Path,
) -> dict[str, Path]:
    """
    여러 이미지를 병렬로 다운로드.

    Args:
        image_urls: 이미지 URL 리스트
        temp_dir: 임시 저장 디렉토리

    Returns:
        {원본 URL: 로컬 경로} 매핑
    """
    download_map: dict[str, Path] = {}
    tasks = []

    for idx, url in enumerate(image_urls):
        # URL 해시로 고유 파일명 생성
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        ext = _extract_extension(url) or ".jpg"
        filename = f"image_{idx}_{url_hash}{ext}"
        save_path = temp_dir / filename

        tasks.append(_download_with_error_handling(url, save_path))

    # 병렬 다운로드
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for url, result in zip(image_urls, results):
        if isinstance(result, Path):
            download_map[url] = result
        elif isinstance(result, Exception):
            logger.warning("이미지 다운로드 실패 %s: %s", url, result)

    logger.info("이미지 다운로드 완료: %d/%d", len(download_map), len(image_urls))
    return download_map


async def _download_with_error_handling(url: str, save_path: Path) -> Path | Exception:
    """에러 처리가 포함된 다운로드."""
    try:
        return await download_image(url, save_path)
    except Exception as e:
        return e


async def download_and_upload_images(
    client: NaverCommerceClient,
    image_urls: list[str],
    temp_dir: Path,
) -> list[str]:
    """
    외부 이미지 URL → 로컬 다운로드 → 네이버 CDN 업로드.

    Args:
        client: Naver Commerce API 클라이언트
        image_urls: 외부 이미지 URL 리스트
        temp_dir: 임시 저장 디렉토리

    Returns:
        업로드된 CDN URL 리스트 (실패한 이미지는 제외)
    """
    from richlychee.api.images import upload_image

    # 1. 병렬 다운로드
    download_map = await download_images_batch(image_urls, temp_dir)

    # 2. 순차 업로드 (upload_image는 동기 함수)
    uploaded_urls = []
    for original_url, local_path in download_map.items():
        try:
            # 동기 함수를 이벤트 루프에서 실행
            cdn_url = await asyncio.to_thread(upload_image, client, local_path)
            uploaded_urls.append(cdn_url)
            logger.info("이미지 업로드 성공: %s → %s", original_url, cdn_url)
        except Exception as e:
            logger.error("이미지 업로드 실패 %s: %s", original_url, e)

        finally:
            # 임시 파일 삭제
            try:
                local_path.unlink(missing_ok=True)
            except Exception:
                pass

    logger.info("CDN 업로드 완료: %d/%d", len(uploaded_urls), len(image_urls))
    return uploaded_urls


def _extract_extension(url: str) -> str | None:
    """URL에서 파일 확장자 추출."""
    from urllib.parse import urlparse

    path = urlparse(url).path
    ext = Path(path).suffix.lower()

    # 유효한 이미지 확장자만 반환
    valid_exts = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
    return ext if ext in valid_exts else None
