import { useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { formatInr } from "@/lib/utils";

type StrategyRow = {
  name: string;
  threshold: number;
  expected_recovery: number;
  actions_taken: number;
  skipped: number;
};

export function StrategySimulator() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [caseCount, setCaseCount] = useState<number | null>(null);
  const [rows, setRows] = useState<StrategyRow[]>([]);

  async function run() {
    setBusy(true);
    setError(null);
    try {
      const data = await api.simulate();
      setCaseCount(data.case_count);
      setRows(data.strategies || []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Simulate failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="border-b border-[var(--color-line)] p-4 last:border-b-0">
      <h2 className="mb-2 text-[11px] font-medium uppercase tracking-[0.12em] text-[var(--color-mute)]">
        Strategy simulator
      </h2>
      <p className="mb-3 text-xs text-[var(--color-mute)]">
        What-if thresholds on current at-risk set — no live charges.
      </p>
      <Button type="button" variant="outline" size="sm" className="w-full" disabled={busy} onClick={run}>
        {busy ? "Simulating…" : "Simulate strategies"}
      </Button>
      {error ? <p className="mt-2 text-xs text-[var(--color-policy-red)]">{error}</p> : null}
      {rows.length > 0 ? (
        <div className="mt-3 space-y-2">
          {caseCount != null ? (
            <p className="text-[11px] text-[var(--color-mute)]">{caseCount} cases in sim</p>
          ) : null}
          {rows.map((s) => (
            <div
              key={s.name}
              className="border border-[var(--color-line)] bg-[var(--color-panel-2)] px-2.5 py-2 text-xs"
            >
              <div className="flex items-baseline justify-between gap-2">
                <span className="font-medium">{s.name}</span>
                <span className="mono text-[var(--color-mute)]">t={s.threshold}</span>
              </div>
              <p className="mt-1 text-[var(--color-mute)]">
                Expected <span className="mono text-[var(--color-fg)]">{formatInr(s.expected_recovery)}</span>
                {" · "}
                {s.actions_taken} actions · {s.skipped} skipped
              </p>
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}
