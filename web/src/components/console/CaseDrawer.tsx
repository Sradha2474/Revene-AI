import { useCallback, useEffect, useState } from "react";
import { Copy, X } from "lucide-react";
import { api } from "@/lib/api";
import type { AtRiskCase } from "@/lib/types";
import { formatInr, shortId } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { PolicyLight } from "@/components/ui/badge";

type CaseDetail = {
  event: AtRiskCase;
  actions: unknown[];
  audit: { step: string; detail: string; created_at?: string }[];
  payment_links?: { short_url?: string; status?: string; razorpay_link_id?: string }[];
  decision?: unknown;
};

export function CaseDrawer({
  caseId,
  onClose,
  onUpdated,
  showClose = false,
}: {
  caseId: number | null;
  onClose: () => void;
  onUpdated?: () => void;
  showClose?: boolean;
}) {
  const [detail, setDetail] = useState<CaseDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busyInvestigate, setBusyInvestigate] = useState(false);
  const [busyLink, setBusyLink] = useState(false);
  const [actionMsg, setActionMsg] = useState<string | null>(null);
  const [investigation, setInvestigation] = useState<{
    decision?: Record<string, unknown>;
    policy?: Record<string, unknown>;
  } | null>(null);
  const [copied, setCopied] = useState(false);

  const load = useCallback(async (id: number) => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.caseDetail(id);
      setDetail(data as CaseDetail);
    } catch (e) {
      setDetail(null);
      setError(e instanceof Error ? e.message : "Failed to load case");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    setInvestigation(null);
    setActionMsg(null);
    setCopied(false);
    if (caseId == null) {
      setDetail(null);
      return;
    }
    void load(caseId);
  }, [caseId, load]);

  if (caseId == null) {
    return (
      <div className="flex h-full min-h-0 flex-col">
        <div className="border-b border-[var(--color-line)] px-4 py-3">
          <h2 className="text-[11px] font-medium uppercase tracking-[0.12em] text-[var(--color-mute)]">
            Case drawer
          </h2>
        </div>
        <p className="p-4 text-sm text-[var(--color-mute)]">Select a case from the at-risk queue.</p>
      </div>
    );
  }

  const ev = detail?.event;
  const policyLight =
    (investigation?.policy?.light as string | undefined) ||
    (investigation?.decision?.policy_light as string | undefined) ||
    (typeof detail?.decision === "object" &&
    detail?.decision &&
    "policy_light" in (detail.decision as object)
      ? String((detail.decision as { policy_light?: string }).policy_light)
      : undefined);

  async function investigate() {
    if (caseId == null) return;
    setBusyInvestigate(true);
    setActionMsg(null);
    try {
      const res = await api.investigate(caseId);
      setInvestigation(res);
      await load(caseId);
      onUpdated?.();
    } catch (e) {
      setActionMsg(e instanceof Error ? e.message : "Investigate failed");
    } finally {
      setBusyInvestigate(false);
    }
  }

  async function createLink() {
    if (caseId == null) return;
    setBusyLink(true);
    setActionMsg(null);
    try {
      const res = await api.paymentLink(caseId);
      if (!res.short_url) throw new Error(res.error || "No short_url");
      setActionMsg(`Link: ${res.short_url}`);
      try {
        window.open(res.short_url, "_blank", "noopener");
      } catch {
        /* ignore */
      }
      await load(caseId);
      onUpdated?.();
    } catch (e) {
      setActionMsg(e instanceof Error ? e.message : "Payment link failed");
    } finally {
      setBusyLink(false);
    }
  }

  async function copyUrl(url: string) {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      setActionMsg("Could not copy");
    }
  }

  const diagnosis =
    investigation?.decision ||
    (typeof detail?.decision === "object" ? (detail.decision as Record<string, unknown>) : null);

  return (
    <div className="flex h-full min-h-0 flex-col bg-[var(--color-ink)]">
      <div className="flex items-start justify-between gap-3 border-b border-[var(--color-line)] px-4 py-3">
        <div>
          <h2 className="text-[11px] font-medium uppercase tracking-[0.12em] text-[var(--color-mute)]">
            Case #{shortId(caseId)}
          </h2>
          {ev ? (
            <p className="mt-1 text-sm">
              {ev.customer_id} · <span className="mono">{formatInr(ev.amount)}</span>
            </p>
          ) : null}
        </div>
        {showClose ? (
          <button
            type="button"
            onClick={onClose}
            className="rounded p-1 text-[var(--color-mute)] hover:bg-white/5 hover:text-white"
            aria-label="Close"
          >
            <X className="size-4" />
          </button>
        ) : null}
      </div>

      <div className="min-h-0 flex-1 space-y-4 overflow-auto p-4">
        {loading ? <p className="text-sm text-[var(--color-mute)]">Loading…</p> : null}
        {error ? <p className="text-sm text-[var(--color-policy-red)]">{error}</p> : null}

        {ev ? (
          <>
            <div className="space-y-1 text-sm">
              <p className="text-[var(--color-mute)]">
                {ev.stage} / {ev.root_cause} / {ev.status}
              </p>
              <p className="mono text-xs">
                {formatInr(ev.amount_recovered || 0)} recovered of {formatInr(ev.amount)}
              </p>
              <div className="flex items-center gap-2 pt-1">
                <span className="text-xs text-[var(--color-mute)]">Policy</span>
                <PolicyLight light={policyLight} />
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              <Button
                type="button"
                variant="soft"
                size="sm"
                disabled={busyInvestigate}
                onClick={investigate}
              >
                {busyInvestigate ? "Investigating…" : "Investigate"}
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={busyLink || ev.status === "recovered"}
                onClick={createLink}
              >
                {busyLink ? "Creating…" : "Payment link"}
              </Button>
            </div>

            {actionMsg ? (
              <p className="break-all text-xs text-[var(--color-mute)]">{actionMsg}</p>
            ) : null}

            {diagnosis ? (
              <div className="border border-[var(--color-line)] bg-[var(--color-panel)] p-3">
                <h3 className="mb-2 text-[11px] uppercase tracking-[0.1em] text-[var(--color-mute)]">
                  Diagnosis
                </h3>
                <dl className="space-y-1.5 text-xs">
                  {Object.entries(diagnosis)
                    .filter(([k]) => !["raw", "pipeline"].includes(k))
                    .slice(0, 12)
                    .map(([k, v]) => (
                      <div key={k} className="flex justify-between gap-3">
                        <dt className="text-[var(--color-mute)]">{k}</dt>
                        <dd className="mono max-w-[60%] truncate text-right">
                          {typeof v === "object" ? JSON.stringify(v) : String(v ?? "—")}
                        </dd>
                      </div>
                    ))}
                </dl>
              </div>
            ) : null}

            {(detail?.payment_links?.length ?? 0) > 0 ? (
              <div>
                <h3 className="mb-2 text-[11px] uppercase tracking-[0.1em] text-[var(--color-mute)]">
                  Payment links
                </h3>
                <ul className="space-y-2">
                  {detail!.payment_links!.map((l, i) => (
                    <li
                      key={`${l.razorpay_link_id || l.short_url || i}`}
                      className="border border-[var(--color-line)] bg-[var(--color-panel)] px-3 py-2 text-xs"
                    >
                      <div className="mb-1 text-[var(--color-mute)]">{l.status || "link"}</div>
                      {l.short_url ? (
                        <div className="flex items-start gap-2">
                          <a
                            href={l.short_url}
                            target="_blank"
                            rel="noreferrer"
                            className="mono break-all text-[var(--color-policy-green)] hover:underline"
                          >
                            {l.short_url}
                          </a>
                          <button
                            type="button"
                            onClick={() => copyUrl(l.short_url!)}
                            className="shrink-0 rounded p-1 text-[var(--color-mute)] hover:bg-white/5 hover:text-white"
                            title="Copy URL"
                          >
                            <Copy className="size-3.5" />
                          </button>
                        </div>
                      ) : (
                        <span className="mono">{l.razorpay_link_id || "—"}</span>
                      )}
                      {copied ? (
                        <p className="mt-1 text-[10px] text-[var(--color-mute)]">Copied</p>
                      ) : null}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            <div>
              <h3 className="mb-2 text-[11px] uppercase tracking-[0.1em] text-[var(--color-mute)]">
                Audit trail
              </h3>
              {!detail?.audit?.length ? (
                <p className="text-xs text-[var(--color-mute)]">No audit steps yet.</p>
              ) : (
                <ul className="space-y-0">
                  {detail.audit.map((a, i) => (
                    <li
                      key={`${a.step}-${i}`}
                      className="border-b border-[var(--color-line)] py-2.5 text-xs last:border-0"
                    >
                      <div className="mono text-[11px] uppercase tracking-wide text-sky-400">
                        {a.step}
                      </div>
                      <div className="mt-0.5 text-[var(--color-fg)]">{a.detail}</div>
                      {a.created_at ? (
                        <div className="mt-0.5 text-[10px] text-[var(--color-mute)]">{a.created_at}</div>
                      ) : null}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}
