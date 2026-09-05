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
  7. Razorpay Test Payment Links + webhooks
     → ₹ recovered only after payment.captured

Run (dev):  python backend/app.py
Run (prod): python scripts/run_production.py
  → http://localhost:5000       landing
  → http://localhost:5000/demo  recovery console
"""

import sys
import os
import json
import random
import threading
import time
import uuid

# Load .env from project root (RAZORPAY_* keys) — never hardcode secrets
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "monitor"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "engine"))
sys.path.append(os.path.dirname(__file__))

from flask import Flask, send_file, send_from_directory, request, jsonify, g
from flask_socketio import SocketIO
from outage_monitor import OutageMonitor
from route_recommender import recommend_route
import db
import recovery_agent as agent
import razorpay_client as rzp
import action_executor
import webhooks as wh
import recovery_pipeline
import payment_health
import simulator
import config as app_config
import logging_setup
import security
import xgboost as xgb
import pickle
import pandas as pd

BASE = os.path.join(os.path.dirname(__file__), "..")

SETTINGS = app_config.load_settings()
log = logging_setup.setup_logging(SETTINGS.log_level)

_boot_errors = app_config.validate_settings(SETTINGS)
if _boot_errors:
    for err in _boot_errors:
        log.error("CONFIG: %s", err)
    if SETTINGS.is_production:
        raise SystemExit("Refusing to start: fix production config errors above.")
elif SETTINGS.is_production:
    log.info("Production config OK (env=%s)", SETTINGS.app_env)
else:
    log.info("Development mode (env=%s)", SETTINGS.app_env)

db.init_db()

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
_cors = SETTINGS.cors_origins
socketio = SocketIO(
    app,
    cors_allowed_origins="*" if _cors == ["*"] else _cors,
    async_mode="threading",
    logger=False,
    engineio_logger=False,
)


def _settings():
    return SETTINGS


@app.before_request
def _request_context():
    g.request_id = request.headers.get("X-Request-Id") or uuid.uuid4().hex[:12]
    g.started_at = time.monotonic()


@app.after_request
def add_security_and_cors(response):
    origin_ok = "*"
    if SETTINGS.cors_origins != ["*"]:
        req_origin = request.headers.get("Origin")
        if req_origin in SETTINGS.cors_origins:
            origin_ok = req_origin
        else:
            origin_ok = SETTINGS.cors_origins[0]
    response.headers["Access-Control-Allow-Origin"] = origin_ok
    response.headers["Access-Control-Allow-Headers"] = (
        "Content-Type,Authorization,X-API-Key,X-Request-Id,X-Razorpay-Signature"
    )
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    response.headers["X-Request-Id"] = getattr(g, "request_id", "")
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if SETTINGS.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.errorhandler(404)
def _not_found(_e):
    if request.path.startswith("/api/") or request.path.startswith("/webhooks/"):
        return jsonify({"error": "not_found"}), 404
    return jsonify({"error": "not_found"}), 404


@app.errorhandler(500)
def _server_error(e):
    log.exception("Unhandled error request_id=%s: %s", getattr(g, "request_id", "-"), e)
    return jsonify({"error": "internal_error", "request_id": getattr(g, "request_id", None)}), 500


@app.route("/health")
def health():
    """Liveness — process is up."""
    return jsonify({
        "status": "ok",
        "service": "revene",
        "env": SETTINGS.app_env,
    })


@app.route("/ready")
def ready():
    """Readiness — DB + model + optional Razorpay."""
    checks = {"db": False, "model": False, "razorpay": SETTINGS.razorpay_configured}
    try:
        db.get_db_stats()
        checks["db"] = True
    except Exception as ex:
        log.warning("ready db check failed: %s", ex)
    checks["model"] = model is not None
    ok = checks["db"] and checks["model"]
    if SETTINGS.is_production:
        ok = ok and checks["razorpay"] and bool(SETTINGS.razorpay_webhook_secret)
    code = 200 if ok else 503
    return jsonify({"status": "ready" if ok else "not_ready", "checks": checks}), code


REACT_DIST = os.path.join(BASE, "web", "dist")


def _react_index():
    index = os.path.join(REACT_DIST, "index.html")
    if os.path.isfile(index):
        return send_file(index)
    # Fallback to legacy HTML if React not built yet
    return None


@app.route("/")
def index():
    """Product landing (React SPA when web/dist exists)."""
    spa = _react_index()
    if spa:
        return spa
    return send_file(os.path.join(BASE, "frontend", "landing.html"))


@app.route("/demo")
@app.route("/demo/")
@app.route("/demo/<path:subpath>")
def demo(subpath=None):
    """Recovery console SPA routes."""
    spa = _react_index()
    if spa:
        return spa
    return send_file(os.path.join(BASE, "frontend", "dashboard.html"))


@app.route("/assets/<path:filename>")
def assets(filename):
    """Vite build assets, else legacy marketing images."""
    dist_assets = os.path.join(REACT_DIST, "assets")
    candidate = os.path.join(dist_assets, filename)
    if os.path.isfile(candidate):
        return send_from_directory(dist_assets, filename)
    legacy = os.path.join(BASE, "frontend", "assets", filename)
    if os.path.isfile(legacy):
        return send_file(legacy)
    return jsonify({"error": "not_found"}), 404


@app.route("/favicon.svg")
def favicon():
    path = os.path.join(REACT_DIST, "favicon.svg")
    if os.path.isfile(path):
        return send_file(path)
    legacy = os.path.join(BASE, "web", "public", "favicon.svg")
    if os.path.isfile(legacy):
        return send_file(legacy)
    return ("", 204)


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
    if not SETTINGS.enable_live_simulator:
        log.info("Live simulator disabled (ENABLE_LIVE_SIMULATOR=0)")
        return
    log.info("Live simulator started")
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
    stats["razorpay_configured"] = rzp.is_configured()
    stats["webhook_secret_configured"] = bool(wh.webhook_secret())
    return jsonify(stats)


@app.route("/api/at_risk")
def api_at_risk():
    return jsonify(db.get_recent_at_risk(int(request.args.get("limit", 40))))


@app.route("/api/razorpay/status")
def api_razorpay_status():
    """Dashboard badge: are Test keys loaded?"""
    return jsonify({
        "configured": rzp.is_configured(),
        "webhook_secret_configured": bool(wh.webhook_secret()),
        "mode": "test" if (os.getenv("RAZORPAY_KEY_ID") or "").startswith("rzp_test") else "unknown",
        "env": SETTINGS.app_env,
        "live_simulator": SETTINGS.enable_live_simulator,
        "hint": (
            "Keys loaded from .env"
            if rzp.is_configured()
            else "Add RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET to .env"
        ),
    })


@app.route("/api/case/<int:event_id>")
def api_case(event_id):
    event = db.get_at_risk_event(event_id)
    if not event:
        return jsonify({"error": "not found"}), 404
    return jsonify({
        "event": event,
        "actions": db.get_actions_for_event(event_id),
        "audit": db.get_audit_for_event(event_id),
        "payment_links": db.get_payment_links_for_event(event_id),
    })


@app.route("/api/cases/<int:event_id>/payment_link", methods=["POST"])
@security.require_api_key_if_enabled(_settings)
@security.rate_limit(20, 60.0, prefix="payment_link")
def api_create_payment_link(event_id):
    """
    DEMO ACTION: create a real Razorpay Test Payment Link for this at-risk case.
    Runs investigate → policy first; only GREEN (or force=1) creates the link.
    """
    event = db.get_at_risk_event(event_id)
    if not event:
        return jsonify({"error": "not found"}), 404
    if event.get("status") == "recovered":
        return jsonify({"error": "already_recovered"}), 400

    force = request.args.get("force") == "1" or (request.json or {}).get("force")

    # Score context for investigation
    hour = time.localtime().tm_hour
    dow = time.localtime().tm_wday
    scores = {}
    if event.get("risk_scores_json"):
        try:
            scores = json.loads(event["risk_scores_json"])
        except Exception:
            scores = {}
    if not scores:
        scores, outage_status, bank_check = score_methods(
            event["bank"], event["amount"], hour, dow
        )
    else:
        _, outage_status, bank_check = score_methods(
            event["bank"], event["amount"], hour, dow
        )

    pipeline = recovery_pipeline.run_investigation(
        event,
        scores,
        outage_status,
        bank_check=bank_check,
        interventions=int(event.get("attempts") or 0),
        auto_execute_green_link=False,
    )
    policy = pipeline["policy"]

    # Dashboard already requires a human click → that satisfies YELLOW.
    # Only RED blocks (unless force=1). React can use /investigate + /approvals later.
    if policy["traffic_light"] == "RED" and not force:
        return jsonify({"error": "policy_blocked", "pipeline": pipeline}), 403

    result = action_executor.create_recovery_payment_link(event)
    if not result.get("ok"):
        return jsonify({**result, "pipeline": pipeline}), 400

    socketio.emit("payment_link_created", {
        "event_id": event_id,
        "short_url": result.get("short_url"),
        "razorpay_link_id": result.get("razorpay_link_id"),
    })
    return jsonify({**result, "pipeline": pipeline})


@app.route("/api/cases/<int:event_id>/investigate", methods=["GET", "POST"])
def api_investigate(event_id):
    """Phase 2+3: WHY + WHAT NEXT + policy traffic light."""
    event = db.get_at_risk_event(event_id)
    if not event:
        return jsonify({"error": "not found"}), 404
    hour = time.localtime().tm_hour
    dow = time.localtime().tm_wday
    scores = {}
    if event.get("risk_scores_json"):
        try:
            scores = json.loads(event["risk_scores_json"])
        except Exception:
            scores = {}
    if not scores:
        scores, outage_status, bank_check = score_methods(
            event["bank"], event["amount"], hour, dow
        )
    else:
        _, outage_status, bank_check = score_methods(
            event["bank"], event["amount"], hour, dow
        )
    out = recovery_pipeline.run_investigation(
        event, scores, outage_status, bank_check=bank_check,
        interventions=len(db.get_actions_for_event(event_id)),
    )
    return jsonify(out)


@app.route("/api/approvals")
def api_approvals():
    return jsonify(db.list_approvals(request.args.get("status", "pending")))


@app.route("/api/approvals/<int:approval_id>/decide", methods=["POST"])
@security.require_api_key_if_enabled(_settings)
def api_approval_decide(approval_id):
    body = request.json or {}
    status = body.get("status", "approved")  # approved | rejected
    row = db.resolve_approval(approval_id, status=status)
    if not row:
        return jsonify({"error": "not found"}), 404
    result = {"approval": row}
    if status == "approved":
        event = db.get_at_risk_event(row["event_id"])
        if event and row.get("recommended_action") == "send_payment_link":
            result["execution"] = action_executor.create_recovery_payment_link(event)
        db.add_audit(row["event_id"], "approval_resolved", f"status={status}")
    else:
        db.update_at_risk_event(row["event_id"], status="stopped")
        db.add_audit(row["event_id"], "approval_rejected", "Human rejected recovery action")
    return jsonify(result)


@app.route("/api/payment_health")
def api_payment_health():
    """Snapshot of bank health from the live outage monitor."""
    banks = []
    for b in BANKS:
        check = outage_monitor._check(b)
        banks.append(payment_health.route_health(
            bank=b,
            z_score=float(check.get("z_score") or 0),
            outage=bool(check.get("outage")),
            recent_failure_rate=check.get("recent_failure_rate"),
            baseline_failure_rate=check.get("baseline_failure_rate"),
        ))
    return jsonify({"banks": banks, "active_outages": list(outage_monitor.active_outages)})


@app.route("/api/simulate_strategies", methods=["GET", "POST"])
def api_simulate_strategies():
    """Phase 5: compare recovery thresholds on recent/open cases."""
    n = int(request.args.get("n") or (request.json or {}).get("n", 40))
    thresholds = (request.json or {}).get("thresholds") or [0.70, 0.85]
    cases = db.get_recent_at_risk(n)
    sim_input = []
    hour = time.localtime().tm_hour
    dow = time.localtime().tm_wday
    for ev in cases:
        scores = {}
        if ev.get("risk_scores_json"):
            try:
                scores = json.loads(ev["risk_scores_json"])
            except Exception:
                scores = {}
        if not scores:
            scores, _, _ = score_methods(ev["bank"], ev["amount"], hour, dow)
        p = max(scores.values()) if scores else 0.5
        sim_input.append({"amount": ev["amount"], "recovery_probability": p})
    return jsonify(simulator.simulate_threshold_strategies(sim_input, thresholds))


@app.route("/api/audit/verify")
def api_audit_verify():
    return jsonify(db.verify_audit_chain())


@app.route("/webhooks/razorpay", methods=["POST"])
@security.rate_limit(120, 60.0, prefix="webhook")
def razorpay_webhook():
    """
    Razorpay calls this URL (via tunnel) on payment events.
    Must verify signature; must ignore duplicates.
    """
    body = request.get_data()
    signature = request.headers.get("X-Razorpay-Signature")

    secret_ok = bool(wh.webhook_secret())
    if SETTINGS.is_production and not secret_ok:
        return jsonify({"error": "webhook_secret_required"}), 503

    if secret_ok:
        if not wh.verify_signature(body, signature):
            log.warning("webhook invalid signature ip=%s", security.client_ip())
            return jsonify({"error": "invalid_signature"}), 400
    else:
        if not SETTINGS.allow_unsigned_webhooks:
            return jsonify({
                "error": "webhook_secret_missing",
                "hint": "Set RAZORPAY_WEBHOOK_SECRET in .env (from Razorpay Dashboard webhook form)",
            }), 503
        log.warning("webhook accepted unsigned (dev only) request_id=%s", g.request_id)

    try:
        payload = wh.parse_payload(body)
    except Exception:
        return jsonify({"error": "invalid_json"}), 400

    def on_captured(meta):
        result = action_executor.apply_captured_payment(meta)
        if result.get("ok") and result.get("amount_recovered"):
            state["revenue_recovered"] += float(result["amount_recovered"])
            socketio.emit("razorpay_captured", {
                "event_id": result.get("event_id"),
                "amount_recovered": result.get("amount_recovered"),
                "live_revenue_recovered": round(state["revenue_recovered"], 2),
            })
        return result

    def on_failed(meta):
        return action_executor.apply_failed_payment(meta)

    out = wh.handle_verified_event(
        payload,
        already_seen=db.webhook_already_seen,
        mark_seen=db.mark_webhook_seen,
        on_captured=on_captured,
        on_failed=on_failed,
    )
    log.info(
        "webhook handled type=%s duplicate=%s request_id=%s",
        out.get("handled") or out.get("event") or payload.get("event"),
        out.get("duplicate", False),
        g.request_id,
    )
    return jsonify(out), 200


@app.route("/api/run_recovery_batch", methods=["POST", "GET"])
@security.require_api_key_if_enabled(_settings)
@security.rate_limit(10, 60.0, prefix="batch")
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
        if live["status"] in ("recovered", "stopped", "escalated", "awaiting_payment"):
            continue

        result = agent.run_one_recovery_step(
            live,
            scores,
            outage_status,
            outage_flag,
            save_action=_persist_action,
            update_event=db.update_at_risk_event,
            add_audit=db.add_audit,
            # Batch stays simulator by default (avoid spamming Razorpay).
            # Use POST /api/cases/<id>/payment_link for real Test links.
            create_payment_link=None,
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
    log.info("Dashboard connected")


def start_background_jobs():
    if SETTINGS.enable_live_simulator:
        threading.Thread(target=simulate_loop, daemon=True, name="revene-sim").start()


if __name__ == "__main__":
    start_background_jobs()
    log.info(
        "Starting Revene on %s:%s env=%s simulator=%s",
        SETTINGS.host,
        SETTINGS.port,
        SETTINGS.app_env,
        SETTINGS.enable_live_simulator,
    )
    socketio.run(
        app,
        host=SETTINGS.host,
        port=SETTINGS.port,
        debug=False,
        allow_unsafe_werkzeug=True,
    )
