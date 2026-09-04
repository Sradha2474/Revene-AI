"""
Layer 4: Route Recommender
============================
WHY THIS EXISTS:
This is the actual "agent" -- the only layer that makes a decision.
Everything before it (risk predictor, outage monitor) just produces
signals. This layer combines them into one action: "for this
customer, checking out right now, which payment method should we
show first?"

HOW IT COMBINES THE SIGNALS:
1. Ask the risk predictor for a success probability for every method
   this merchant supports (card, upi, netbanking, wallet).
2. Ask the outage monitor whether the bank behind any of those methods
   is currently in a detected outage.
3. If a method's bank is in an active outage, heavily penalize that
   method's score regardless of what the ML model alone would say --
   the outage is real-time ground truth, the model is a general
   pattern learned from history, and real-time signal should win.
4. Rank methods by adjusted score, recommend the top one, and return
   the reasoning so it can be shown on the dashboard / audit log.

REAL-WORLD BENEFIT:
Instead of a customer blindly picking "Pay with Card" and hitting a
decline, the checkout page can pre-select or highlight the method
most likely to actually work for THIS customer, right now -- turning
a probable failure into a probable success, before it ever happens.
"""

OUTAGE_PENALTY = 0.5  # multiply the model's score by this if the bank is in an outage


def recommend_route(risk_scores: dict, outage_status: dict):
    """
    risk_scores: {"card": 0.81, "upi": 0.93, "netbanking": 0.70, "wallet": 0.88}
                 (success probability per method, from the risk predictor)
    outage_status: {"card": {"bank": "SBI", "outage": True}, "upi": {...}, ...}
                 (per-method outage flag, from the outage monitor, keyed by
                 whichever bank/gateway handles that method for this txn)

    Returns the recommended method plus the full ranked list with reasoning.
    """
    adjusted = {}
    reasons = {}

    for method, score in risk_scores.items():
        status = outage_status.get(method, {"outage": False})
        adj_score = score
        reason = f"predicted success probability {score:.0%}"

        if status.get("outage"):
            adj_score = score * OUTAGE_PENALTY
            reason += f" -- penalized: {status.get('bank')} is currently flagged as unstable (z={status.get('z_score')})"

        adjusted[method] = adj_score
        reasons[method] = reason

    ranked = sorted(adjusted.items(), key=lambda x: x[1], reverse=True)
    best_method, best_score = ranked[0]

    return {
        "recommended_method": best_method,
        "confidence": round(best_score, 3),
        "reasoning": reasons[best_method],
        "full_ranking": [
            {"method": m, "adjusted_score": round(s, 3), "reasoning": reasons[m]}
            for m, s in ranked
        ],
    }


if __name__ == "__main__":
    # example: card looks best on paper, but its bank is having an outage
    risk_scores = {"card": 0.90, "upi": 0.85, "netbanking": 0.70, "wallet": 0.82}
    outage_status = {
        "card": {"bank": "SBI", "outage": True, "z_score": 6.1},
        "upi": {"bank": "UPI-NPCI", "outage": False},
        "netbanking": {"bank": "SBI", "outage": True, "z_score": 6.1},
        "wallet": {"bank": "Paytm", "outage": False},
    }

    result = recommend_route(risk_scores, outage_status)
    print(f"Recommended: {result['recommended_method']} (confidence {result['confidence']:.0%})")
    print(f"Reasoning: {result['reasoning']}\n")
    print("Full ranking:")
    for r in result["full_ranking"]:
        print(f"  {r['method']}: {r['adjusted_score']:.0%} -- {r['reasoning']}")
