export type AtRiskCase = {
  id: number;
  customer_id: string;
  amount: number;
  bank: string;
  original_method?: string;
  stage: string;
  root_cause: string;
  status: string;
  attempts: number;
  amount_recovered?: number;
  degradation_score?: number;
  created_at?: string;
};

export type BankHealth = {
  bank: string;
  z_score: number;
  status: "HEALTHY" | "DEGRADED" | "OUTAGE" | string;
  avoid_retry_same_route?: boolean;
  recent_failure_rate?: number | null;
  baseline_failure_rate?: number | null;
};

export type Approval = {
  id: number;
  event_id: number;
  recommended_action: string;
  reason: string;
  status: string;
  created_at?: string;
};

export type TxnFeedItem = {
  id: string;
  customer_id?: string;
  amount: number;
  bank: string;
  recommended_method?: string;
  success: boolean;
  degradation_score?: number;
  ts: number;
};

export type ToastItem = {
  id: string;
  title: string;
  detail?: string;
  href?: string;
};
