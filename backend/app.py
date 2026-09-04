"""
Payment Guardian — Predictive Revenue Recovery (backend)
========================================================
SIMPLE FLOW:
  1. Fake customers keep paying (live demo stream)
  2. AI scores: will this method work? Is the bank sick?
  3. If looking sick  → open "at-risk" case (PREDICT lane)
     If already failed → open "at-risk" case (RECOVER lane)
  4. Agent picks ONE action with stop rules, logs audit
  5. Dashboard shows ₹ preempted / ₹ recovered live
  6. /api/run_recovery_batch proves money won back on a batch

Run: python backend/app.py
  → http://localhost:5000       landing (Buildathon-inspired)
  → http://localhost:5000/demo  recovery console
"""

import sys
import os
import json
import random
import threading
import time

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "monitor"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "engine"))
sys.path.append(os.path.dirname(__file__))

from flask import Flask, send_file, request, jsonify
from flask_socketio import SocketIO
from outage_monitor import OutageMonitor
from route_recommender import recommend_route
import db
import recovery_agent as agent
import xgboost as xgb
import pickle
import pandas as pd

BASE = os.path.join(os.path.dirname(__file__), "..")

db.init_db()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")


@app.route("/")
def index():
    """Product landing."""
    return send_file(os.path.join(BASE, "frontend", "landing.html"))


@app.route("/demo")
def demo():
    """Live predictive recovery console."""
    return send_file(os.path.join(BASE, "frontend", "dashboard.html"))


@app.route("/assets/<path:filename>")
def assets(filename):
    """Landing / marketing images."""
    return send_file(os.path.join(BASE, "frontend", "assets", filename))


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response


# ---- Load trained risk model ----
model = xgb.XGBClassifier()
model.load_model(os.path.join(BASE, "models", "risk_model.json"))
with open(os.path.join(BASE, "models", "encoders.pkl"), "rb") as f:
    meta = pickle.load(f)
encoders, FEATURES = meta["encoders"], meta["features"]

BANKS = list(encoders["bank"].classes_)
METHODS = list(encoders["method"].classes_)
BANK_BASELINES = {"HDFC": 0.06, "SBI": 0.11, "ICICI": 0.07, "Axis": 0.09, "Kotak": 0.08, "PNB": 0.13}

outage_monitor = OutageMonitor(BANK_BASELINES)

state = {
    "revenue_protected": 0.0,   # old metric: good routing avoided a bad method
    "revenue_preempted": 0.0,   # NEW: saved while still at checkout (degrading)
    "revenue_recovered": 0.0,   # NEW: won back after failure
    "transactions_processed": 0,
    "forced_outage_bank": None,
    "forced_outage_ticks_left": 0,
}


def predict_success(method, bank, amount, hour, day_of_week, past_failures=0):
    row = pd.DataFrame([{
        "method_enc": encoders["method"].transform([method])[0],
        "bank_enc": encoders["bank"].transform([bank])[0],
        "amount": amount,
        "hour": hour,
        "day_of_week": day_of_week,
        "past_failures_this_method": past_failures,
    }])[FEATURES]
    return float(model.predict_proba(row)[0][1])


def score_methods(bank, amount, hour, day_of_week):
    risk_scores, outage_status = {}, {}
    bank_check = outage_monitor._check(bank)
    for method in METHODS:
        risk_scores[method] = predict_success(method, bank, amount, hour, day_of_week)
        outage_status[method] = {
            "bank": bank,
            "outage": bank_check.get("outage", False),
            "z_score": bank_check.get("z_score", 0.0),
        }
    return risk_scores, outage_status, bank_check


def _persist_action(event_id, action, method_used, success, amount_recovered, reason):
    return db.save_recovery_action(event_id, action, method_used, success, amount_recovered, reason)


def handle_at_risk_case(
    customer_id, amount, bank, method, stage, root_cause,
    deg_score, risk_scores, outage_status, bank_outage,
):
    """Create at-risk event, run one agent step, update money counters."""
    event_id = db.create_at_risk_event(
        customer_id=customer_id,
        amount=amount,
        bank=bank,
        original_method=method,
        stage=stage,
        root_cause=root_cause,
        degradation_score=deg_score,
        risk_scores=risk_scores,
    )
    db.add_audit(
        event_id,
        "detect",
        f"{stage} detected for {customer_id}: ₹{amount}, bank={bank}, "
        f"method={method}, cause={root_cause}, deg_score={deg_score}",
    )

    event = db.get_at_risk_event(event_id)
    result = agent.run_one_recovery_step(
        event,
        risk_scores,
        outage_status,
        bank_outage,
        save_action=_persist_action,
        update_event=db.update_at_risk_event,
        add_audit=db.add_audit,
    )

    if result["success"] and result["amount_recovered"] > 0:
        if result["lane"] == "preempt":
            state["revenue_preempted"] += result["amount_recovered"]
        else:
            state["revenue_recovered"] += result["amount_recovered"]

    return event_id, result


