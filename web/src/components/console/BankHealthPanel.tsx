import { useState } from "react";
import type { BankHealth } from "@/lib/types";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

function statusLabel(b: BankHealth) {
  return (b.status || "HEALTHY").toUpperCase();
}

export function BankHealthPanel({
  banks,
  onRefresh,
}: {
  banks: BankHealth[];
  onRefresh?: () => void;
}) {
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function trigger(bank: string) {
    setBusy(bank);
    setError(null);
    try {
      await api.triggerOutage(bank);
      onRefresh?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Outage trigger failed");
    } finally {
      setBusy(null);
    }
  }

  return (
    <section className="border-b border-[var(--color-line)] p-4">
      <h2 className="mb-3 text-[11px] font-medium uppercase tracking-[0.12em] text-[var(--color-mute)]">
        Bank health
      </h2>
      <ul className="space-y-0">
        {banks.map((b) => {
          const st = statusLabel(b);
          const isOutage = st === "OUTAGE";
          const isDegraded = st === "DEGRADED";
          return (
            <li
              key={b.bank}
              className={cn(
                "flex items-center justify-between gap-2 border-b border-[var(--color-line)] py-2 text-sm last:border-0",
                isOutage && "text-[var(--color-policy-red)]",
                isDegraded && "text-[var(--color-policy-yellow)]",
              )}
            >
              <span className="flex min-w-0 items-center gap-2">
                <span
                  className={cn(
                    "inline-block size-1.5 shrink-0 rounded-full bg-[var(--color-policy-green)]",
                    isOutage && "bg-[var(--color-policy-red)]",
                    isDegraded && "bg-[var(--color-policy-yellow)]",
                  )}
                />
                <span className="truncate">{b.bank}</span>
                <span className="mono text-[11px] text-[var(--color-mute)]">
                  z {Number(b.z_score || 0).toFixed(1)}
                </span>
              </span>
              <Button
                type="button"
                variant="soft"
                size="sm"
                disabled={busy === b.bank}
                onClick={() => trigger(b.bank)}
                className="h-7 shrink-0 rounded px-2 text-[10px] uppercase tracking-wide"
              >
                {busy === b.bank ? "…" : "outage"}
              </Button>
            </li>
          );
        })}
      </ul>
      {error ? <p className="mt-2 text-xs text-[var(--color-policy-red)]">{error}</p> : null}
    </section>
  );
}
