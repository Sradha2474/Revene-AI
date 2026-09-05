"""
Razorpay Test Mode client
=========================
WHY: Judges want real test-mode money actions, not only a simulator.

WHAT: Create Payment Links via Razorpay API using keys from .env.
      If keys are missing, is_configured() is False and the app
      falls back to the existing simulator (nothing breaks).

Amount: Razorpay expects paise (₹100.50 → 10050).
"""

from __future__ import annotations

import os
from typing import Any, Optional

import razorpay


def _keys() -> tuple[str, str]:
    key_id = (os.getenv("RAZORPAY_KEY_ID") or "").strip()
    key_secret = (os.getenv("RAZORPAY_KEY_SECRET") or "").strip()
    return key_id, key_secret


def is_configured() -> bool:
    key_id, key_secret = _keys()
    return bool(key_id.startswith("rzp_") and key_secret)


def get_client() -> razorpay.Client:
    key_id, key_secret = _keys()
    if not key_id or not key_secret:
        raise RuntimeError("Razorpay keys missing. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in .env")
    return razorpay.Client(auth=(key_id, key_secret))


def create_payment_link(
    *,
    amount_inr: float,
    event_id: int,
    customer_id: str,
    description: str = "Revene recovery payment",
    idempotency_key: Optional[str] = None,
) -> dict[str, Any]:
    """
    Create a Razorpay Payment Link (Test Mode works the same API).

    notes.revene_event_id lets the webhook map payment.captured → our case.
    """
    client = get_client()
    amount_paise = int(round(float(amount_inr) * 100))
    if amount_paise < 100:
        raise ValueError("Amount must be at least ₹1.00 for Razorpay Payment Links")

    payload = {
        "amount": amount_paise,
        "currency": "INR",
        "accept_partial": False,
        "description": description[:255],
        "customer": {
            "name": customer_id[:50] or "Revene Customer",
        },
        "notify": {"sms": False, "email": False},
        "reminder_enable": False,
        "notes": {
            "revene_event_id": str(event_id),
            "revene_customer_id": str(customer_id)[:40],
            "source": "revene_recovery",
        },
    }

    headers = {}
    if idempotency_key:
        headers["X-Razorpay-Idempotency-Key"] = idempotency_key[:64]

    # Official SDK: payment_link.create
    link = client.payment_link.create(payload)
    return {
        "razorpay_link_id": link.get("id"),
        "short_url": link.get("short_url"),
        "amount": amount_inr,
        "status": link.get("status", "created"),
        "raw": link,
    }
