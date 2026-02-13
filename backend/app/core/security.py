"""JWT 인증 + 비밀번호 해싱 + AES-256 암호화."""

from __future__ import annotations

import base64
import hashlib
import os
from datetime import UTC, datetime, timedelta

import jwt
from passlib.context import CryptContext

from app.core.config import get_app_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── 비밀번호 ──────────────────────────────────────────────
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── JWT ───────────────────────────────────────────────────
def create_access_token(subject: str, extra: dict | None = None) -> str:
    settings = get_app_settings()
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject, "exp": expire, "type": "access"}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(subject: str) -> str:
    settings = get_app_settings()
    expire = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    payload = {"sub": subject, "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict:
    settings = get_app_settings()
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])


# ── AES-256 (네이버 API Secret 암호화) ────────────────────
def _get_aes_key() -> bytes:
    """encryption_key를 SHA-256 해싱하여 32바이트 키 생성."""
    settings = get_app_settings()
    return hashlib.sha256(settings.encryption_key.encode()).digest()


def encrypt_secret(plaintext: str) -> str:
    """AES-256-CBC 암호화 → base64 문자열."""
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives.padding import PKCS7

    key = _get_aes_key()
    iv = os.urandom(16)
    padder = PKCS7(128).padder()
    padded = padder.update(plaintext.encode()) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    ct = cipher.encryptor().update(padded) + cipher.encryptor().finalize()
    return base64.b64encode(iv + ct).decode()


def decrypt_secret(ciphertext: str) -> str:
    """base64 → AES-256-CBC 복호화."""
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives.padding import PKCS7

    key = _get_aes_key()
    raw = base64.b64decode(ciphertext)
    iv, ct = raw[:16], raw[16:]
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    padded = decryptor.update(ct) + decryptor.finalize()
    unpadder = PKCS7(128).unpadder()
    return (unpadder.update(padded) + unpadder.finalize()).decode()
