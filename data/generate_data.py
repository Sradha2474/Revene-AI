"""
Layer 1: Synthetic Data Generator
==================================
WHY THIS EXISTS:
Razorpay test mode won't give you real historical failure patterns
(no real bank behaviour, no real customer history). So we simulate a
realistic transaction history that a merchant would actually have
after a few months live -- customer_id, payment method, bank/gateway,
amount, time of day, and whether it succeeded or failed.

The realism comes from BUILT-IN PATTERNS (not random noise):
  - Each bank has a baseline failure rate (some banks are just flakier)
  - Netbanking fails more at night (banks run maintenance windows)
  - High amounts fail more often on cards (risk holds, insufficient funds)
  - Repeat customers on a method that failed them before are more likely
    to fail again on that same method (real behavioural signal)
  - A random 2-hour "outage window" is injected for one bank, where its
    failure rate spikes to ~85%. This is what your outage monitor is
    built to catch, and what you'll replay live in the demo.

Run: python generate_data.py
Output: transactions.csv in this folder
"""

import pandas as pd
import numpy as np

np.random.seed(42)

N_TRANSACTIONS = 20000
BANKS = ["HDFC", "SBI", "ICICI", "Axis", "Kotak", "PNB"]
METHODS = ["card", "upi", "netbanking", "wallet"]

# Each bank's baseline failure rate -- some banks are just less reliable
BANK_BASE_FAILURE_RATE = {"HDFC": 0.06, "SBI": 0.11, "ICICI": 0.07,
                           "Axis": 0.09, "Kotak": 0.08, "PNB": 0.13}

# Each method's baseline failure rate
METHOD_BASE_FAILURE_RATE = {"card": 0.10, "upi": 0.04, "netbanking": 0.09, "wallet": 0.05}

# Pick a random 2-hour outage window for one bank, in the last day of data
OUTAGE_BANK = "SBI"
OUTAGE_START_TXN = int(N_TRANSACTIONS * 0.95)   # near the end -> "recent" outage
OUTAGE_LEN_TXN = 150                             # roughly a burst window

rows = []
customer_history = {}  # customer_id -> {method: [outcomes]}

for i in range(N_TRANSACTIONS):
    customer_id = f"cust_{np.random.randint(1, 4000)}"
    method = np.random.choice(METHODS, p=[0.35, 0.40, 0.15, 0.10])
    bank = np.random.choice(BANKS)
    amount = round(np.random.lognormal(mean=6.5, sigma=1.0), 2)  # skewed, mostly small amounts
    hour = np.random.randint(0, 24)
    day_of_week = np.random.randint(0, 7)

    # base failure probability from bank + method
    fail_prob = 1 - (1 - BANK_BASE_FAILURE_RATE[bank]) * (1 - METHOD_BASE_FAILURE_RATE[method])

    # night-time netbanking maintenance windows fail more
    if method == "netbanking" and (hour >= 1 and hour <= 4):
        fail_prob += 0.20

    # high amount cards fail more (risk holds / insufficient funds)
    if method == "card" and amount > 8000:
        fail_prob += 0.15

    # repeat-failure behavioural signal: if this customer's last attempt
    # on this method failed, they're more likely to fail again on it
    hist = customer_history.setdefault(customer_id, {})
    past_outcomes = hist.get(method, [])
    if past_outcomes and past_outcomes[-1] == 0:
        fail_prob += 0.18

    # the injected outage window
    is_outage_injected = False
    if bank == OUTAGE_BANK and OUTAGE_START_TXN <= i < OUTAGE_START_TXN + OUTAGE_LEN_TXN:
        fail_prob = 0.85
        is_outage_injected = True

    fail_prob = min(fail_prob, 0.95)
    success = np.random.rand() > fail_prob
    outcome = 1 if success else 0

    if not success:
        reason = np.random.choice(
            ["insufficient_funds", "bank_timeout", "card_declined", "network_error"],
            p=[0.30, 0.30, 0.25, 0.15]
        )
    else:
        reason = None

    hist.setdefault(method, []).append(outcome)

    rows.append({
        "txn_id": i,
        "customer_id": customer_id,
        "method": method,
        "bank": bank,
        "amount": amount,
        "hour": hour,
        "day_of_week": day_of_week,
        "past_failures_this_method": sum(1 for o in past_outcomes if o == 0),
        "success": outcome,
        "failure_reason": reason,
        "is_outage_injected": is_outage_injected,
    })

import os

df = pd.DataFrame(rows)
output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "transactions.csv")
df.to_csv(output_path, index=False)

print(f"Generated {len(df)} transactions")
print(f"Overall failure rate: {(1 - df['success'].mean()):.1%}")
print(f"\nFailure rate by bank:\n{(1 - df.groupby('bank')['success'].mean()).sort_values(ascending=False)}")
print(f"\nFailure rate by method:\n{(1 - df.groupby('method')['success'].mean()).sort_values(ascending=False)}")
print(f"\nOutage window rows: {df['is_outage_injected'].sum()} (SBI, failure rate {(1 - df[df['is_outage_injected']]['success'].mean()):.1%})")


