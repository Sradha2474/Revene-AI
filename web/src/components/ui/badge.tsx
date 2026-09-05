import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function Badge({
  children,
  tone = "neutral",
  className,
}: {
  children: ReactNode;
  tone?: "neutral" | "ok" | "warn" | "bad" | "live";
  className?: string;
}) {
  const tones = {
    neutral: "border-[var(--color-line)] text-[var(--color-mute)]",
    ok: "border-[var(--color-policy-green)]/40 text-[var(--color-policy-green)]",
    warn: "border-[var(--color-policy-yellow)]/40 text-[var(--color-policy-yellow)]",
    bad: "border-[var(--color-policy-red)]/40 text-[var(--color-policy-red)]",
    live: "border-emerald-500/30 text-emerald-400",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[11px] uppercase tracking-[0.08em]",
        tones[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

export function PolicyLight({ light }: { light?: string }) {
  const l = (light || "").toUpperCase();
  const tone = l === "GREEN" ? "ok" : l === "YELLOW" ? "warn" : l === "RED" ? "bad" : "neutral";
  return <Badge tone={tone}>{l || "—"}</Badge>;
}
