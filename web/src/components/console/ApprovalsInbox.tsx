import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";
import type { Approval } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { shortId } from "@/lib/utils";

export function ApprovalsInbox({
  approvals,
  onChanged,
}: {
  approvals: Approval[];
  onChanged?: () => void;
}) {
  const [busyId, setBusyId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function decide(id: number, status: "approved" | "rejected") {
    setBusyId(id);
    setError(null);
    try {
      await api.decideApproval(id, status);
      onChanged?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Decision failed");
    } finally {
      setBusyId(null);
    }
  }

  const pending = approvals.filter((a) => a.status === "pending");
  const rest = approvals.filter((a) => a.status !== "pending");

  return (
    <div className="mx-auto max-w-3xl px-4 py-6 md:px-6">
      <div className="mb-6 flex items-end justify-between gap-4">
        <div>
          <h2 className="text-lg font-medium tracking-tight">Approvals inbox</h2>
          <p className="mt-1 text-sm text-[var(--color-mute)]">
            YELLOW policy actions waiting for a human gate.
          </p>
        </div>
        <Badge tone="neutral">{pending.length} pending</Badge>
      </div>

      {error ? <p className="mb-4 text-sm text-[var(--color-policy-red)]">{error}</p> : null}

      {approvals.length === 0 ? (
        <p className="border border-[var(--color-line)] bg-[var(--color-panel)] p-6 text-sm text-[var(--color-mute)]">
          No approvals in queue.
        </p>
      ) : (
        <ul className="space-y-3">
          {[...pending, ...rest].map((a) => (
            <li
              key={a.id}
              className="border border-[var(--color-line)] bg-[var(--color-panel)] p-4"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="mono text-sm">#{shortId(a.id)}</span>
                    <Badge tone={a.status === "pending" ? "warn" : a.status === "approved" ? "ok" : "bad"}>
                      {a.status}
                    </Badge>
                  </div>
                  <p className="mt-2 text-sm font-medium">{a.recommended_action}</p>
                  <p className="mt-1 text-sm text-[var(--color-mute)]">{a.reason}</p>
                  <Link
                    to={`/demo/cases/${a.event_id}`}
                    className="mt-2 inline-block text-xs text-[var(--color-accent)] hover:underline"
                  >
                    Case #{a.event_id}
                  </Link>
                </div>
                {a.status === "pending" ? (
                  <div className="flex shrink-0 gap-2">
                    <Button
                      type="button"
                      variant="soft"
                      size="sm"
                      disabled={busyId === a.id}
                      onClick={() => decide(a.id, "approved")}
                    >
                      Approve
                    </Button>
                    <Button
                      type="button"
                      variant="danger"
                      size="sm"
                      disabled={busyId === a.id}
                      onClick={() => decide(a.id, "rejected")}
                    >
                      Reject
                    </Button>
                  </div>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
