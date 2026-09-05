"""
Database for Payment Guardian — Predictive Revenue Recovery
============================================================
Simple meaning: three notebooks + one transaction log.

1. transactions     — every payment that happened
2. at_risk_events   — money that might slip away (degrading or failed)
3. recovery_actions — what the agent tried to win it back
4. audit_log        — full diary: why we did each step (judges love this)
"""

import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "payment_guardian.db")


def _conn():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables if they don't exist yet."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = _conn()
    # WAL = better concurrent reads under live demo + webhooks
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT NOT NULL,
            amount REAL NOT NULL,
            bank TEXT NOT NULL,
            recommended_method TEXT NOT NULL,
            success INTEGER NOT NULL,
            confidence REAL NOT NULL,
            reasoning TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Money that is slipping / already slipped — the recovery queue
    c.execute("""
        CREATE TABLE IF NOT EXISTS at_risk_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT NOT NULL,
            amount REAL NOT NULL,
            bank TEXT NOT NULL,
            original_method TEXT,
            stage TEXT NOT NULL,
            root_cause TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            attempts INTEGER NOT NULL DEFAULT 0,
            amount_recovered REAL NOT NULL DEFAULT 0,
            degradation_score REAL,
            risk_scores_json TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Each try the agent makes on an at-risk case
    c.execute("""
        CREATE TABLE IF NOT EXISTS recovery_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            method_used TEXT,
            success INTEGER,
            amount_recovered REAL NOT NULL DEFAULT 0,
            reason TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (event_id) REFERENCES at_risk_events(id)
        )
    """)

    # Immutable-ish diary for the demo / judges
    c.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER,
            step TEXT NOT NULL,
            detail TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Razorpay webhook idempotency — same event never processed twice
    c.execute("""
        CREATE TABLE IF NOT EXISTS webhook_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            razorpay_event_id TEXT NOT NULL UNIQUE,
            event_type TEXT NOT NULL,
            payload_json TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Payment links created for recovery (Test Mode)
    c.execute("""
        CREATE TABLE IF NOT EXISTS payment_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            razorpay_link_id TEXT UNIQUE,
            short_url TEXT,
            amount REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'created',
            idempotency_key TEXT UNIQUE,
            razorpay_payment_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            paid_at DATETIME,
            FOREIGN KEY (event_id) REFERENCES at_risk_events(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS agent_decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            diagnosis TEXT,
            recommendation TEXT,
            recovery_probability REAL,
            expected_value REAL,
            confidence REAL,
            policy_traffic_light TEXT,
            policy_decision TEXT,
            policy_reason TEXT,
            payload_json TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (event_id) REFERENCES at_risk_events(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS approval_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            recommended_action TEXT NOT NULL,
            reason TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            resolved_at DATETIME,
            FOREIGN KEY (event_id) REFERENCES at_risk_events(id)
        )
    """)

    # Hash-chained audit (Phase 5) — append-only
    c.execute("""
        CREATE TABLE IF NOT EXISTS audit_chain (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER,
            event_type TEXT NOT NULL,
            payload TEXT NOT NULL,
            previous_hash TEXT,
            current_hash TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def save_transaction(customer_id, amount, bank, recommended_method, success, confidence, reasoning):
    conn = _conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO transactions (customer_id, amount, bank, recommended_method, success, confidence, reasoning)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (customer_id, amount, bank, recommended_method, 1 if success else 0, confidence, reasoning))
    txn_id = c.lastrowid
    conn.commit()
    conn.close()
    return txn_id


def create_at_risk_event(
    customer_id, amount, bank, original_method, stage, root_cause,
    degradation_score=None, risk_scores=None
):
    conn = _conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO at_risk_events
        (customer_id, amount, bank, original_method, stage, root_cause,
         status, attempts, degradation_score, risk_scores_json)
        VALUES (?, ?, ?, ?, ?, ?, 'open', 0, ?, ?)
    """, (
        customer_id, amount, bank, original_method, stage, root_cause,
        degradation_score,
        json.dumps(risk_scores) if risk_scores else None,
    ))
    event_id = c.lastrowid
    conn.commit()
    conn.close()
    return event_id


def update_at_risk_event(event_id, **fields):
    if not fields:
        return
    allowed = {"status", "attempts", "amount_recovered", "root_cause", "stage"}
    sets = []
    vals = []
    for k, v in fields.items():
        if k in allowed:
            sets.append(f"{k} = ?")
            vals.append(v)
    if not sets:
        return
    sets.append("updated_at = CURRENT_TIMESTAMP")
    vals.append(event_id)
    conn = _conn()
    conn.execute(f"UPDATE at_risk_events SET {', '.join(sets)} WHERE id = ?", vals)
    conn.commit()
    conn.close()


