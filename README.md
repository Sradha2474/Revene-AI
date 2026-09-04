# Revene

**Predictive revenue recovery for payments that degrade, fail, or get abandoned.**

Revene detects revenue at risk, chooses a bounded intervention, and wins money back — with stopping rules and a full audit trail.

Built for [Razorpay AI Buildathon](https://razorpay.com/buildathon/) · Track **03 — AI Revenue Recovery**.

---

## Why Revene

Most recovery tools only act *after* a payment fails.  
Revene works in **two lanes**:

| Lane | When | What it does |
|------|------|----------------|
| **Preempt** | Payment is degrading (bank shaky / wrong method) | Switch or highlight a safer method *before* loss |
| **Recover** | Payment already failed | Smart retry, wait+switch, payment link, escalate, or **stop** |

ML success scores + live bank outage signals drive the decision — not blind reminder blasts.

---

## Demo (2 minutes)

```bash
pip install -r requirements.txt
python data/generate_data.py            # once
python models/train_risk_predictor.py   # once
python backend/app.py
```



**Judge path**

1. Open the console  
2. Click **simulate outage** on a bank  
3. Watch the **at-risk queue** fill  
4. Click **Run recovery batch** → read ₹ at risk vs ₹ won back  
5. Click any case → audit: detect → diagnose → decide → outcome  

---

## Architecture

```
data/           synthetic transaction history
models/         XGBoost P(success | method, bank, …)
monitor/        rolling z-score bank outage detector
engine/         route recommender (best method under outage)
backend/
  recovery_agent.py   diagnose → intervene → stop rules
  db.py               at_risk · actions · audit_log
  app.py              live loop + batch API + websockets
frontend/
  landing.html        product site
  dashboard.html      recovery console
```

---

## Track 03 bar

| Requirement | How Revene hits it |
|-------------|--------------------|
| Detect revenue at risk | Degradation score + failed txns → `at_risk_events` |
| Right intervention | Cause-specific actions in `recovery_agent.py` |
| Bounded workflow | Max 3 attempts, min amount, ROI gate, no blind outage retry |
| Measured money (batch) | `GET /api/run_recovery_batch?n=40` |
| Escalation | `escalate_human` then stop |
| Audit trail | `audit_log` + case drawer in UI |

---

## API

| Endpoint | Purpose |
|----------|---------|
| `GET /` | Landing |
| `GET /demo` | Console |
| `GET /trigger_outage/<bank>` | Inject demo outage |
| `GET /api/run_recovery_batch?n=40` | Measured batch recovery |
| `GET /api/at_risk` | Recent at-risk cases |
| `GET /api/case/<id>` | Event + actions + audit |
| `GET /api/db_stats` | Aggregates + live ₹ |

---

## Metrics on the console

- **₹ Recovered** — won back after failure  
- **₹ Preempted** — saved in the degradation window  
- **₹ Protected** — smart routing benefit  
- **Batch recovery rate** — won_back / at_risk  

---

## Stack

Python · Flask · Socket.IO · SQLite · XGBoost · Pandas  

---

## Honest demo note

Outcomes use the same model probabilities as routing so the demo stays internally consistent. In production, Razorpay webhooks / Payment Links replace the simulator; the agent policy stays the same.

---

## License

MIT — for hackathon / portfolio use.
