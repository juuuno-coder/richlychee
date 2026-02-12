"""이미지 업로드 API."""

from __future__ import annotations

from pathlib import Path

from richlychee.api.client import NaverCommerceClient
from richlychee.utils.logging import get_logger

logger = get_logger("api.images")


def upload_image(client: NaverCommerceClient, image_path: str | Path) -> str:
    """로컬 이미지를 네이버 CDN에 업로드하고 URL을 반환.

    Args:
        client: HTTP 클라이언트.
        image_path: 로컬 이미지 파일 경로.

    Returns:
        업로드된 이미지의 CDN URL.

    Raises:
        FileNotFoundError: 이미지 파일이 존재하지 않을 때.
        requests.HTTPError: 업로드 실패 시.
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {path}")

    logger.debug("이미지 업로드: %s", path.name)

    with open(path, "rb") as f:
        resp = client.post(
            "product-images/upload",
            files={"imageFiles": (path.name, f, _guess_content_type(path))},
            timeout=client._settings.registration.image_upload_timeout,
        )

    resp.raise_for_status()

    result = resp.json()
    # API 응답에서 이미지 URL 추출
    images = result.get("images", [])
    if not images:
        raise ValueError(f"이미지 업로드 응답에 URL이 없습니다: {result}")

    url = images[0].get("url", "")
    logger.info("이미지 업로드 완료: %s → %s", path.name, url)

    return url


def upload_images_batch(
    client: NaverCommerceClient,
    image_paths: list[str],
) -> dict[str, str]:
    """여러 이미지를 업로드하고 로컬 경로 → CDN URL 매핑을 반환.

    Args:
        client: HTTP 클라이언트.
        image_paths: 로컬 이미지 파일 경로 리스트.

    Returns:
        {로컬경로: CDN URL} 매핑.
    """
    url_map: dict[str, str] = {}

    for img_path in image_paths:
        try:
            url = upload_image(client, img_path)
            url_map[img_path] = url
        except Exception as e:
            logger.error("이미지 업로드 실패: %s — %s", img_path, e)

    logger.info("이미지 업로드 완료: %d/%d", len(url_map), len(image_paths))
    return url_map


def _guess_content_type(path: Path) -> str:
    """파일 확장자로 Content-Type 추정."""
    ext = path.suffix.lower()
    types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
    }
    return types.get(ext, "application/octet-stream")
