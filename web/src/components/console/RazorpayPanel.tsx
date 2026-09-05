import { useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import type { AtRiskCase } from "@/lib/types";
import { formatInr, shortId } from "@/lib/utils";

export function RazorpayPanel({
  selectedCase,
  cases,
  status,
  onLinkCreated,
}: {
  selectedCase: AtRiskCase | null;
  cases: AtRiskCase[];
  status: {
    configured: boolean;
    webhook_secret_configured: boolean;
    mode: string;
    hint: string;
  } | null;
  onLinkCreated?: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [link, setLink] = useState<string | null>(null);

  async function createLink() {
    setBusy(true);
    setError(null);
    setLink(null);
    try {
      let target = selectedCase;
      if (!target) {
        target =
          cases.find((c) => ["open", "recovering", "awaiting_payment"].includes(c.status)) ||
          null;
      }
      if (!target) {
        throw new Error("No open/recovering case — simulate an outage or run batch");
      }
      const res = await api.paymentLink(target.id);
      if (!res.short_url) throw new Error(res.error || "No short_url in response");
      setLink(res.short_url);
      try {
        window.open(res.short_url, "_blank", "noopener");
      } catch {
        /* ignore */
      }
      onLinkCreated?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Link creation failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="border-b border-[var(--color-line)] p-4">
      <h2 className="mb-2 text-[11px] font-medium uppercase tracking-[0.12em] text-[var(--color-mute)]">
        Razorpay Test Mode
      </h2>
      <div className="mb-3 text-xs text-[var(--color-mute)]">
        {status == null ? (
          "Checking keys…"
        ) : status.configured ? (
          <span>
            <span className="text-[var(--color-policy-green)]">Keys loaded</span>
            {" · "}mode {status.mode}
            {status.webhook_secret_configured
              ? " · webhook secret OK"
              : " · webhook secret missing (ok until tunnel)"}
          </span>
        ) : (
          <span className="text-[var(--color-policy-red)]">
            Keys missing — add RAZORPAY_KEY_ID / SECRET to .env
          </span>
        )}
      </div>
      <p className="mb-3 text-xs leading-relaxed text-[var(--color-mute)]">
        {selectedCase
          ? `Selected case #${selectedCase.id} · ${formatInr(selectedCase.amount)}`
          : "Uses selected case, or latest open case in the queue."}
      </p>
      <Button
        type="button"
        variant="soft"
        size="sm"
        className="w-full"
        disabled={busy}
        onClick={createLink}
      >
        {busy
          ? "Creating…"
          : selectedCase
            ? `Payment link (#${shortId(selectedCase.id)})`
            : "Create payment link (latest)"}
      </Button>
      {error ? <p className="mt-2 text-xs text-[var(--color-policy-red)]">{error}</p> : null}
      {link ? (
        <a
          href={link}
          target="_blank"
          rel="noreferrer"
          className="mt-2 block break-all text-xs text-[var(--color-policy-green)] hover:underline"
        >
          {link}
        </a>
      ) : null}
    </section>
  );
}
