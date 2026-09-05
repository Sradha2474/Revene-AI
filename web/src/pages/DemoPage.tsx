import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { api } from "@/lib/api";
import { getSocket } from "@/lib/socket";
import { MOCK_APPROVALS, MOCK_BANKS, MOCK_CASES, MOCK_FEED } from "@/lib/mocks";
import type { Approval, AtRiskCase, BankHealth, ToastItem, TxnFeedItem } from "@/lib/types";
import { formatInr, cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { BankHealthPanel } from "@/components/console/BankHealthPanel";
import { BatchPanel, type BatchResult } from "@/components/console/BatchPanel";
import { RazorpayPanel } from "@/components/console/RazorpayPanel";
import { StoppingRules } from "@/components/console/StoppingRules";
import { StrategySimulator } from "@/components/console/StrategySimulator";
import { LiveFeed } from "@/components/console/LiveFeed";
import { AtRiskQueue } from "@/components/console/AtRiskQueue";
import { CaseDrawer } from "@/components/console/CaseDrawer";
import { ApprovalsInbox } from "@/components/console/ApprovalsInbox";
import { ToastStack } from "@/components/console/ToastStack";

type Tab = "console" | "approvals";

type Metrics = {
  recovered: number;
  preempted: number;
  protected: number;
  txnCount: number;
  batchRate: number | null;
  batchSub: string;
};

const INITIAL_METRICS: Metrics = {
  recovered: 0,
  preempted: 0,
  protected: 0,
  txnCount: 0,
  batchRate: null,
  batchSub: "Run a batch to measure",
};

export default function DemoPage({ initialTab }: { initialTab?: Tab } = {}) {
  const { id: caseIdParam } = useParams<{ id?: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const tabFromSearch = searchParams.get("tab");
  const tab: Tab =
    initialTab === "approvals" || tabFromSearch === "approvals" ? "approvals" : "console";

  const selectedId = useMemo(() => {
    if (!caseIdParam) return null;
    const n = Number(caseIdParam);
    return Number.isFinite(n) ? n : null;
  }, [caseIdParam]);

  const [connected, setConnected] = useState(false);
  const [banks, setBanks] = useState<BankHealth[]>(MOCK_BANKS);
  const [cases, setCases] = useState<AtRiskCase[]>(MOCK_CASES);
  const [feed, setFeed] = useState<TxnFeedItem[]>(MOCK_FEED);
  const [approvals, setApprovals] = useState<Approval[]>(MOCK_APPROVALS);
  const [metrics, setMetrics] = useState<Metrics>(INITIAL_METRICS);
  const [rzpStatus, setRzpStatus] = useState<{
    configured: boolean;
    webhook_secret_configured: boolean;
    mode: string;
    hint: string;
  } | null>(null);
  const [auditOk, setAuditOk] = useState<boolean | null>(null);
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const [isLg, setIsLg] = useState(
    () => typeof window !== "undefined" && window.matchMedia("(min-width: 1024px)").matches,
  );
  const toastTimers = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

  useEffect(() => {
    const mq = window.matchMedia("(min-width: 1024px)");
    const onChange = () => setIsLg(mq.matches);
    onChange();
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  const pushToast = useCallback((toast: Omit<ToastItem, "id"> & { id?: string }) => {
    const id = toast.id || `t-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    setToasts((prev) => [{ ...toast, id }, ...prev].slice(0, 5));
    const existing = toastTimers.current.get(id);
    if (existing) clearTimeout(existing);
    toastTimers.current.set(
      id,
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
        toastTimers.current.delete(id);
      }, 6000),
    );
  }, []);

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
    const t = toastTimers.current.get(id);
    if (t) clearTimeout(t);
    toastTimers.current.delete(id);
  }, []);

  const refreshCases = useCallback(async () => {
    try {
      const rows = await api.atRisk();
      if (Array.isArray(rows)) setCases(rows);
    } catch {
      /* keep mocks / last good */
    }
  }, []);

  const refreshBanks = useCallback(async () => {
    try {
      const data = await api.paymentHealth();
      if (data?.banks?.length) setBanks(data.banks);
    } catch {
      /* keep mocks */
    }
  }, []);

  const refreshApprovals = useCallback(async () => {
    try {
      const rows = await api.approvals();
      if (Array.isArray(rows)) setApprovals(rows);
    } catch {
      /* keep mocks */
    }
  }, []);

  const refreshStats = useCallback(async () => {
    try {
      const s = await api.dbStats();
      setMetrics((m) => ({
        ...m,
        recovered: Number(s.live_revenue_recovered ?? m.recovered),
        preempted: Number(s.live_revenue_preempted ?? m.preempted),
        protected: Number(s.live_revenue_protected ?? m.protected),
      }));
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    void refreshStats();
    void refreshCases();
    void refreshBanks();
    void refreshApprovals();

    api
      .razorpayStatus()
      .then(setRzpStatus)
      .catch(() => setRzpStatus(null));

    api
      .auditVerify()
      .then((r) => setAuditOk(!!r.ok))
      .catch(() => setAuditOk(null));
  }, [refreshApprovals, refreshBanks, refreshCases, refreshStats]);

  useEffect(() => {
    const socket = getSocket();

    const onConnect = () => setConnected(true);
    const onDisconnect = () => setConnected(false);

    const onTransaction = (data: {
      customer_id?: string;
      amount?: number;
      bank?: string;
      recommended_method?: string;
      success?: boolean;
      degradation_score?: number;
      revenue_recovered?: number;
      revenue_preempted?: number;
      revenue_protected?: number;
      transactions_processed?: number;
      active_outage_banks?: string[];
      recovery?: { event_id?: number; action?: string; lane?: string };
    }) => {
      setMetrics((m) => ({
        ...m,
        recovered: Number(data.revenue_recovered ?? m.recovered),
        preempted: Number(data.revenue_preempted ?? m.preempted),
        protected: Number(data.revenue_protected ?? m.protected),
        txnCount: Number(data.transactions_processed ?? m.txnCount + 1),
      }));

      if (data.active_outage_banks) {
        const outages = new Set(data.active_outage_banks);
        setBanks((prev) =>
          prev.map((b) => ({
            ...b,
            status: outages.has(b.bank) ? "OUTAGE" : b.status === "OUTAGE" ? "HEALTHY" : b.status,
          })),
        );
      }

      setFeed((prev) =>
        [
          {
            id: `live-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
            customer_id: data.customer_id,
            amount: Number(data.amount || 0),
            bank: data.bank || "—",
            recommended_method: data.recommended_method,
            success: !!data.success,
            degradation_score: data.degradation_score,
            ts: Date.now(),
          },
          ...prev,
        ].slice(0, 40),
      );

      if (data.recovery?.event_id) {
        void refreshCases();
      }
    };

    const onBatchComplete = (data: BatchResult & Record<string, unknown>) => {
      const rate = Math.round((Number(data.recovery_rate) || 0) * 100);
      setMetrics((m) => ({
        ...m,
        recovered: Number(data.live_revenue_recovered ?? data.amount_recovered ?? m.recovered),
        preempted: Number(data.live_revenue_preempted ?? data.amount_preempted ?? m.preempted),
        batchRate: rate,
        batchSub: `${formatInr(data.amount_won_back)} of ${formatInr(data.amount_at_risk)} at risk`,
      }));
      pushToast({
        title: "Batch complete",
        detail: `${rate}% · ${formatInr(data.amount_won_back)} won back`,
      });
      void refreshCases();
    };

    const onPaymentLink = (data?: { event_id?: number; short_url?: string }) => {
      pushToast({
        title: "Payment link created",
        detail: data?.short_url || (data?.event_id ? `Case #${data.event_id}` : undefined),
        href: data?.event_id ? `/demo/cases/${data.event_id}` : undefined,
      });
      void refreshCases();
    };

    const onCaptured = (data: {
      live_revenue_recovered?: number;
      event_id?: number;
      amount?: number;
    }) => {
      if (data.live_revenue_recovered != null) {
        setMetrics((m) => ({ ...m, recovered: Number(data.live_revenue_recovered) }));
      }
      pushToast({
        title: "Razorpay captured",
        detail: data.amount != null ? formatInr(data.amount) : "Payment credited",
        href: data.event_id ? `/demo/cases/${data.event_id}` : undefined,
      });
      void refreshCases();
      void refreshStats();
    };

    socket.on("connect", onConnect);
    socket.on("disconnect", onDisconnect);
    socket.on("transaction", onTransaction);
    socket.on("batch_complete", onBatchComplete);
    socket.on("payment_link_created", onPaymentLink);
    socket.on("razorpay_captured", onCaptured);

    if (socket.connected) setConnected(true);

    return () => {
      socket.off("connect", onConnect);
      socket.off("disconnect", onDisconnect);
      socket.off("transaction", onTransaction);
      socket.off("batch_complete", onBatchComplete);
      socket.off("payment_link_created", onPaymentLink);
      socket.off("razorpay_captured", onCaptured);
    };
  }, [pushToast, refreshCases, refreshStats]);

  useEffect(() => {
    return () => {
      toastTimers.current.forEach((t) => clearTimeout(t));
      toastTimers.current.clear();
    };
  }, []);

  function setTab(next: Tab) {
    if (next === "approvals") {
      if (initialTab === "approvals" || window.location.pathname === "/demo/approvals") {
        navigate("/demo/approvals");
      } else {
        setSearchParams({ tab: "approvals" });
      }
      return;
    }
    if (selectedId != null) {
      navigate(`/demo/cases/${selectedId}`);
    } else {
      navigate("/demo");
    }
  }

  function selectCase(id: number) {
    navigate(`/demo/cases/${id}`);
  }

  function closeCase() {
    if (tab === "approvals") {
      navigate("/demo/approvals");
    } else {
      navigate("/demo");
    }
  }

  function onBatchComplete(data: BatchResult) {
    const rate = Math.round((data.recovery_rate || 0) * 100);
    setMetrics((m) => ({
      ...m,
      recovered: Number(data.live_revenue_recovered ?? data.amount_recovered ?? m.recovered),
      preempted: Number(data.live_revenue_preempted ?? data.amount_preempted ?? m.preempted),
      batchRate: rate,
      batchSub: `${formatInr(data.amount_won_back)} of ${formatInr(data.amount_at_risk)} at risk`,
    }));
    void refreshCases();
  }

  const selectedCase = cases.find((c) => c.id === selectedId) || null;
  const anyOutage = banks.some((b) => String(b.status).toUpperCase() === "OUTAGE");

  return (
    <div className="flex min-h-screen flex-col bg-[#07090f] text-[var(--color-fg)]">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 bg-[#0a0d17]/80 px-4 py-3 backdrop-blur-md md:px-6">
        <div className="flex min-w-0 items-center gap-5">
          <Link to="/" className="flex items-center gap-2 group">
            <span className="flex size-7 items-center justify-center rounded-lg bg-gradient-to-br from-sky-400 to-blue-600 font-bold text-white text-xs shadow-[0_0_12px_rgba(14,165,233,0.4)]">
              R
            </span>
            <span className="font-heading text-sm font-bold tracking-tight text-white group-hover:text-sky-300 transition-colors">
              Revene
            </span>
            <span className="hidden sm:inline-block rounded-full bg-white/5 border border-white/10 px-2 py-0.5 text-[10px] font-mono text-zinc-400">
              CONSOLE
            </span>
          </Link>
          <nav className="flex gap-1 rounded-lg bg-white/5 p-0.5 border border-white/10 text-xs">
            <button
              type="button"
              onClick={() => setTab("console")}
              className={cn(
                "rounded-md px-3 py-1 font-medium transition-all",
                tab === "console" ? "bg-sky-500 text-white shadow-[0_0_10px_rgba(14,165,233,0.4)]" : "text-zinc-400 hover:text-white",
              )}
            >
              Console
            </button>
            <button
              type="button"
              onClick={() => setTab("approvals")}
              className={cn(
                "rounded-md px-3 py-1 font-medium transition-all",
                tab === "approvals" ? "bg-sky-500 text-white shadow-[0_0_10px_rgba(14,165,233,0.4)]" : "text-zinc-400 hover:text-white",
              )}
            >
              Approvals
            </button>
          </nav>
        </div>
        <div className="flex flex-wrap items-center gap-2.5">
          <span className="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-xs text-zinc-300">
            <span
              className={cn(
                "inline-block size-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.7)]",
                !connected && "bg-zinc-600 shadow-none",
                connected && anyOutage && "bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.7)] animate-pulse",
              )}
            />
            {connected ? (anyOutage ? "Live · Outage Detected" : "Live · Telemetry OK") : "Offline"}
          </span>
          <Badge tone="neutral">Test Mode</Badge>
          <Badge tone={rzpStatus?.configured ? "ok" : "bad"}>
            {rzpStatus?.configured ? `Razorpay ${rzpStatus.mode}` : "Razorpay Keys"}
          </Badge>
          <Badge tone={auditOk === true ? "ok" : auditOk === false ? "bad" : "neutral"}>
            {auditOk === true ? "Audit Verified" : auditOk === false ? "Audit Broken" : "Audit —"}
          </Badge>
        </div>
      </header>

      {tab === "console" ? (
        <>
          <div className="sticky top-0 z-30 grid grid-cols-2 border-b border-white/10 bg-[#090c15] shadow-lg lg:grid-cols-4">
            {[
              {
                label: "₹ Recovered",
                value: formatInr(metrics.recovered),
                sub: "after failure",
                border: "border-t-2 border-emerald-500/80",
                tone: "text-emerald-400 drop-shadow-[0_0_12px_rgba(16,185,129,0.3)]",
                bg: "bg-gradient-to-b from-emerald-500/[0.04] to-transparent",
              },
              {
                label: "₹ Preempted",
                value: formatInr(metrics.preempted),
                sub: "before failure",
                border: "border-t-2 border-sky-400/80",
                tone: "text-sky-400 drop-shadow-[0_0_12px_rgba(56,189,248,0.3)]",
                bg: "bg-gradient-to-b from-sky-500/[0.04] to-transparent",
              },
              {
                label: "₹ Protected",
                value: formatInr(metrics.protected),
                sub: `${metrics.txnCount} transactions`,
                border: "border-t-2 border-indigo-400/80",
                tone: "text-indigo-300",
                bg: "bg-gradient-to-b from-indigo-500/[0.04] to-transparent",
              },
              {
                label: "Batch Recovery Rate",
                value: metrics.batchRate != null ? `${metrics.batchRate}%` : "—",
                sub: metrics.batchSub,
                border: "border-t-2 border-amber-400/80",
                tone: "text-amber-400",
                bg: "bg-gradient-to-b from-amber-500/[0.04] to-transparent",
              },
            ].map((m) => (
              <div
                key={m.label}
                className={cn(
                  "border-b border-white/10 px-5 py-4 lg:border-b-0 lg:border-r lg:last:border-r-0 transition-colors",
                  m.border,
                  m.bg,
                )}
              >
                <p className="mb-1 text-[11px] font-mono uppercase tracking-wider text-zinc-400">{m.label}</p>
                <p className={cn("mono text-2xl font-bold tracking-tight", m.tone)}>{m.value}</p>
                <p className="mt-1 text-[11px] text-zinc-500">{m.sub}</p>
              </div>
            ))}
          </div>

          <div className="grid min-h-0 flex-1 lg:grid-cols-[280px_minmax(0,1fr)_320px]">
            <aside className="max-h-[50vh] overflow-auto border-b border-white/10 bg-[#080b13] lg:max-h-none lg:border-b-0 lg:border-r">
              <BankHealthPanel banks={banks} onRefresh={refreshBanks} />
              <BatchPanel onComplete={onBatchComplete} />
              <RazorpayPanel
                selectedCase={selectedCase}
                cases={cases}
                status={rzpStatus}
                onLinkCreated={refreshCases}
              />
              <StoppingRules />
              <StrategySimulator />
            </aside>

            <div className="flex min-h-[50vh] flex-col lg:min-h-0 lg:h-[calc(100vh-8.5rem)]">
              <LiveFeed items={feed} />
              <AtRiskQueue cases={cases} selectedId={selectedId} onSelect={selectCase} />
            </div>

            {isLg ? (
              <aside className="min-h-0 border-l border-[var(--color-line)] lg:h-[calc(100vh-8.5rem)]">
                <CaseDrawer caseId={selectedId} onClose={closeCase} onUpdated={refreshCases} />
              </aside>
            ) : null}
          </div>

          {!isLg && selectedId != null ? (
            <div className="fixed inset-0 z-50">
              <button
                type="button"
                aria-label="Close drawer backdrop"
                className="absolute inset-0 bg-black/55"
                onClick={closeCase}
              />
              <div className="absolute inset-y-0 right-0 w-full max-w-md border-l border-[var(--color-line)] bg-[var(--color-ink)] shadow-xl">
                <CaseDrawer
                  caseId={selectedId}
                  onClose={closeCase}
                  onUpdated={refreshCases}
                  showClose
                />
              </div>
            </div>
          ) : null}
        </>
      ) : (
        <ApprovalsInbox approvals={approvals} onChanged={refreshApprovals} />
      )}

      <ToastStack toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
}
