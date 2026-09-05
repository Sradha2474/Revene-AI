"""
Deterministic policy engine (Phase 3)
=====================================
AI recommends → policy decides → executor may act.

GREEN  = AUTO EXECUTE
YELLOW = HUMAN APPROVAL
RED    = BLOCK / STOP

LLM never makes this final call.
"""

from __future__ import annotations

import os
from typing import Any


def _f(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return default


def _i(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


def evaluate_policy(decision: dict[str, Any]) -> dict[str, Any]:
    """
    decision: output of investigate_agent.investigate()
    """
    max_retries = _i("POLICY_MAX_RETRIES", 2)
    auto_max_amount = _f("POLICY_AUTO_MAX_AMOUNT", 5000)
    human_amount = _f("POLICY_HUMAN_AMOUNT", 10000)
    min_prob_auto = _f("POLICY_MIN_PROBABILITY_AUTO", 0.80)

    action = decision.get("recommended_action")
    amount = float(decision.get("amount") or 0)
    attempts = int(decision.get("retry_count") or 0)
    prob = float(decision.get("recovery_probability") or 0)
    fatigue = (decision.get("fatigue") or {}).get("fatigue_level", "LOW")
    known = bool((decision.get("failure") or {}).get("known", True))
    recoverable = bool((decision.get("failure") or {}).get("recoverable", True))
    health = decision.get("payment_health") or {}
    avoid = bool(health.get("avoid_retry_same_route"))

    # --- RED ---
    if action in ("stop", "escalate_human") and decision.get("force_stop"):
        return _red("Agent already requested stop/escalate", action)

    if attempts >= max_retries and action not in ("escalate_human", "send_payment_link"):
        return _red(f"Retry count {attempts} >= max {max_retries}", "stop")

    if fatigue == "HIGH":
        return _red("Recovery fatigue HIGH — stop chasing customer", "stop")

    if not known or (decision.get("failure") or {}).get("failure_category") == "UNKNOWN_ERROR":
        return _red("Unknown failure — do not auto-execute", "escalate_human")

    if not recoverable and action in ("smart_retry", "wait_then_switch"):
        return _red("Failure marked non-recoverable for retry", "stop")

    if action in ("smart_retry",) and avoid:
        # Don't blind-retry the sick route — require link/switch (auto if safe)
        return _yellow(
            "Bank/route DEGRADED or OUTAGE — switch via payment link / alternate",
            "send_payment_link",
        )

    if amount < 50 and action not in ("stop",):
        return _red("Amount below chase threshold", "stop")

    # --- YELLOW ---
    if amount >= human_amount:
        return _yellow(f"High-value ₹{amount:.0f} requires human approval", action)

    if amount >= auto_max_amount and prob < 0.9:
        return _yellow(f"Amount ₹{amount:.0f} with mid confidence — approval needed", action)

    if fatigue == "MEDIUM" and action in ("smart_retry", "send_payment_link"):
        return _yellow("Medium fatigue — human should confirm intervention", action)

    if prob < min_prob_auto and action in ("smart_retry", "wait_then_switch", "send_payment_link"):
        if prob < 0.35:
            return _red(f"Recovery probability {prob:.0%} too low", "stop")
        return _yellow(f"Probability {prob:.0%} below auto threshold {min_prob_auto:.0%}", action)

    if action == "escalate_human":
        return _yellow("Escalation requested", action)

    # --- GREEN ---
    if action in (
        "preempt_switch_method",
        "preempt_highlight",
        "smart_retry",
        "wait_then_switch",
        "send_payment_link",
    ):
        if prob >= min_prob_auto or action.startswith("preempt"):
            return _green(f"Safe auto-execute: {action}", action)
        return _yellow("Borderline confidence", action)

    if action == "stop":
        return _red("Stop action", "stop")

    return _yellow(f"Unrecognized action {action} — require approval", action)


def _green(reason: str, action: str) -> dict[str, Any]:
    return {
        "decision": "AUTO_EXECUTE",
        "traffic_light": "GREEN",
        "allowed": True,
        "approved_action": action,
        "reason": reason,
    }


def _yellow(reason: str, action: str) -> dict[str, Any]:
    return {
        "decision": "HUMAN_APPROVAL",
        "traffic_light": "YELLOW",
        "allowed": False,
        "approved_action": action,
        "reason": reason,
    }


def _red(reason: str, action: str) -> dict[str, Any]:
    return {
        "decision": "BLOCK",
        "traffic_light": "RED",
        "allowed": False,
        "approved_action": action,
        "reason": reason,
    }
