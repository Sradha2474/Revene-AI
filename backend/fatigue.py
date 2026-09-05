"""
Recovery fatigue scorer (Phase 4)
=================================
Deterministic — not a behavioral ML model.
HIGH fatigue → stop chasing the customer.
"""

from __future__ import annotations

from typing import Any


def calculate_fatigue(
    *,
    retry_attempts: int = 0,
    interventions: int = 0,
    recent_failures: int = 0,
) -> dict[str, Any]:
    """
    Score 0–100 → LOW / MEDIUM / HIGH.
    """
    score = (
        int(retry_attempts) * 25
        + int(interventions) * 20
        + int(recent_failures) * 15
    )
    score = min(100, score)

    if score >= 70 or retry_attempts >= 3:
        level = "HIGH"
    elif score >= 40 or retry_attempts >= 2:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {
        "retry_attempts": int(retry_attempts),
        "interventions": int(interventions),
        "recent_failures": int(recent_failures),
        "fatigue_score": score,
        "fatigue_level": level,
        "should_stop": level == "HIGH",
    }
