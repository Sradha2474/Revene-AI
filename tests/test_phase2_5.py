"""Unit tests for Phase 2–5 backend (no frontend, no Razorpay network)."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.join(os.path.dirname(__file__), "..")
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, BACKEND)
sys.path.insert(0, os.path.join(ROOT, "engine"))
sys.path.insert(0, os.path.join(ROOT, "monitor"))


class TestFailureClassifier(unittest.TestCase):
    def test_known_code(self):
        import failure_classifier as fc
        out = fc.classify_failure(error_code="INSUFFICIENT_FUNDS")
        self.assertTrue(out["known"])
        self.assertEqual(out["failure_category"], "INSUFFICIENT_FUNDS")
        self.assertEqual(out["side"], "customer")

    def test_outage_overrides(self):
        import failure_classifier as fc
        out = fc.classify_failure(error_code="NETWORK_ERROR", outage=True)
        self.assertEqual(out["failure_category"], "BANK_DECLINED")
        self.assertTrue(out["recoverable"])

    def test_unknown(self):
        import failure_classifier as fc
        out = fc.classify_failure(error_code="WEIRD_XYZ")
        self.assertFalse(out["known"])
        self.assertEqual(out["failure_category"], "UNKNOWN_ERROR")

    def test_root_cause_map(self):
        import failure_classifier as fc
        out = fc.classify_failure(root_cause="bank_outage")
        self.assertEqual(out["failure_category"], "BANK_DECLINED")


class TestFatigue(unittest.TestCase):
    def test_low(self):
        import fatigue
        f = fatigue.calculate_fatigue(retry_attempts=0, interventions=0)
        self.assertEqual(f["fatigue_level"], "LOW")
        self.assertFalse(f["should_stop"])

    def test_high_stops(self):
        import fatigue
        f = fatigue.calculate_fatigue(retry_attempts=3, interventions=2, recent_failures=3)
        self.assertEqual(f["fatigue_level"], "HIGH")
        self.assertTrue(f["should_stop"])


class TestPaymentHealth(unittest.TestCase):
    def test_healthy(self):
        import payment_health as ph
        h = ph.route_health(bank="HDFC", z_score=0.2, outage=False)
        self.assertEqual(h["status"], "HEALTHY")
        self.assertFalse(h["avoid_retry_same_route"])

    def test_outage(self):
        import payment_health as ph
        h = ph.route_health(bank="SBI", z_score=3.0, outage=True)
        self.assertEqual(h["status"], "OUTAGE")
        self.assertTrue(h["avoid_retry_same_route"])


class TestPolicyEngine(unittest.TestCase):
    def _base(self, **kw):
        d = {
            "recommended_action": "send_payment_link",
            "amount": 500,
            "retry_count": 0,
            "recovery_probability": 0.9,
            "force_stop": False,
            "failure": {"known": True, "recoverable": True, "failure_category": "BANK_DECLINED"},
            "fatigue": {"fatigue_level": "LOW"},
            "payment_health": {"avoid_retry_same_route": False},
        }
        d.update(kw)
        return d

    def test_green(self):
        import policy_engine as pe
        p = pe.evaluate_policy(self._base())
        self.assertEqual(p["traffic_light"], "GREEN")

    def test_red_unknown(self):
        import policy_engine as pe
        p = pe.evaluate_policy(self._base(
            failure={"known": False, "recoverable": False, "failure_category": "UNKNOWN_ERROR"},
        ))
        self.assertEqual(p["traffic_light"], "RED")

    def test_yellow_high_value(self):
        import policy_engine as pe
        p = pe.evaluate_policy(self._base(amount=15000, recovery_probability=0.95))
        self.assertEqual(p["traffic_light"], "YELLOW")

    def test_red_fatigue(self):
        import policy_engine as pe
        p = pe.evaluate_policy(self._base(fatigue={"fatigue_level": "HIGH"}))
        self.assertEqual(p["traffic_light"], "RED")

    def test_degraded_retry_becomes_yellow_link(self):
        import policy_engine as pe
        p = pe.evaluate_policy(self._base(
            recommended_action="smart_retry",
            payment_health={"avoid_retry_same_route": True},
            recovery_probability=0.9,
        ))
        self.assertEqual(p["traffic_light"], "YELLOW")
        self.assertEqual(p["approved_action"], "send_payment_link")


class TestSimulator(unittest.TestCase):
    def test_thresholds(self):
        import simulator
        cases = [
            {"amount": 100, "recovery_probability": 0.9},
            {"amount": 200, "recovery_probability": 0.5},
        ]
        out = simulator.simulate_threshold_strategies(cases, [0.7, 0.85])
        self.assertEqual(out["case_count"], 2)
        self.assertEqual(len(out["strategies"]), 2)
        # only first case clears 0.7
        self.assertEqual(out["strategies"][0]["actions_taken"], 1)


class TestWebhookIdempotency(unittest.TestCase):
    def test_verify_signature(self):
        import webhooks as wh
        os.environ["RAZORPAY_WEBHOOK_SECRET"] = "test_secret"
        body = b'{"event":"payment.captured"}'
        sig = hmac.new(b"test_secret", body, hashlib.sha256).hexdigest()
        self.assertTrue(wh.verify_signature(body, sig))
        self.assertFalse(wh.verify_signature(body, "bad"))

    def test_duplicate_event_skipped(self):
        import webhooks as wh
        seen = set()

        def already_seen(eid):
            return eid in seen

        def mark_seen(eid, etype, payload):
            seen.add(eid)

        payload = {
            "event": "payment.captured",
            "event_id": "evt_dup_1",
            "payload": {"payment": {"entity": {"id": "pay_1", "amount": 10000, "notes": {}}}},
        }
        r1 = wh.handle_verified_event(
            payload,
            already_seen=already_seen,
            mark_seen=mark_seen,
            on_captured=lambda m: {"ok": True},
            on_failed=lambda m: {"ok": True},
        )
        r2 = wh.handle_verified_event(
            payload,
            already_seen=already_seen,
            mark_seen=mark_seen,
            on_captured=lambda m: {"ok": True},
            on_failed=lambda m: {"ok": True},
        )
        self.assertTrue(r1.get("ok") and r1.get("handled") == "payment.captured")
        self.assertTrue(r2.get("duplicate"))


class TestAuditChain(unittest.TestCase):
    def setUp(self):
        import db
        self._old = db.DB_PATH
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        db.DB_PATH = path
        db.init_db()
        self.db = db
        self.path = path

    def tearDown(self):
        self.db.DB_PATH = self._old
        try:
            os.remove(self.path)
        except OSError:
            pass

    def test_chain_ok(self):
        self.db.append_audit_chain(1, "test", '{"a":1}')
        self.db.append_audit_chain(1, "test", '{"a":2}')
        v = self.db.verify_audit_chain()
        self.assertTrue(v["ok"])
        self.assertEqual(v["entries"], 2)


if __name__ == "__main__":
    unittest.main()
