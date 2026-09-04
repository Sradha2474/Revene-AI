"""
Layer 3: Outage Monitor
========================
WHY THIS EXISTS:
A single failed transaction doesn't mean a bank is down -- it just
means that one payment failed. An outage is a PATTERN: a bank's
failure rate over the last N transactions suddenly jumping way above
its own normal baseline.

WHY THIS IS *NOT* ML:
This is a deliberate design choice, and a good talking point for
"AI judgment" -- outage detection is a well-understood statistics
problem (control charts / anomaly detection), not a prediction
problem. Using an LLM or a trained model here would be slower, less
transparent, and wouldn't do the job any better than a rolling
z-score. Use the simplest tool that solves the problem correctly.

HOW IT WORKS:
For each bank, keep a rolling window of the last WINDOW_SIZE outcomes.
Compare the recent failure rate to that bank's known historical
baseline. If it's statistically far above baseline (z-score over a
threshold) AND the window has enough data to be meaningful, flag it
as a likely outage.

REAL-WORLD BENEFIT:
Merchants currently find out about a gateway/bank outage only when
enough customers complain or someone checks a dashboard manually.
This catches it within a handful of transactions, automatically, and
can reroute new transactions away from the affected bank/method
before more customers hit the same failure.
"""

from collections import deque
import math

WINDOW_SIZE = 20          # how many recent transactions per bank to watch
MIN_SAMPLES = 8           # don't judge on too little data
Z_SCORE_THRESHOLD = 2.5   # how many std-deviations above baseline counts as an outage


class OutageMonitor:
    def __init__(self, bank_baseline_failure_rates: dict):
        """
        bank_baseline_failure_rates: e.g. {"HDFC": 0.06, "SBI": 0.11, ...}
        In production this would be computed from a longer rolling history
        (e.g. the last 30 days) rather than hardcoded.
        """
        self.baselines = bank_baseline_failure_rates
        self.windows = {bank: deque(maxlen=WINDOW_SIZE) for bank in bank_baseline_failure_rates}
        self.active_outages = set()

    def record(self, bank: str, success: bool):
        """Call this for every transaction outcome as it happens."""
        if bank not in self.windows:
            self.windows[bank] = deque(maxlen=WINDOW_SIZE)
            self.baselines[bank] = 0.10  # sane default

        self.windows[bank].append(0 if success else 1)  # 1 = failure
        return self._check(bank)

    def _check(self, bank: str):
        window = self.windows[bank]
        if len(window) < MIN_SAMPLES:
            return {"bank": bank, "outage": False, "reason": "insufficient_data", "z_score": 0.0}

        baseline = self.baselines.get(bank, 0.10)
        recent_failure_rate = sum(window) / len(window)

        # standard error of a proportion, guarded against zero
        n = len(window)
        se = math.sqrt(max(baseline * (1 - baseline), 1e-6) / n)
        z = (recent_failure_rate - baseline) / se if se > 0 else 0

        is_outage = z > Z_SCORE_THRESHOLD

        if is_outage and bank not in self.active_outages:
            self.active_outages.add(bank)
        elif not is_outage and bank in self.active_outages and z < 1.5:
            self.active_outages.discard(bank)  # recovered when z drops below 1.5

        return {
            "bank": bank,
            "outage": bank in self.active_outages,
            "recent_failure_rate": round(recent_failure_rate, 3),
            "baseline_failure_rate": round(baseline, 3),
            "z_score": round(z, 2),
        }


if __name__ == "__main__":
    # quick self-test: simulate a healthy bank, then inject an outage burst
    baselines = {"HDFC": 0.06, "SBI": 0.11}
    monitor = OutageMonitor(baselines)

    import random
    random.seed(1)
    print("-- Normal traffic for SBI --")
    for i in range(15):
        success = random.random() > baselines["SBI"]
        result = monitor.record("SBI", success)
    print(result)

    print("\n-- Injecting an outage burst for SBI (85% failure) --")
    for i in range(15):
        success = random.random() > 0.85
        result = monitor.record("SBI", success)
    print(result)
