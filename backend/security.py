"""
Auth + light rate limiting for production APIs.
Webhook stays on Razorpay HMAC (not API key).
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from functools import wraps
from typing import Callable, Optional

from flask import jsonify, request


class SlidingWindowRateLimiter:
    """In-process limiter — enough for single-node hackathon/prod demo."""

    def __init__(self):
        self._hits: dict[str, deque] = defaultdict(deque)

    def allow(self, key: str, limit: int, window_sec: float) -> bool:
        now = time.monotonic()
        q = self._hits[key]
        while q and now - q[0] > window_sec:
            q.popleft()
        if len(q) >= limit:
            return False
        q.append(now)
        return True


rate_limiter = SlidingWindowRateLimiter()


def client_ip() -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def require_api_key_if_enabled(get_settings: Callable):
    """Decorator: when REQUIRE_API_KEY, demand X-API-Key or Authorization: Bearer."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            settings = get_settings()
            if not settings.require_api_key:
                return fn(*args, **kwargs)
            expected = settings.api_key
            if not expected:
                return jsonify({"error": "server_misconfigured", "detail": "API_KEY missing"}), 500
            provided = request.headers.get("X-API-Key") or ""
            if not provided:
                auth = request.headers.get("Authorization") or ""
                if auth.lower().startswith("bearer "):
                    provided = auth[7:].strip()
            if provided != expected:
                return jsonify({"error": "unauthorized"}), 401
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def rate_limit(limit: int, window_sec: float, *, prefix: str):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            key = f"{prefix}:{client_ip()}"
            if not rate_limiter.allow(key, limit, window_sec):
                return jsonify({"error": "rate_limited", "retry_after_sec": window_sec}), 429
            return fn(*args, **kwargs)

        return wrapper

    return decorator
