"""
Razorpay webhook verification + handlers
========================================
WHY: Revenue is only "recovered" when Razorpay says payment.captured —
     not when we merely create a link (avoids fake ₹).

SECURITY:
  - HMAC-SHA256 of raw body with RAZORPAY_WEBHOOK_SECRET
  - timing-safe compare
  - duplicate event_id rejected (idempotency)
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from typing import Any, Callable, Optional


def webhook_secret() -> str:
    return (os.getenv("RAZORPAY_WEBHOOK_SECRET") or "").strip()


def verify_signature(body: bytes, signature: Optional[str]) -> bool:
    """
    Razorpay sends header: X-Razorpay-Signature
    = HMAC_SHA256(webhook_secret, raw_body) as hex digest.
    """
    secret = webhook_secret()
    if not secret:
        # Fail closed if secret not set — safer for hackathon demos once configured
        return False
    if not signature:
        return False
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature.strip())


def parse_payload(body: bytes) -> dict[str, Any]:
    return json.loads(body.decode("utf-8"))


def extract_event_meta(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize fields we care about for recovery."""
    event_type = payload.get("event") or ""
    event_id = payload.get("event_id") or payload.get("id") or ""
    # Some payloads nest under payload.payment.entity
    payment = (
        (payload.get("payload") or {})
        .get("payment", {})
        .get("entity", {})
    )
    notes = payment.get("notes") or {}
    amount_paise = payment.get("amount") or 0
    return {
        "event_type": event_type,
        "razorpay_event_id": str(event_id),
        "payment_id": payment.get("id"),
        "amount_inr": round(float(amount_paise) / 100.0, 2) if amount_paise else 0.0,
        "status": payment.get("status"),
        "method": payment.get("method"),
        "error_code": payment.get("error_code"),
        "error_description": payment.get("error_description"),
        "revene_event_id": notes.get("revene_event_id"),
        "revene_customer_id": notes.get("revene_customer_id"),
        "notes": notes,
    }


def handle_verified_event(
    payload: dict[str, Any],
    *,
    already_seen: Callable[[str], bool],
    mark_seen: Callable[[str, str, str], None],
    on_captured: Callable[[dict[str, Any]], dict[str, Any]],
    on_failed: Callable[[dict[str, Any]], dict[str, Any]],
) -> dict[str, Any]:
    meta = extract_event_meta(payload)
    rid = meta["razorpay_event_id"]
    etype = meta["event_type"]

    if not rid:
        return {"ok": False, "error": "missing_event_id"}

    if already_seen(rid):
        return {"ok": True, "duplicate": True, "event_id": rid, "event": etype}

    mark_seen(rid, etype, json.dumps(payload)[:8000])

    if etype == "payment.captured":
        result = on_captured(meta)
        return {"ok": True, "handled": "payment.captured", "result": result}

    if etype == "payment.failed":
        result = on_failed(meta)
        return {"ok": True, "handled": "payment.failed", "result": result}

    return {"ok": True, "ignored": etype}
