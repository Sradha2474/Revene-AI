"""
Strategy simulator (Phase 5)
============================
What-if on existing at-risk / synthetic probabilities.
No RL — just threshold math.
"""

from __future__ import annotations

from typing import Any, Iterable


def simulate_threshold_strategies(
    cases: Iterable[dict],
    thresholds: list[float] | None = None,
) -> dict[str, Any]:
    """
    cases: each needs amount + recovery_probability (0-1)
    Compare auto-recover when probability > threshold.
    """
    thresholds = thresholds or [0.70, 0.85]
    rows = list(cases)
    strategies = []

    for t in thresholds:
        recovered = 0.0
        retries = 0
        skipped = 0
        for c in rows:
            amt = float(c.get("amount") or 0)
            p = float(c.get("recovery_probability") or c.get("probability") or 0)
            if p > t:
                # expected recovery contribution
                recovered += amt * p
                retries += 1
            else:
                skipped += 1
        # "unnecessary" ≈ retries that would fail in expectation
        unnecessary = 0.0
        for c in rows:
            p = float(c.get("recovery_probability") or c.get("probability") or 0)
            if p > t:
                unnecessary += (1.0 - p)

        strategies.append({
            "name": f"Auto-recover when probability > {t:.0%}",
            "threshold": t,
            "expected_recovery": round(recovered, 2),
            "actions_taken": retries,
            "skipped": skipped,
            "estimated_unnecessary_retries": round(unnecessary, 1),
        })

    return {
        "case_count": len(rows),
        "strategies": strategies,
    }
