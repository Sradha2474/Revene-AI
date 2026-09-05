import type { TxnFeedItem } from "@/lib/types";
import { formatInr, shortId } from "@/lib/utils";
import { cn } from "@/lib/utils";

export function LiveFeed({ items }: { items: TxnFeedItem[] }) {
  return (
    <section className="flex min-h-0 flex-1 flex-col border-b border-[var(--color-line)] lg:border-b-0">
      <div className="flex items-baseline justify-between gap-2 border-b border-[var(--color-line)] px-4 py-3">
        <h2 className="text-[11px] font-medium uppercase tracking-[0.12em] text-[var(--color-mute)]">
          Live payment feed
        </h2>
        <span className="text-[11px] text-[var(--color-mute)]">{items.length} shown</span>
      </div>
      <div className="min-h-0 flex-1 overflow-auto">
        {items.length === 0 ? (
          <p className="p-4 text-sm text-[var(--color-mute)]">Waiting for transactions…</p>
        ) : (
          <table className="w-full text-left text-[12.5px]">
            <thead className="sticky top-0 bg-[var(--color-ink)]">
              <tr className="border-b border-[var(--color-line)] text-[11px] text-[var(--color-mute)]">
                <th className="px-3 py-2 font-medium">Customer</th>
                <th className="px-3 py-2 font-medium">Amount</th>
                <th className="px-3 py-2 font-medium">Bank</th>
                <th className="px-3 py-2 font-medium">Route</th>
                <th className="px-3 py-2 font-medium">Pay</th>
              </tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <tr key={row.id} className="border-b border-[var(--color-line)]">
                  <td className="mono px-3 py-2">{shortId(row.customer_id)}</td>
                  <td className="mono px-3 py-2">{formatInr(row.amount)}</td>
                  <td className="px-3 py-2">{row.bank}</td>
                  <td className="px-3 py-2 text-[var(--color-mute)]">
                    {row.recommended_method || "—"}
                  </td>
                  <td
                    className={cn(
                      "px-3 py-2",
                      row.success
                        ? "text-[var(--color-policy-green)]"
                        : "text-[var(--color-policy-red)]",
                    )}
                  >
                    {row.success ? "ok" : "fail"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  );
}
