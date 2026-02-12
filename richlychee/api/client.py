"""HTTP 클라이언트 (레이트 리밋 + 재시도)."""

from __future__ import annotations

from typing import Any

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from richlychee.auth.session import AuthSession
from richlychee.config import Settings
from richlychee.utils.logging import get_logger
from richlychee.utils.rate_limiter import TokenBucketRateLimiter

logger = get_logger("api.client")


class NaverCommerceClient:
    """네이버 커머스 API HTTP 클라이언트.

    레이트 리밋 준수, 자동 재시도, 인증 헤더 자동 부여를 담당.
    """

    def __init__(self, settings: Settings, auth_session: AuthSession) -> None:
        self._settings = settings
        self._auth = auth_session
        self._base_url = settings.api.base_url.rstrip("/")
        self._timeout = settings.api.timeout
        self._max_retries = settings.api.max_retries
        self._session = requests.Session()
        self._rate_limiter = TokenBucketRateLimiter(
            rate=settings.rate_limit.requests_per_second,
            burst=settings.rate_limit.burst_max,
        )

    def _url(self, path: str) -> str:
        """전체 URL 조합."""
        if path.startswith("http"):
            return path
        return f"{self._base_url}/{path.lstrip('/')}"

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        """공통 헤더 구성."""
        headers = {
            "Content-Type": "application/json",
            **self._auth.get_auth_header(),
        }
        if extra:
            headers.update(extra)
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        data: Any | None = None,
        files: Any | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: int | None = None,
    ) -> requests.Response:
        """내부 요청 메서드 (레이트 리밋 + 단일 시도)."""
        self._rate_limiter.wait()

        url = self._url(path)
        req_headers = self._headers(headers)

        # 파일 업로드 시 Content-Type 제거 (requests가 자동 설정)
        if files:
            req_headers.pop("Content-Type", None)

        logger.debug("%s %s", method.upper(), url)

        resp = self._session.request(
            method=method,
            url=url,
            json=json,
            data=data,
            files=files,
            params=params,
            headers=req_headers,
            timeout=timeout or self._timeout,
        )

        if resp.status_code == 401:
            logger.warning("401 Unauthorized — 토큰 갱신 후 재시도")
            self._auth.invalidate()
            req_headers.update(self._auth.get_auth_header())
            resp = self._session.request(
                method=method,
                url=url,
                json=json,
                data=data,
                files=files,
                params=params,
                headers=req_headers,
                timeout=timeout or self._timeout,
            )

        return resp

    def request_with_retry(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        data: Any | None = None,
        files: Any | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: int | None = None,
    ) -> requests.Response:
        """재시도가 포함된 요청.

        HTTP 429(Too Many Requests) 및 5xx 에러 시 지수 백오프로 재시도.
        """

        @retry(
            stop=stop_after_attempt(self._max_retries),
            wait=wait_exponential_jitter(
                initial=self._settings.api.retry_backoff_factor,
                max=30,
            ),
            retry=retry_if_exception_type(requests.HTTPError),
            reraise=True,
        )
        def _do_request() -> requests.Response:
            resp = self._request(
                method, path,
                json=json, data=data, files=files,
                params=params, headers=headers, timeout=timeout,
            )

            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 1))
                logger.warning("429 Rate Limited — %d초 후 재시도", retry_after)
                import time
                time.sleep(retry_after)
                resp.raise_for_status()

            if resp.status_code >= 500:
                logger.warning("서버 오류 %d — 재시도", resp.status_code)
                resp.raise_for_status()

            return resp

        return _do_request()

    def get(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request_with_retry("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request_with_retry("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request_with_retry("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request_with_retry("DELETE", path, **kwargs)
