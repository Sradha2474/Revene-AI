"""
Central configuration — fail-fast in production, permissive in demo.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


def _bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class Settings:
    app_env: str
    port: int
    host: str
    cors_origins: list[str]
    api_key: Optional[str]
    require_api_key: bool
    enable_live_simulator: bool
    razorpay_key_id: str
    razorpay_key_secret: str
    razorpay_webhook_secret: str
    allow_unsigned_webhooks: bool
    log_level: str

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def razorpay_configured(self) -> bool:
        return bool(self.razorpay_key_id and self.razorpay_key_secret)


def load_settings() -> Settings:
    env = (os.getenv("APP_ENV") or os.getenv("FLASK_ENV") or "development").strip().lower()
    if env in ("prod", "production"):
        env = "production"
    else:
        env = "development"

    cors_raw = (os.getenv("CORS_ORIGINS") or "*").strip()
    cors_origins = [o.strip() for o in cors_raw.split(",") if o.strip()]

    settings = Settings(
        app_env=env,
        port=_int("PORT", 5000),
        host=(os.getenv("HOST") or "0.0.0.0").strip(),
        cors_origins=cors_origins,
        api_key=(os.getenv("API_KEY") or "").strip() or None,
        require_api_key=_bool("REQUIRE_API_KEY", default=False),
        enable_live_simulator=_bool("ENABLE_LIVE_SIMULATOR", default=True),
        razorpay_key_id=(os.getenv("RAZORPAY_KEY_ID") or "").strip(),
        razorpay_key_secret=(os.getenv("RAZORPAY_KEY_SECRET") or "").strip(),
        razorpay_webhook_secret=(os.getenv("RAZORPAY_WEBHOOK_SECRET") or "").strip(),
        allow_unsigned_webhooks=_bool("RAZORPAY_WEBHOOK_ALLOW_UNSIGNED", default=False),
        log_level=(os.getenv("LOG_LEVEL") or ("INFO" if env == "production" else "DEBUG")).upper(),
    )
    return settings


def validate_settings(settings: Settings) -> list[str]:
    """
    Returns list of hard errors. Empty = OK to boot.
    Production is stricter; development only warns via caller.
    """
    errors: list[str] = []
    if not settings.is_production:
        return errors

    if not settings.razorpay_configured:
        errors.append("RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET required in production")
    if not settings.razorpay_webhook_secret:
        errors.append("RAZORPAY_WEBHOOK_SECRET required in production")
    if settings.allow_unsigned_webhooks:
        errors.append("RAZORPAY_WEBHOOK_ALLOW_UNSIGNED must be off in production")
    if settings.require_api_key and not settings.api_key:
        errors.append("REQUIRE_API_KEY=1 but API_KEY is empty")
    if settings.cors_origins == ["*"] and settings.require_api_key:
        # not fatal — warn-level left to caller
        pass
    return errors