def simulate_loop():
    """Background loop: live payments + predictive recovery."""
    while True:
        customer_id = f"cust_{random.randint(1, 4000)}"
        amount = round(random.lognormvariate(6.5, 1.0), 2)
        hour = time.localtime().tm_hour
        day_of_week = time.localtime().tm_wday
        chosen_bank = random.choice(BANKS)

        if state["forced_outage_bank"] and state["forced_outage_ticks_left"] > 0:
            chosen_bank = state["forced_outage_bank"]
            state["forced_outage_ticks_left"] -= 1
            if state["forced_outage_ticks_left"] <= 0:
                state["forced_outage_bank"] = None

        risk_scores, outage_status, bank_check = score_methods(
            chosen_bank, amount, hour, day_of_week
        )
        decision = recommend_route(risk_scores, outage_status)
        recommended = decision["recommended_method"]
        best_p = max(risk_scores.values())
        z = float(bank_check.get("z_score", 0.0) or 0.0)
        outage_flag = bool(bank_check.get("outage")) or (
            state["forced_outage_bank"] == chosen_bank
        )

        deg = agent.degradation_score(best_p, z, outage_flag)

        # ---- PREDICT lane FIRST (before money is lost) ----
        recovery_payload = None
        attempt_method = recommended
        preempt_event_id = None
        preempt_choice = None

        if deg >= agent.DEGRADE_SCORE_THRESHOLD:
            root_cause = agent.diagnose(
                "degrading", chosen_bank, outage_flag, z, risk_scores, recommended
            )
            preempt_event_id = db.create_at_risk_event(
                customer_id=customer_id,
                amount=amount,
                bank=chosen_bank,
                original_method=recommended,
                stage="degrading",
                root_cause=root_cause,
                degradation_score=deg,
                risk_scores=risk_scores,
            )
            db.add_audit(
                preempt_event_id,
                "detect",
                f"degrading: ₹{amount}, bank={chosen_bank}, deg={deg}, cause={root_cause}",
            )
            fake_event = {
                "id": preempt_event_id,
                "amount": amount,
                "original_method": recommended,
                "attempts": 0,
                "status": "open",
                "stage": "degrading",
                "root_cause": root_cause,
            }
            preempt_choice = agent.choose_action(
                "degrading", root_cause, fake_event, risk_scores, outage_status
            )
            db.add_audit(
                preempt_event_id,
                "decide",
                f"action={preempt_choice['action']}, method={preempt_choice['method']}, "
                f"rule={preempt_choice['rule_id']}",
            )
            if preempt_choice.get("method"):
                attempt_method = preempt_choice["method"]

        # Attempt payment (forced low success during demo outage)
        if chosen_bank in outage_monitor.active_outages or state["forced_outage_bank"] == chosen_bank:
            success_prob = 0.15
        else:
            success_prob = risk_scores.get(attempt_method, risk_scores[recommended])
        success = random.random() < success_prob

        outage_result = outage_monitor.record(chosen_bank, success)

        db.save_transaction(
            customer_id=customer_id,
            amount=amount,
            bank=chosen_bank,
            recommended_method=attempt_method,
            success=success,
            confidence=decision["confidence"],
            reasoning=decision["reasoning"],
        )

        # Classic "protected" metric (good routing vs worst method)
        worst_score = min(risk_scores.values())
        best_score = risk_scores[attempt_method]
        if best_score - worst_score > 0.15 and success:
            state["revenue_protected"] += amount

        # Close the preempt case using the REAL payment outcome
        if preempt_event_id and preempt_choice:
            switched = attempt_method != recommended
            preempt_success = bool(success and switched)
            recovered_amt = amount if preempt_success else 0.0
            db.save_recovery_action(
                preempt_event_id,
                preempt_choice["action"],
                attempt_method,
                preempt_success,
                recovered_amt,
                preempt_choice["reason"],
            )
            if preempt_success:
                state["revenue_preempted"] += amount
                db.update_at_risk_event(
                    preempt_event_id, status="recovered", attempts=1, amount_recovered=amount
                )
                db.add_audit(
                    preempt_event_id,
                    "outcome",
                    f"PREEMPT SUCCESS: switched {recommended}→{attempt_method}, payment OK, ₹{amount}",
                )
            else:
                db.update_at_risk_event(
                    preempt_event_id,
                    status="recovering" if not success else "stopped",
                    attempts=1,
                )
                db.add_audit(
                    preempt_event_id,
                    "outcome",
                    f"preempt applied ({preempt_choice['action']}); payment={'ok' if success else 'fail'}",
                )
            recovery_payload = {
                "event_id": preempt_event_id,
                "stage": "degrading",
                "root_cause": root_cause,
                "degradation_score": deg,
                "action": preempt_choice["action"],
                "method": attempt_method,
                "success": preempt_success,
                "amount_recovered": recovered_amt,
                "status": "recovered" if preempt_success else ("recovering" if not success else "stopped"),
                "reason": preempt_choice["reason"],
                "rule_id": preempt_choice["rule_id"],
                "lane": "preempt",
                "attempts": 1,
            }

        # ---- RECOVER lane (payment already failed) ----
        if not success:
            root_cause = agent.diagnose(
                "failed", chosen_bank, outage_flag, z, risk_scores, attempt_method
            )
            event_id, result = handle_at_risk_case(
                customer_id, amount, chosen_bank, attempt_method,
                "failed", root_cause, deg, risk_scores, outage_status, outage_flag,
            )
            recovery_payload = {
                "event_id": event_id,
                "stage": "failed",
                "root_cause": root_cause,
                "degradation_score": deg,
                **result,
            }

        state["transactions_processed"] += 1

        socketio.emit("transaction", {
            "customer_id": customer_id,
            "amount": amount,
            "bank": chosen_bank,
            "recommended_method": recommended,
            "confidence": decision["confidence"],
            "reasoning": decision["reasoning"],
            "success": success,
            "outage_active": outage_result["outage"],
            "degradation_score": deg,
            "revenue_protected": round(state["revenue_protected"], 2),
            "revenue_preempted": round(state["revenue_preempted"], 2),
            "revenue_recovered": round(state["revenue_recovered"], 2),
            "transactions_processed": state["transactions_processed"],
            "active_outage_banks": list(outage_monitor.active_outages),
            "recovery": recovery_payload,
        })

        time.sleep(0.7)


