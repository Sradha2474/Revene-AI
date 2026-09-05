"""
Recovery pipeline: investigate → policy → (optional) execute
============================================================
Used by APIs; does not require frontend changes.
"""

from __future__ import annotations

import json
from typing import Any, Optional

import db
import investigate_agent
import policy_engine
import action_executor


def run_investigation(
    event: dict,
    risk_scores: dict,
    outage_status: dict,
    bank_check: Optional[dict] = None,
    error_code: Optional[str] = None,
    interventions: int = 0,
    *,
    auto_execute_green_link: bool = False,
) -> dict[str, Any]:
    decision = investigate_agent.investigate(
        event=event,
        risk_scores=risk_scores,
        outage_status=outage_status,
        bank_check=bank_check,
        error_code=error_code,
        interventions=interventions,
    )
    policy = policy_engine.evaluate_policy(decision)
    event_id = event["id"]

    db.save_agent_decision(event_id, decision, policy)
    db.add_audit(
        event_id,
        "agent_decision",
        f"{decision['diagnosis']} → {decision['recommended_action']} "
        f"(p={decision['recovery_probability']:.0%}, EV=₹{decision['expected_recovery_value']})",
    )
    db.add_audit(
        event_id,
        "policy",
        f"{policy['traffic_light']} / {policy['decision']}: {policy['reason']}",
    )
    db.append_audit_chain(
        event_id,
        "agent_policy",
        json.dumps({"decision": decision["recommended_action"], "policy": policy["decision"]}),
    )

    execution = None
    if policy["traffic_light"] == "YELLOW":
        aid = db.enqueue_approval(
            event_id,
            policy.get("approved_action") or decision["recommended_action"],
            policy["reason"],
        )
        db.add_audit(event_id, "approval_queued", f"approval_id={aid}")
        db.update_at_risk_event(event_id, status="awaiting_approval")
        execution = {"queued_approval_id": aid}

    elif policy["traffic_light"] == "RED":
        action = policy.get("approved_action") or "stop"
        if action == "escalate_human":
            db.update_at_risk_event(event_id, status="escalated")
        else:
            db.update_at_risk_event(event_id, status="stopped")
        execution = {"blocked": True, "action": action}

    elif policy["traffic_light"] == "GREEN" and auto_execute_green_link:
        if decision["recommended_action"] == "send_payment_link":
            execution = action_executor.create_recovery_payment_link(event)
        else:
            execution = {"auto": True, "note": "GREEN — executor left to caller/simulator"}

    return {
        "decision": decision,
        "policy": policy,
        "execution": execution,
    }
