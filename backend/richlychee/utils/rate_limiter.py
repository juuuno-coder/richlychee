"""토큰 버킷 레이트 리미터."""

from __future__ import annotations

import threading
import time


class TokenBucketRateLimiter:
    """토큰 버킷 알고리즘 기반 레이트 리미터.

    Args:
        rate: 초당 허용 요청 수.
        burst: 최대 버스트 허용량.
    """

    def __init__(self, rate: float, burst: int | None = None) -> None:
        self.rate = rate
        self.burst = burst or int(rate)
        self._tokens = float(self.burst)
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        """경과 시간에 비례해 토큰 보충."""
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.burst, self._tokens + elapsed * self.rate)
        self._last_refill = now

    def acquire(self, timeout: float | None = None) -> bool:
        """토큰 1개를 소비. 부족하면 대기 후 재시도.

        Args:
            timeout: 최대 대기 시간(초). None이면 무제한 대기.

        Returns:
            토큰 획득 성공 여부.
        """
        deadline = None if timeout is None else time.monotonic() + timeout

        while True:
            with self._lock:
                self._refill()
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return True

                # 토큰 1개 충전에 필요한 대기 시간
                wait = (1.0 - self._tokens) / self.rate

            if deadline is not None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return False
                wait = min(wait, remaining)

            time.sleep(wait)

    def wait(self) -> None:
        """토큰을 획득할 때까지 무제한 대기."""
        self.acquire(timeout=None)
