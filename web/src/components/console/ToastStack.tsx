import { AnimatePresence, motion } from "framer-motion";
import { Link } from "react-router-dom";
import { X } from "lucide-react";
import type { ToastItem } from "@/lib/types";
import { cn } from "@/lib/utils";

export function ToastStack({
  toasts,
  onDismiss,
}: {
  toasts: ToastItem[];
  onDismiss: (id: string) => void;
}) {
  return (
    <div className="pointer-events-none fixed bottom-4 right-4 z-[80] flex w-[min(100vw-2rem,22rem)] flex-col gap-2">
      <AnimatePresence initial={false}>
        {toasts.map((t) => (
          <motion.div
            key={t.id}
            initial={{ opacity: 0, y: 12, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.98 }}
            className={cn(
              "pointer-events-auto border border-[var(--color-line)] bg-[var(--color-panel)] px-3.5 py-3 shadow-lg",
            )}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="text-sm font-medium text-[var(--color-fg)]">{t.title}</p>
                {t.detail ? (
                  <p className="mt-0.5 text-xs text-[var(--color-mute)]">{t.detail}</p>
                ) : null}
                {t.href ? (
                  <Link
                    to={t.href}
                    className="mt-1.5 inline-block text-xs text-[var(--color-accent)] underline-offset-2 hover:underline"
                  >
                    Open
                  </Link>
                ) : null}
              </div>
              <button
                type="button"
                aria-label="Dismiss"
                onClick={() => onDismiss(t.id)}
                className="shrink-0 rounded p-0.5 text-[var(--color-mute)] hover:bg-white/5 hover:text-white"
              >
                <X className="size-3.5" />
              </button>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