@app.route("/trigger_outage/<bank>")
def trigger_outage(bank):
    state["forced_outage_bank"] = bank
    state["forced_outage_ticks_left"] = 18
    return {"status": "outage triggered", "bank": bank}


@app.route("/checkout_recommendation", methods=["GET", "POST"])
def checkout_recommendation():
    bank = request.args.get("bank") or (request.json and request.json.get("bank")) or "SBI"
    try:
        amount = float(request.args.get("amount") or (request.json and request.json.get("amount")) or 2500)
    except Exception:
        amount = 2500.0

    hour = time.localtime().tm_hour
    day_of_week = time.localtime().tm_wday
    risk_scores, outage_status, bank_check = score_methods(bank, amount, hour, day_of_week)
    decision = recommend_route(risk_scores, outage_status)
    best_p = max(risk_scores.values())
    z = float(bank_check.get("z_score", 0) or 0)
    outage_flag = bool(bank_check.get("outage"))
    deg = agent.degradation_score(best_p, z, outage_flag)
    stage = "degrading" if deg >= agent.DEGRADE_SCORE_THRESHOLD else "healthy"
    cause = agent.diagnose(stage if stage != "healthy" else "degrading", bank, outage_flag, z, risk_scores, decision["recommended_method"]) if stage != "healthy" else None

    return {
        **decision,
        "degradation_score": deg,
        "stage": stage,
        "root_cause": cause,
        "bank_z_score": z,
        "outage": outage_flag,
    }


@app.route("/api/db_transactions")
def api_db_transactions():
    return jsonify(db.get_recent_transactions(int(request.args.get("limit", 50))))


@app.route("/api/db_stats")
def api_db_stats():
    stats = db.get_db_stats()
    stats["live_revenue_preempted"] = round(state["revenue_preempted"], 2)
    stats["live_revenue_recovered"] = round(state["revenue_recovered"], 2)
    stats["live_revenue_protected"] = round(state["revenue_protected"], 2)
    return jsonify(stats)


@app.route("/api/at_risk")
def api_at_risk():
    return jsonify(db.get_recent_at_risk(int(request.args.get("limit", 40))))


