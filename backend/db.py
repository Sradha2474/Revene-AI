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
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all tables if they don't exist yet."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = _conn()
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
            SUM(CASE WHEN stage = 'failed' THEN 1 ELSE 0 END)
        FROM at_risk_events
    """)
    (
        risk_count, at_risk_volume, recovered_volume,
        recovered_n, stopped_n, escalated_n, degrading_n, failed_n
    ) = c.fetchone()

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
    }


if __name__ == "__main__":
    init_db()
    print("DB ready:", DB_PATH)
    print(get_db_stats())
