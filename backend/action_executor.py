"""
Action executor — bridge between agent decision and Razorpay
=============================================================
GREEN path for Phase 1:
  - If action needs a collect link AND Razorpay keys exist → create Payment Link
  - Do NOT mark ₹ recovered until webhook payment.captured
  - If Razorpay not configured → keep old simulator behaviour
"""

from __future__ import annotations

from typing import Any, Optional

import db
import razorpay_client as rzp


def create_recovery_payment_link(event: dict) -> dict[str, Any]:
    """
    Idempotent: if an open link already exists for this case, return it.
    """
    event_id = int(event["id"])
    existing = db.get_open_payment_link_for_event(event_id)
    if existing:
        return {
            "ok": True,
            "duplicate": True,
            "razorpay_link_id": existing.get("razorpay_link_id"),
            "short_url": existing.get("short_url"),
            "amount": existing.get("amount"),
            "status": existing.get("status"),
        }

    if not rzp.is_configured():
        return {"ok": False, "error": "razorpay_not_configured"}

    idem = f"revene-event-{event_id}"
    try:
        created = rzp.create_payment_link(
            amount_inr=float(event["amount"]),
            event_id=event_id,
            customer_id=str(event.get("customer_id") or "cust"),
            description=f"Revene recovery for case #{event_id}",
            idempotency_key=idem,
        )
    except Exception as e:
        return {"ok": False, "error": str(e)}

    db.save_payment_link(
        event_id=event_id,
        razorpay_link_id=created["razorpay_link_id"],
        short_url=created["short_url"],
        amount=float(event["amount"]),
        idempotency_key=idem,
        status=created.get("status") or "created",
    )
    db.add_audit(
        event_id,
        "razorpay_link",
        f"Created Payment Link {created['razorpay_link_id']} → {created['short_url']}",
    )
    db.update_at_risk_event(event_id, status="awaiting_payment")

    return {
        "ok": True,
        "duplicate": False,
        "razorpay_link_id": created["razorpay_link_id"],
        "short_url": created["short_url"],
        "amount": float(event["amount"]),
        "status": created.get("status"),
    }


def apply_captured_payment(meta: dict) -> dict[str, Any]:
    """Mark case recovered only after verified payment.captured webhook."""
    raw_eid = meta.get("revene_event_id")
    event_id = db.find_event_id_by_payment_notes(str(raw_eid) if raw_eid else "")
    amount = float(meta.get("amount_inr") or 0)

    if not event_id:
        return {"ok": False, "error": "unknown_revene_event", "meta": meta}

    event = db.get_at_risk_event(event_id)
    if not event:
        return {"ok": False, "error": "event_missing", "event_id": event_id}

    if event.get("status") == "recovered":
        return {"ok": True, "duplicate_capture": True, "event_id": event_id}

    recovered = amount or float(event["amount"])
    db.update_at_risk_event(
        event_id,
        status="recovered",
        amount_recovered=recovered,
    )
    db.mark_payment_link_paid(
        event_id=event_id,
        razorpay_payment_id=meta.get("payment_id"),
    )
    db.save_recovery_action(
        event_id,
        "razorpay_captured",
        meta.get("method"),
        True,
        recovered,
        f"Razorpay payment.captured {meta.get('payment_id')}",
    )
    db.add_audit(
        event_id,
        "outcome",
        f"RAZORPAY CAPTURED ₹{recovered} payment_id={meta.get('payment_id')}",
    )
    return {"ok": True, "event_id": event_id, "amount_recovered": recovered}


def apply_failed_payment(meta: dict) -> dict[str, Any]:
    """Optional: log failure webhook against an existing recovery case."""
    raw_eid = meta.get("revene_event_id")
    event_id = db.find_event_id_by_payment_notes(str(raw_eid) if raw_eid else "")
    if not event_id:
        # Could create a new at-risk from raw gateway failure later (Phase 2+)
        return {"ok": True, "ignored": "no_matching_case"}

    db.add_audit(
        event_id,
        "razorpay_failed",
        f"payment.failed code={meta.get('error_code')} {meta.get('error_description')}",
    )
    return {"ok": True, "event_id": event_id}