@app.route("/api/case/<int:event_id>")
def api_case(event_id):
    event = db.get_at_risk_event(event_id)
    if not event:
        return jsonify({"error": "not found"}), 404
    return jsonify({
        "event": event,
        "actions": db.get_actions_for_event(event_id),
        "audit": db.get_audit_for_event(event_id),
    })


@app.route("/api/run_recovery_batch", methods=["POST", "GET"])
def run_recovery_batch():
    """
    THE JUDGE BUTTON.
    Take N open/recovering cases (or seed failures) and run recovery steps.
    Returns measured ₹ at risk vs ₹ recovered — Track 03 bar.
    """
    n = int(request.args.get("n") or (request.json or {}).get("n", 40))

    # Prefer real open cases; if too few, seed synthetic failed batch
    cases = db.get_open_at_risk(limit=n)
    seeded = 0
    while len(cases) < n:
        bank = random.choice(BANKS)
        amount = round(random.lognormvariate(6.8, 0.8), 2)
        hour = time.localtime().tm_hour
        dow = time.localtime().tm_wday
        risk_scores, outage_status, bank_check = score_methods(bank, amount, hour, dow)
        method = min(risk_scores, key=risk_scores.get)  # pick a weak method on purpose
        z = float(bank_check.get("z_score", 0) or 0)
        outage_flag = bool(bank_check.get("outage"))
        deg = agent.degradation_score(risk_scores[method], z, outage_flag)
        cause = agent.diagnose("failed", bank, outage_flag, z, risk_scores, method)
        eid = db.create_at_risk_event(
            customer_id=f"batch_cust_{random.randint(1, 9999)}",
            amount=amount,
            bank=bank,
            original_method=method,
            stage="failed",
            root_cause=cause,
            degradation_score=deg,
            risk_scores=risk_scores,
        )
        db.add_audit(eid, "detect", f"batch-seeded failed case ₹{amount} cause={cause}")
        cases.append(db.get_at_risk_event(eid))
        seeded += 1

    at_risk_total = 0.0
    recovered_total = 0.0
    preempted_total = 0.0
    results = []
    stopped = escalated = recovered_n = 0

    for event in cases[:n]:
        at_risk_total += float(event["amount"])
        scores = json.loads(event["risk_scores_json"]) if event.get("risk_scores_json") else None
        if not scores:
            hour = time.localtime().tm_hour
            dow = time.localtime().tm_wday
            scores, outage_status, bank_check = score_methods(
                event["bank"], event["amount"], hour, dow
            )
        else:
            _, outage_status, bank_check = score_methods(
                event["bank"], event["amount"],
                time.localtime().tm_hour, time.localtime().tm_wday,
            )

        outage_flag = bool(bank_check.get("outage"))
        # refresh live event row (attempts/status may change mid-batch)
        live = db.get_at_risk_event(event["id"]) or event
        if live["status"] in ("recovered", "stopped", "escalated"):
            continue

        result = agent.run_one_recovery_step(
            live,
            scores,
            outage_status,
            outage_flag,
            save_action=_persist_action,
            update_event=db.update_at_risk_event,
            add_audit=db.add_audit,
        )
        results.append(result)

        if result["success"]:
            recovered_n += 1
            if result["lane"] == "preempt":
                preempted_total += result["amount_recovered"]
                state["revenue_preempted"] += result["amount_recovered"]
            else:
                recovered_total += result["amount_recovered"]
                state["revenue_recovered"] += result["amount_recovered"]
        if result["status"] == "stopped":
            stopped += 1
        if result["status"] == "escalated":
            escalated += 1

    won = recovered_total + preempted_total
    summary = {
        "batch_size": len(results),
        "seeded_failures": seeded,
        "amount_at_risk": round(at_risk_total, 2),
        "amount_recovered": round(recovered_total, 2),
        "amount_preempted": round(preempted_total, 2),
        "amount_won_back": round(won, 2),
        "recovery_rate": round(won / at_risk_total, 3) if at_risk_total else 0,
        "cases_recovered": recovered_n,
        "cases_stopped": stopped,
        "cases_escalated": escalated,
        "live_revenue_recovered": round(state["revenue_recovered"], 2),
        "live_revenue_preempted": round(state["revenue_preempted"], 2),
        "results": results[:25],  # trim for UI
    }
    socketio.emit("batch_complete", summary)
    return jsonify(summary)


@socketio.on("connect")
def on_connect():
    print("Dashboard connected")


if __name__ == "__main__":
    threading.Thread(target=simulate_loop, daemon=True).start()
    socketio.run(app, host="0.0.0.0", port=5000, debug=False, allow_unsafe_werkzeug=True)
