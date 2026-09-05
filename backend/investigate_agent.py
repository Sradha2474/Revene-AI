"""
AI Recovery investigation — structured WHY + WHAT NEXT (Phase 2)
================================================================
Uses deterministic classifier + ML scores + health + fatigue.
No LLM inventing payment facts.
"""

from __future__ import annotations

from typing import Any, Optional

from route_recommender import recommend_route
import failure_classifier
import fatigue as fatigue_mod
import payment_health
import recovery_agent as base_agent


def investigate(
    *,
    event: dict,
    risk_scores: dict,
    outage_status: dict,
    bank_check: Optional[dict] = None,
    error_code: Optional[str] = None,
    interventions: int = 0,
) -> dict[str, Any]:
    """
    Build the structured agent decision JSON.
    """
    bank = event.get("bank") or "UNKNOWN"
    amount = float(event.get("amount") or 0)
    attempts = int(event.get("attempts") or 0)
    stage = event.get("stage") or "failed"
    method = event.get("original_method") or (
        max(risk_scores, key=risk_scores.get) if risk_scores else "upi"
    )
    bank_check = bank_check or {}
    z = float(bank_check.get("z_score") or 0)
    outage = bool(bank_check.get("outage"))

    failure = failure_classifier.classify_failure(
        error_code=error_code,
        root_cause=event.get("root_cause"),
        outage=outage,
    )

    health = payment_health.route_health(
        bank=bank,
        z_score=z,
        outage=outage,
        recent_failure_rate=bank_check.get("recent_failure_rate"),
        baseline_failure_rate=bank_check.get("baseline_failure_rate"),
    )

    fat = fatigue_mod.calculate_fatigue(
        retry_attempts=attempts,
        interventions=interventions,
        recent_failures=attempts,
    )

    ranking = recommend_route(risk_scores, outage_status) if risk_scores else {
        "recommended_method": method,
        "confidence": 0.5,
    }
    best_method = ranking["recommended_method"]
    # recovery probability ≈ success prob of best alternate (or best overall)
    recovery_probability = float(ranking.get("confidence") or risk_scores.get(best_method, 0.5))
    if health["avoid_retry_same_route"] and best_method:
        recovery_probability = min(0.95, recovery_probability + 0.05)

    expected_value = round(amount * recovery_probability, 2)

    # Reuse existing action chooser for recommended_action
    choice = base_agent.choose_action(
        stage,
        event.get("root_cause") or failure["failure_category"].lower(),
        event,
        risk_scores or {method: recovery_probability},
        outage_status or {},
    )

    force_stop = fat["should_stop"] or not failure["recoverable"]
    if force_stop and choice["action"] not in ("stop", "escalate_human"):
        if not failure["known"]:
            choice = {
                "action": "escalate_human",
                "method": best_method,
                "reason": failure["diagnosis"],
                "rule_id": "UNKNOWN_ESCALATE",
            }
        else:
            choice = {
                "action": "stop",
                "method": None,
                "reason": "Fatigue HIGH or non-recoverable",
                "rule_id": "FATIGUE_OR_TERMINAL",
            }

    reason = (
        f"{failure['diagnosis']}. "
        f"Best route now: {best_method} (p={recovery_probability:.0%}). "
        f"Bank {bank} is {health['status']}. Fatigue={fat['fatigue_level']}. "
        f"{choice['reason']}"
    )

    return {
        "event_id": event.get("id"),
        "amount": amount,
        "customer_id": event.get("customer_id"),
        "diagnosis": failure["diagnosis"],
        "recommended_action": choice["action"],
        "recommended_method": choice.get("method") or best_method,
        "recovery_probability": round(recovery_probability, 3),
        "expected_recovery_value": expected_value,
        "confidence": round(min(0.95, 0.55 + recovery_probability * 0.4), 3),
        "reason": reason,
        "retry_count": attempts,
        "force_stop": force_stop,
        "failure": failure,
        "payment_health": health,
        "method_health": payment_health.summarize_methods(
            risk_scores or {}, outage_status or {}
        ),
        "fatigue": fat,
        "rule_id": choice.get("rule_id"),
    }
