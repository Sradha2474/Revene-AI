"""
Payment / bank health (Phase 4)
===============================
Wraps outage monitor signals into HEALTHY / DEGRADED / OUTAGE.
"""

from __future__ import annotations

from typing import Any, Optional


def route_health(
    *,
    bank: str,
    z_score: float = 0.0,
    outage: bool = False,
    recent_failure_rate: Optional[float] = None,
    baseline_failure_rate: Optional[float] = None,
) -> dict[str, Any]:
    if outage or z_score >= 2.5:
        status = "OUTAGE"
    elif z_score >= 1.8 or (
        recent_failure_rate is not None
        and baseline_failure_rate is not None
        and recent_failure_rate >= max(0.15, (baseline_failure_rate or 0.05) * 3)
    ):
        status = "DEGRADED"
    else:
        status = "HEALTHY"

    return {
        "bank": bank,
        "z_score": round(float(z_score or 0), 2),
        "recent_failure_rate": recent_failure_rate,
        "baseline_failure_rate": baseline_failure_rate,
        "status": status,
        "avoid_retry_same_route": status in ("DEGRADED", "OUTAGE"),
    }


def summarize_methods(risk_scores: dict, outage_status: dict) -> list[dict[str, Any]]:
    rows = []
    for method, p in sorted(risk_scores.items(), key=lambda x: -x[1]):
        st = outage_status.get(method, {})
        rows.append({
            "method": method,
            "success_probability": round(float(p), 3),
            "bank": st.get("bank"),
            "outage": bool(st.get("outage")),
            "z_score": st.get("z_score", 0),
            "status": "OUTAGE" if st.get("outage") else (
                "DEGRADED" if float(st.get("z_score") or 0) >= 1.8 else "HEALTHY"
            ),
        })
    return rows
