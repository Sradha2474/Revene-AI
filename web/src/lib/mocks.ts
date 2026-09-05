import type { AtRiskCase, BankHealth, Approval, TxnFeedItem } from "./types";

export const MOCK_BANKS: BankHealth[] = [
  { bank: "HDFC", z_score: 0.4, status: "HEALTHY" },
  { bank: "SBI", z_score: 2.1, status: "DEGRADED" },
  { bank: "ICICI", z_score: 0.2, status: "HEALTHY" },
  { bank: "Axis", z_score: 3.1, status: "OUTAGE" },
  { bank: "Kotak", z_score: 0.6, status: "HEALTHY" },
  { bank: "PNB", z_score: 1.1, status: "HEALTHY" },
];

export const MOCK_CASES: AtRiskCase[] = [
  {
    id: 101,
    customer_id: "cust_2041",
    amount: 2499,
    bank: "SBI",
    stage: "failed",
    root_cause: "bank_degrading",
    status: "open",
    attempts: 0,
  },
  {
    id: 102,
    customer_id: "cust_881",
    amount: 12999,
    bank: "Axis",
    stage: "failed",
    root_cause: "bank_outage",
    status: "awaiting_approval",
    attempts: 1,
  },
  {
    id: 103,
    customer_id: "cust_552",
    amount: 799,
    bank: "HDFC",
    stage: "degrading",
    root_cause: "wrong_method_risk",
    status: "recovering",
    attempts: 1,
  },
];

export const MOCK_APPROVALS: Approval[] = [
  {
    id: 1,
    event_id: 102,
    recommended_action: "send_payment_link",
    reason: "High-value ₹12999 requires human approval",
    status: "pending",
  },
];

export const MOCK_FEED: TxnFeedItem[] = [
  {
    id: "m1",
    amount: 1200,
    bank: "HDFC",
    recommended_method: "upi",
    success: true,
    degradation_score: 0.12,
    ts: Date.now() - 4000,
  },
  {
    id: "m2",
    amount: 3400,
    bank: "SBI",
    recommended_method: "card",
    success: false,
    degradation_score: 0.71,
    ts: Date.now() - 2000,
  },
];
