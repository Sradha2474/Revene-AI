import { useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { formatInr } from "@/lib/utils";

export type BatchResult = {
  amount_at_risk: number;
  amount_won_back: number;
  recovery_rate: number;
  amount_recovered: number;
  amount_preempted: number;
  batch_size: number;
  cases_stopped?: number;
  cases_escalated?: number;
  cases_recovered?: number;
  seeded_failures?: number;
  live_revenue_recovered?: number;
  live_revenue_preempted?: number;
};

export function BatchPanel({
  onComplete,
}: {
  onComplete?: (data: BatchResult) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<BatchResult | null>(null);

  async function run() {
    setBusy(true);
    setError(null);
    try {
      const data = (await api.runBatch()) as BatchResult;
      setResult(data);
      onComplete?.(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Batch failed");
    } finally {
      setBusy(false);
    }
  }

  const rate = result ? Math.round((result.recovery_rate || 0) * 100) : null;

  return (
    <section className="border-b border-[var(--color-line)] p-4">
      <h2 className="mb-2 text-[11px] font-medium uppercase tracking-[0.12em] text-[var(--color-mute)]">
        Prove the bar
      </h2>
      <p className="mb-3 text-xs leading-relaxed text-[var(--color-mute)]">
        Measured money across a batch with stopping rules. Runs recovery on at-risk cases.
      </p>
      <Button type="button" variant="default" size="sm" className="w-full rounded-md" disabled={busy} onClick={run}>
        {busy ? "Running batch…" : "Run recovery batch"}
      </Button>
      {error ? <p className="mt-2 text-xs text-[var(--color-policy-red)]">{error}</p> : null}
      {result ? (
        <div className="mt-3 space-y-1 border border-[var(--color-line)] bg-[var(--color-panel-2)] p-3 text-xs leading-relaxed">
          <p className="font-medium">
            Batch done ({result.batch_size} cases
            {result.seeded_failures ? `, ${result.seeded_failures} seeded` : ""})
          </p>
          <p>
            At risk: <span className="mono">{formatInr(result.amount_at_risk)}</span>
          </p>
          <p>
            Recovered:{" "}
            <span className="mono text-[var(--color-policy-green)]">{formatInr(result.amount_recovered)}</span>
          </p>
          <p>
            Preempted: <span className="mono text-sky-400">{formatInr(result.amount_preempted)}</span>
          </p>
          <p>
            Won back:{" "}
            <span className="mono text-[var(--color-policy-green)]">
              {formatInr(result.amount_won_back)}
            </span>{" "}
            ({rate}%)
          </p>
        </div>
      ) : null}
    </section>
  );
}