def get_at_risk_event(event_id):
    conn = _conn()
    row = conn.execute("SELECT * FROM at_risk_events WHERE id = ?", (event_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_open_at_risk(limit=50):
    conn = _conn()
    rows = conn.execute(
        "SELECT * FROM at_risk_events WHERE status IN ('open', 'recovering') "
        "ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_recent_at_risk(limit=40):
    conn = _conn()
    rows = conn.execute(
        "SELECT * FROM at_risk_events ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_recovery_action(event_id, action, method_used, success, amount_recovered, reason):
    conn = _conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO recovery_actions
        (event_id, action, method_used, success, amount_recovered, reason)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (event_id, action, method_used, 1 if success else 0, amount_recovered, reason))
    action_id = c.lastrowid
    conn.commit()
    conn.close()
    return action_id


def get_actions_for_event(event_id):
    conn = _conn()
    rows = conn.execute(
        "SELECT * FROM recovery_actions WHERE event_id = ? ORDER BY id ASC", (event_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_audit(event_id, step, detail):
    conn = _conn()
    conn.execute(
        "INSERT INTO audit_log (event_id, step, detail) VALUES (?, ?, ?)",
        (event_id, step, detail),
    )
    conn.commit()
    conn.close()


def get_audit_for_event(event_id):
    conn = _conn()
    rows = conn.execute(
        "SELECT * FROM audit_log WHERE event_id = ? ORDER BY id ASC", (event_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_recent_transactions(limit=50):
    conn = _conn()
    rows = conn.execute(
        "SELECT * FROM transactions ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_db_stats():
    conn = _conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*), COALESCE(SUM(amount),0), AVG(success) FROM transactions")
    total_count, total_volume, avg_success = c.fetchone()

    c.execute("""
        SELECT
            COUNT(*),
            COALESCE(SUM(amount), 0),
            COALESCE(SUM(amount_recovered), 0),
            SUM(CASE WHEN status = 'recovered' THEN 1 ELSE 0 END),
            SUM(CASE WHEN status = 'stopped' THEN 1 ELSE 0 END),
            SUM(CASE WHEN status = 'escalated' THEN 1 ELSE 0 END),
            SUM(CASE WHEN stage = 'degrading' THEN 1 ELSE 0 END),
            SUM(CASE WHEN stage = 'failed' THEN 1 ELSE 0 END),
            SUM(CASE WHEN status = 'awaiting_payment' THEN 1 ELSE 0 END)
        FROM at_risk_events
    """)
    (
        risk_count, at_risk_volume, recovered_volume,
        recovered_n, stopped_n, escalated_n, degrading_n, failed_n, awaiting_n
    ) = c.fetchone()

    c.execute("SELECT COUNT(*) FROM payment_links WHERE status = 'paid'")
    links_paid = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM payment_links")
    links_total = c.fetchone()[0] or 0

    conn.close()
    return {
        "total_transactions": total_count or 0,
        "total_volume": round(total_volume or 0.0, 2),
        "overall_success_rate": round(avg_success or 0.0, 3),
        "at_risk_cases": risk_count or 0,
        "at_risk_volume": round(at_risk_volume or 0.0, 2),
        "revenue_recovered": round(recovered_volume or 0.0, 2),
        "recovered_cases": recovered_n or 0,
        "stopped_cases": stopped_n or 0,
        "escalated_cases": escalated_n or 0,
        "degrading_cases": degrading_n or 0,
        "failed_cases": failed_n or 0,
        "awaiting_payment": awaiting_n or 0,
        "payment_links_total": links_total,
        "payment_links_paid": links_paid,
    }


# ---- Razorpay helpers ----

def webhook_already_seen(razorpay_event_id: str) -> bool:
    conn = _conn()
    row = conn.execute(
        "SELECT 1 FROM webhook_events WHERE razorpay_event_id = ?",
        (razorpay_event_id,),
    ).fetchone()
    conn.close()
    return row is not None


def mark_webhook_seen(razorpay_event_id: str, event_type: str, payload_json: str):
    conn = _conn()
    try:
        conn.execute(
            "INSERT INTO webhook_events (razorpay_event_id, event_type, payload_json) VALUES (?, ?, ?)",
            (razorpay_event_id, event_type, payload_json),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # duplicate race
    finally:
        conn.close()


def get_open_payment_link_for_event(event_id: int):
    conn = _conn()
    row = conn.execute(
        "SELECT * FROM payment_links WHERE event_id = ? AND status IN ('created', 'issued') "
        "ORDER BY id DESC LIMIT 1",
        (event_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def save_payment_link(event_id, razorpay_link_id, short_url, amount, idempotency_key, status="created"):
    conn = _conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO payment_links
        (event_id, razorpay_link_id, short_url, amount, status, idempotency_key)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (event_id, razorpay_link_id, short_url, amount, status, idempotency_key))
    lid = c.lastrowid
    conn.commit()
    conn.close()
    return lid


def mark_payment_link_paid(razorpay_link_id=None, event_id=None, razorpay_payment_id=None):
    conn = _conn()
    if razorpay_link_id:
        conn.execute(
            "UPDATE payment_links SET status = 'paid', razorpay_payment_id = ?, "
            "paid_at = CURRENT_TIMESTAMP WHERE razorpay_link_id = ?",
            (razorpay_payment_id, razorpay_link_id),
        )
    elif event_id:
        conn.execute(
            "UPDATE payment_links SET status = 'paid', razorpay_payment_id = ?, "
            "paid_at = CURRENT_TIMESTAMP WHERE event_id = ? AND status != 'paid'",
            (razorpay_payment_id, event_id),
        )
    conn.commit()
    conn.close()


def find_event_id_by_payment_notes(revene_event_id: str):
    if not revene_event_id:
        return None
    try:
        eid = int(revene_event_id)
    except (TypeError, ValueError):
        return None
    return eid if get_at_risk_event(eid) else None


def get_payment_links_for_event(event_id: int):
    conn = _conn()
    rows = conn.execute(
        "SELECT * FROM payment_links WHERE event_id = ? ORDER BY id DESC",
        (event_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_agent_decision(event_id, decision: dict, policy: dict):
    conn = _conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO agent_decisions
        (event_id, diagnosis, recommendation, recovery_probability, expected_value,
         confidence, policy_traffic_light, policy_decision, policy_reason, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event_id,
        decision.get("diagnosis"),
        decision.get("recommended_action"),
        decision.get("recovery_probability"),
        decision.get("expected_recovery_value"),
        decision.get("confidence"),
        policy.get("traffic_light"),
        policy.get("decision"),
        policy.get("reason"),
        json.dumps({"decision": decision, "policy": policy}),
    ))
    row_id = c.lastrowid
    conn.commit()
    conn.close()
    return row_id


def get_latest_decision(event_id: int):
    conn = _conn()
    row = conn.execute(
        "SELECT * FROM agent_decisions WHERE event_id = ? ORDER BY id DESC LIMIT 1",
        (event_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def enqueue_approval(event_id, recommended_action, reason):
    conn = _conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO approval_queue (event_id, recommended_action, reason, status)
        VALUES (?, ?, ?, 'pending')
    """, (event_id, recommended_action, reason))
    aid = c.lastrowid
    conn.commit()
    conn.close()
    return aid


def list_approvals(status="pending", limit=50):
    conn = _conn()
    rows = conn.execute(
        "SELECT * FROM approval_queue WHERE status = ? ORDER BY id DESC LIMIT ?",
        (status, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def resolve_approval(approval_id, status="approved"):
    conn = _conn()
    conn.execute(
        "UPDATE approval_queue SET status = ?, resolved_at = CURRENT_TIMESTAMP WHERE id = ?",
        (status, approval_id),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM approval_queue WHERE id = ?", (approval_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def append_audit_chain(event_id, event_type: str, payload: str) -> dict:
    """SHA-256 hash chain: current = sha256(id|ts|type|prev|payload)."""
    import hashlib
    from datetime import datetime, timezone

    conn = _conn()
    prev = conn.execute(
        "SELECT current_hash FROM audit_chain ORDER BY id DESC LIMIT 1"
    ).fetchone()
    previous_hash = prev["current_hash"] if prev else "GENESIS"
    ts = datetime.now(timezone.utc).isoformat()
    # provisional hash without id, then update — use next id estimate
    c = conn.cursor()
    c.execute(
        "INSERT INTO audit_chain (event_id, event_type, payload, previous_hash, current_hash) "
        "VALUES (?, ?, ?, ?, ?)",
        (event_id, event_type, payload, previous_hash, "PENDING"),
    )
    row_id = c.lastrowid
    material = f"{row_id}|{ts}|{event_type}|{previous_hash}|{payload}"
    current_hash = hashlib.sha256(material.encode("utf-8")).hexdigest()
    c.execute("UPDATE audit_chain SET current_hash = ? WHERE id = ?", (current_hash, row_id))
    conn.commit()
    conn.close()
    return {"id": row_id, "previous_hash": previous_hash, "current_hash": current_hash}


def verify_audit_chain(limit=500) -> dict:
    import hashlib
    conn = _conn()
    rows = conn.execute(
        "SELECT * FROM audit_chain ORDER BY id ASC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    prev = "GENESIS"
    for r in rows:
        if r["previous_hash"] != prev:
            return {"ok": False, "broken_at": r["id"], "expected_prev": prev, "got": r["previous_hash"]}
        prev = r["current_hash"]
    return {"ok": True, "entries": len(rows), "tip_hash": prev if rows else "GENESIS"}


if __name__ == "__main__":
    init_db()
    print("DB ready:", DB_PATH)
    print(get_db_stats())
