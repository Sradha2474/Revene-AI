async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  const text = await res.text();
  let data: unknown = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { raw: text };
  }
  if (!res.ok) {
    const err = data as { error?: string; hint?: string };
    throw new Error(err?.error || err?.hint || `HTTP ${res.status}`);
  }
  return data as T;
}

export const api = {
  dbStats: () => request<Record<string, number>>("/api/db_stats"),
  atRisk: () => request<import("./types").AtRiskCase[]>("/api/at_risk"),
  caseDetail: (id: number) =>
    request<{
      event: import("./types").AtRiskCase;
      actions: unknown[];
      audit: { step: string; detail: string; created_at?: string }[];
      payment_links?: { short_url?: string; status?: string; razorpay_link_id?: string }[];
      decision?: unknown;
    }>(`/api/case/${id}`),
  investigate: (id: number) =>
    request<{ decision: Record<string, unknown>; policy: Record<string, unknown> }>(
      `/api/cases/${id}/investigate`,
      { method: "POST" },
    ),
  paymentLink: (id: number) =>
    request<{
      ok?: boolean;
      short_url?: string;
      razorpay_link_id?: string;
      error?: string;
      pipeline?: unknown;
    }>(`/api/cases/${id}/payment_link`, { method: "POST" }),
  approvals: () => request<import("./types").Approval[]>("/api/approvals"),
  decideApproval: (id: number, status: "approved" | "rejected") =>
    request(`/api/approvals/${id}/decide`, {
      method: "POST",
      body: JSON.stringify({ status }),
    }),
  paymentHealth: () =>
    request<{ banks: import("./types").BankHealth[]; active_outages: string[] }>(
      "/api/payment_health",
    ),
  simulate: () =>
    request<{
      case_count: number;
      strategies: {
        name: string;
        threshold: number;
        expected_recovery: number;
        actions_taken: number;
        skipped: number;
      }[];
    }>("/api/simulate_strategies"),
  runBatch: () =>
    request<{
      amount_at_risk: number;
      amount_won_back: number;
      recovery_rate: number;
      amount_recovered: number;
      amount_preempted: number;
      batch_size: number;
    }>("/api/run_recovery_batch"),
  razorpayStatus: () =>
    request<{
      configured: boolean;
      webhook_secret_configured: boolean;
      mode: string;
      hint: string;
      live_simulator?: boolean;
    }>("/api/razorpay/status"),
  auditVerify: () =>
    request<{ ok: boolean; entries: number; tip_hash?: string }>("/api/audit/verify"),
  triggerOutage: (bank: string) => request(`/trigger_outage/${encodeURIComponent(bank)}`),
};
