import type { AtRiskCase } from "@/lib/types";
import { formatInr, shortId, cn } from "@/lib/utils";

export function AtRiskQueue({
  cases,
  selectedId,
  onSelect,
}: {
  cases: AtRiskCase[];
  selectedId: number | null;
  onSelect: (id: number) => void;
}) {
  return (
    <section className="flex min-h-[220px] flex-col border-t border-[var(--color-line)] lg:min-h-0 lg:flex-1">
      <div className="flex items-baseline justify-between gap-2 border-b border-[var(--color-line)] px-4 py-3">
        <h2 className="text-[11px] font-medium uppercase tracking-[0.12em] text-[var(--color-mute)]">
          At-risk queue
        </h2>
        <span className="text-[11px] text-[var(--color-mute)]">{cases.length}</span>
      </div>
      <div className="min-h-0 flex-1 overflow-auto">
        {cases.length === 0 ? (
          <p className="p-4 text-sm text-[var(--color-mute)]">
            No at-risk cases — simulate an outage
          </p>
        ) : (
          <table className="w-full text-left text-[12.5px]">
            <thead className="sticky top-0 bg-[var(--color-ink)]">
              <tr className="border-b border-[var(--color-line)] text-[11px] text-[var(--color-mute)]">
                <th className="px-3 py-2 font-medium">Case</th>
                <th className="px-3 py-2 font-medium">Stage</th>
                <th className="px-3 py-2 font-medium">Status</th>
                <th className="px-3 py-2 font-medium">₹</th>
              </tr>
            </thead>
            <tbody>
              {cases.map((c) => {
                const selected = selectedId === c.id;
                return (
                  <tr
                    key={c.id}
                    onClick={() => onSelect(c.id)}
                    className={cn(
                      "cursor-pointer border-b border-[var(--color-line)] transition-colors hover:bg-[var(--color-panel)]",
                      selected && "bg-[var(--color-panel)] outline outline-1 outline-white/15",
                    )}
                  >
                    <td className="px-3 py-2">
                      <div className="mono">#{shortId(c.id)}</div>
                      <div className="text-[11px] text-[var(--color-mute)]">{c.customer_id}</div>
                    </td>
                    <td className="px-3 py-2">
                      <div>{c.stage}</div>
                      <div className="text-[11px] text-[var(--color-mute)]">{c.root_cause}</div>
                    </td>
                    <td className="px-3 py-2">
                      <div>{c.status}</div>
                      <div className="text-[11px] text-[var(--color-mute)]">{c.attempts} tries</div>
                    </td>
                    <td className="mono px-3 py-2">
                      <div>{formatInr(c.amount_recovered || 0)}</div>
                      <div className="text-[11px] text-[var(--color-mute)]">of {formatInr(c.amount)}</div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </section>
  );
}
