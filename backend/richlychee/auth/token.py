"""OAuth2 토큰 발급 (bcrypt 서명)."""

from __future__ import annotations

import base64
import time
from dataclasses import dataclass

import bcrypt
import requests

from richlychee.utils.logging import get_logger

logger = get_logger("auth.token")


@dataclass
class TokenInfo:
    """발급된 토큰 정보."""

    access_token: str
    expires_at: float  # epoch seconds
    token_type: str = "Bearer"

    @property
    def is_expired(self) -> bool:
        """토큰 만료 여부 (30초 마진)."""
        return time.time() >= (self.expires_at - 30)


def generate_signature(client_id: str, client_secret: str, timestamp: int | None = None) -> tuple[str, int]:
    """네이버 커머스 API용 bcrypt 서명을 생성.

    Args:
        client_id: 클라이언트 ID.
        client_secret: 클라이언트 시크릿 (bcrypt salt 형식).
        timestamp: epoch 밀리초. None이면 현재 시각 - 3초.

    Returns:
        (client_secret_sign, timestamp) 튜플.
    """
    if timestamp is None:
        timestamp = int((time.time() - 3) * 1000)

    password = f"{client_id}_{timestamp}"
    hashed = bcrypt.hashpw(password.encode("utf-8"), client_secret.encode("utf-8"))
    signature = base64.b64encode(hashed).decode("utf-8")

    return signature, timestamp


def request_token(
    client_id: str,
    client_secret: str,
    token_url: str = "https://api.commerce.naver.com/external/v1/oauth2/token",
    timeout: int = 30,
) -> TokenInfo:
    """OAuth2 Client Credentials 방식으로 액세스 토큰을 발급.

    Args:
        client_id: 클라이언트 ID.
        client_secret: 클라이언트 시크릿.
        token_url: 토큰 발급 URL.
        timeout: HTTP 요청 타임아웃(초).

    Returns:
        TokenInfo 객체.

    Raises:
        requests.HTTPError: 토큰 발급 실패 시.
    """
    signature, timestamp = generate_signature(client_id, client_secret)

    data = {
        "client_id": client_id,
        "timestamp": timestamp,
        "client_secret_sign": signature,
        "grant_type": "client_credentials",
        "type": "SELF",
    }

    logger.debug("토큰 발급 요청: %s", token_url)

    resp = requests.post(
        token_url,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=timeout,
    )
    resp.raise_for_status()

    body = resp.json()
    expires_in = body.get("expires_in", 3600)

    token = TokenInfo(
        access_token=body["access_token"],
        expires_at=time.time() + expires_in,
        token_type=body.get("token_type", "Bearer"),
    )

    logger.info("토큰 발급 성공 (만료: %d초 후)", expires_in)
    return token
