"""인증 모듈 테스트."""

from __future__ import annotations

import base64
import time
from unittest.mock import patch

import pytest
import responses

from richlychee.auth.token import TokenInfo, generate_signature, request_token
from richlychee.auth.session import AuthSession
from richlychee.config import Settings


class TestGenerateSignature:
    """서명 생성 테스트."""

    def test_returns_tuple(self):
        """서명과 타임스탬프 튜플 반환."""
        # bcrypt salt 형식의 테스트 시크릿
        client_secret = "$2b$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy"
        sig, ts = generate_signature("test_id", client_secret)

        assert isinstance(sig, str)
        assert isinstance(ts, int)
        assert len(sig) > 0

    def test_signature_is_base64(self):
        """서명이 유효한 Base64 인코딩인지 확인."""
        client_secret = "$2b$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy"
        sig, _ = generate_signature("test_id", client_secret)

        # Base64 디코딩 가능 확인
        decoded = base64.b64decode(sig)
        assert len(decoded) > 0

    def test_custom_timestamp(self):
        """커스텀 타임스탬프 사용 시 동일 값 반환."""
        client_secret = "$2b$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy"
        ts = 1700000000000
        sig1, ts1 = generate_signature("test_id", client_secret, timestamp=ts)
        sig2, ts2 = generate_signature("test_id", client_secret, timestamp=ts)

        assert ts1 == ts
        assert ts2 == ts
        assert sig1 == sig2


class TestTokenInfo:
    """TokenInfo 테스트."""

    def test_not_expired(self):
        """만료 전 토큰."""
        token = TokenInfo(
            access_token="test_token",
            expires_at=time.time() + 3600,
        )
        assert not token.is_expired

    def test_expired(self):
        """만료된 토큰."""
        token = TokenInfo(
            access_token="test_token",
            expires_at=time.time() - 100,
        )
        assert token.is_expired

    def test_expired_within_margin(self):
        """30초 마진 내의 토큰은 만료 처리."""
        token = TokenInfo(
            access_token="test_token",
            expires_at=time.time() + 10,  # 30초 마진보다 작음
        )
        assert token.is_expired


class TestRequestToken:
    """토큰 발급 테스트."""

    @responses.activate
    def test_successful_token_request(self):
        """정상 토큰 발급."""
        responses.add(
            responses.POST,
            "https://api.commerce.naver.com/external/v1/oauth2/token",
            json={
                "access_token": "test_access_token",
                "expires_in": 3600,
                "token_type": "Bearer",
            },
            status=200,
        )

        client_secret = "$2b$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy"
        token = request_token("test_id", client_secret)

        assert token.access_token == "test_access_token"
        assert token.token_type == "Bearer"
        assert not token.is_expired

    @responses.activate
    def test_failed_token_request(self):
        """토큰 발급 실패."""
        responses.add(
            responses.POST,
            "https://api.commerce.naver.com/external/v1/oauth2/token",
            json={"error": "invalid_client"},
            status=401,
        )

        client_secret = "$2b$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy"

        with pytest.raises(Exception):
            request_token("bad_id", client_secret)


class TestAuthSession:
    """AuthSession 테스트."""

    @responses.activate
    def test_test_connection_success(self, sample_settings):
        """연결 테스트 성공."""
        responses.add(
            responses.POST,
            "https://api.commerce.naver.com/external/v1/oauth2/token",
            json={
                "access_token": "test_token",
                "expires_in": 3600,
                "token_type": "Bearer",
            },
            status=200,
        )

        # bcrypt salt가 유효해야 하므로 mock 사용
        with patch("richlychee.auth.token.generate_signature") as mock_sig:
            mock_sig.return_value = ("mock_signature", 1700000000000)
            session = AuthSession(sample_settings)
            assert session.test_connection() is True

    def test_test_connection_failure(self, sample_settings):
        """연결 테스트 실패 (네트워크 오류)."""
        session = AuthSession(sample_settings)
        # 실제 API 호출 없이 실패
        assert session.test_connection() is False

    def test_invalidate_forces_refresh(self, sample_settings):
        """invalidate 후 토큰이 None."""
        session = AuthSession(sample_settings)
        session.invalidate()
        assert session._token is None
