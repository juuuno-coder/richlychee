"""인증 세션 래퍼 (자동 토큰 갱신)."""

from __future__ import annotations

import threading

import requests

from richlychee.auth.token import TokenInfo, request_token
from richlychee.config import Settings
from richlychee.utils.logging import get_logger

logger = get_logger("auth.session")


class AuthSession:
    """자동 토큰 갱신 기능이 있는 인증 세션.

    모든 API 호출에서 이 세션을 통해 Authorization 헤더를 자동 부여한다.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._token: TokenInfo | None = None
        self._lock = threading.Lock()

    @property
    def token(self) -> TokenInfo:
        """유효한 토큰을 반환. 만료 시 자동 갱신."""
        with self._lock:
            if self._token is None or self._token.is_expired:
                self._refresh_token()
            assert self._token is not None
            return self._token

    def _refresh_token(self) -> None:
        """토큰을 새로 발급."""
        logger.info("토큰 갱신 중...")
        self._token = request_token(
            client_id=self._settings.naver_client_id,
            client_secret=self._settings.naver_client_secret,
            token_url=self._settings.api.token_url,
            timeout=self._settings.api.timeout,
        )

    def get_auth_header(self) -> dict[str, str]:
        """Authorization 헤더를 반환."""
        t = self.token
        return {"Authorization": f"{t.token_type} {t.access_token}"}

    def test_connection(self) -> bool:
        """인증 테스트. 토큰 발급 성공 여부를 반환."""
        try:
            _ = self.token
            logger.info("인증 테스트 성공")
            return True
        except requests.HTTPError as e:
            logger.error("인증 테스트 실패: %s", e)
            return False
        except Exception as e:
            logger.error("인증 테스트 실패 (예외): %s", e)
            return False

    def invalidate(self) -> None:
        """현재 토큰을 무효화하여 다음 호출 시 갱신 강제."""
        with self._lock:
            self._token = None
