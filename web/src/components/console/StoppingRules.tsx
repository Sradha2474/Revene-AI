const RULES = [
  "Max 3 attempts",
  "Skip if amount < ₹50",
  "No blind retry during bank outage",
  "ROI gate if success chance too low",
  "Escalate to human, then stop",
];

export function StoppingRules() {
  return (
    <section className="border-b border-[var(--color-line)] p-4">
      <h2 className="mb-3 text-[11px] font-medium uppercase tracking-[0.12em] text-[var(--color-mute)]">
        Stopping rules
      </h2>
      <div className="flex flex-wrap gap-1.5">
        {RULES.map((r) => (
          <span
            key={r}
            className="rounded border border-[var(--color-line)] bg-[var(--color-panel-2)] px-2 py-1 text-[11px] text-[var(--color-mute)]"
          >
            {r}
          </span>
        ))}
      </div>
    </section>
  );
}
