"""Password hashing and login rate limiting (F2).

Passwords are bcrypt-hashed and never stored, logged or returned in plaintext -
`HRAccountOut` does not even declare the hash field.
"""
from __future__ import annotations

import threading
import time

from passlib.context import CryptContext

from .config import settings

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto",
                    bcrypt__rounds=settings.bcrypt_rounds)


def hash_password(plain: str) -> str:
    return _pwd.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _pwd.verify(plain, hashed)
    except Exception:
        # A malformed/legacy hash must read as "wrong password", not as a 500.
        return False


def dummy_verify() -> None:
    """Burn roughly one bcrypt round when the username does not exist, so
    "no such user" and "wrong password" take about the same time. Without this,
    response time alone enumerates valid usernames."""
    try:
        _pwd.dummy_verify()
    except Exception:
        pass


class LoginRateLimiter:
    """Per-username failure counter, in memory.

    Deliberately simple: one process, one dict, Phase 1. It resets on restart
    and does not work across replicas - when this moves behind more than one
    worker, swap it for Redis. Keyed on username (not IP) because the attack it
    blocks is password guessing against a known HR account.
    """

    def __init__(self, max_failures: int, window_seconds: int) -> None:
        self.max_failures = max_failures
        self.window_seconds = window_seconds
        self._failures: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def _recent(self, key: str, now: float) -> list[float]:
        cutoff = now - self.window_seconds
        return [t for t in self._failures.get(key, []) if t > cutoff]

    def is_blocked(self, username: str) -> bool:
        key = (username or "").strip().lower()
        now = time.time()
        with self._lock:
            recent = self._recent(key, now)
            self._failures[key] = recent
            return len(recent) >= self.max_failures

    def record_failure(self, username: str) -> None:
        key = (username or "").strip().lower()
        now = time.time()
        with self._lock:
            self._failures[key] = self._recent(key, now) + [now]

    def reset(self, username: str) -> None:
        key = (username or "").strip().lower()
        with self._lock:
            self._failures.pop(key, None)

    def retry_after_seconds(self, username: str) -> int:
        key = (username or "").strip().lower()
        now = time.time()
        with self._lock:
            recent = self._recent(key, now)
        if not recent:
            return 0
        return max(1, int(self.window_seconds - (now - min(recent))))


login_limiter = LoginRateLimiter(
    max_failures=settings.login_max_failures,
    window_seconds=settings.login_failure_window_minutes * 60,
)
