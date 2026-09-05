"""
Deterministic failure classifier (Phase 2)
==========================================
Maps Razorpay / gateway error codes → category.
LLM must NEVER invent these — only reason over them.
"""

from __future__ import annotations

from typing import Any, Optional

# code → (category, side, recoverable_hint)
FAILURE_MAP = {
    "INSUFFICIENT_FUNDS": ("INSUFFICIENT_FUNDS", "customer", True),
    "BAD_REQUEST_ERROR": ("UNKNOWN_ERROR", "unknown", False),
    "CARD_EXPIRED": ("CARD_EXPIRED", "payment_method", False),
    "AUTHENTICATION_FAILED": ("AUTHENTICATION_FAILED", "authentication", True),
    "AUTHENTICATION_FAILED_ERROR": ("AUTHENTICATION_FAILED", "authentication", True),
    "NETWORK_ERROR": ("NETWORK_ERROR", "technical", True),
    "GATEWAY_ERROR": ("NETWORK_ERROR", "technical", True),
    "SERVER_ERROR": ("NETWORK_ERROR", "technical", True),
    "BANK_DECLINED": ("BANK_DECLINED", "bank", True),
    "PAYMENT_DECLINED": ("BANK_DECLINED", "bank", True),
    "ISSUER_DECLINED": ("BANK_DECLINED", "bank", True),
    "LIMIT_EXCEEDED": ("LIMIT_EXCEEDED", "payment_limitation", True),
    "TRANSACTION_LIMIT_EXCEEDED": ("LIMIT_EXCEEDED", "payment_limitation", True),
    "DO_NOT_HONOR": ("BANK_DECLINED", "bank", True),
    "INVALID_CARD_NUMBER": ("CARD_EXPIRED", "payment_method", False),
    "CARD_DECLINED": ("BANK_DECLINED", "bank", True),
}

# Our internal root_cause labels → failure category
ROOT_CAUSE_MAP = {
    "bank_outage": ("BANK_DECLINED", "bank", True),
    "bank_degrading": ("NETWORK_ERROR", "technical", True),
    "wrong_method": ("PAYMENT_DECLINED", "payment_method", True),
    "wrong_method_risk": ("PAYMENT_DECLINED", "payment_method", True),
    "soft_decline": ("BANK_DECLINED", "bank", True),
    "soft_decline_risk": ("BANK_DECLINED", "bank", True),
    "hard_decline": ("INSUFFICIENT_FUNDS", "customer", True),
}


def classify_failure(
    *,
    error_code: Optional[str] = None,
    root_cause: Optional[str] = None,
    outage: bool = False,
) -> dict[str, Any]:
    """
    Returns structured failure intelligence.
    If unknown → explicitly says cannot determine exact cause.
    """
    code = (error_code or "").strip().upper() or None

    if outage:
        return {
            "failure_code": code or "BANK_OUTAGE",
            "failure_category": "BANK_DECLINED",
            "side": "bank",
            "recoverable": True,
            "known": True,
            "diagnosis": "Bank-side temporary failure / outage",
        }

    if code and code in FAILURE_MAP:
        cat, side, rec = FAILURE_MAP[code]
        return {
            "failure_code": code,
            "failure_category": cat,
            "side": side,
            "recoverable": rec,
            "known": True,
            "diagnosis": _diagnosis_text(cat, side),
        }

    if root_cause and root_cause in ROOT_CAUSE_MAP:
        cat, side, rec = ROOT_CAUSE_MAP[root_cause]
        return {
            "failure_code": code or root_cause.upper(),
            "failure_category": cat,
            "side": side,
            "recoverable": rec,
            "known": True,
            "diagnosis": _diagnosis_text(cat, side),
        }

    return {
        "failure_code": code or "UNKNOWN_ERROR",
        "failure_category": "UNKNOWN_ERROR",
        "side": "unknown",
        "recoverable": False,
        "known": False,
        "diagnosis": "Cannot determine the exact cause — needs human review",
    }


def _diagnosis_text(category: str, side: str) -> str:
    labels = {
        "INSUFFICIENT_FUNDS": "Customer-side funds / balance issue",
        "CARD_EXPIRED": "Payment-method issue (expired or invalid card)",
        "AUTHENTICATION_FAILED": "Authentication issue (OTP / 3DS drop-off)",
        "NETWORK_ERROR": "Temporary technical / network issue",
        "BANK_DECLINED": "Bank-side decline or instability",
        "LIMIT_EXCEEDED": "Payment limitation (limit exceeded)",
        "PAYMENT_DECLINED": "Payment method decline — alternate method may work",
        "UNKNOWN_ERROR": "Unknown failure",
    }
    base = labels.get(category, category)
    return f"{base} ({side}-side)"
