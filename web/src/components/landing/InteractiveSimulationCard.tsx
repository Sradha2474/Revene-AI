import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ShieldAlert, ArrowRight, RefreshCw, Zap, CheckCircle2, Lock, Smartphone, ChevronRight } from "lucide-react";
import { PolicyLight } from "@/components/ui/badge";

type SimMode = "preempt" | "recover";

export function InteractiveSimulationCard() {
  const [mode, setMode] = useState<SimMode>("preempt");
  const [animating, setAnimating] = useState(false);
  const [simStep, setSimStep] = useState(3); // 0 = start, 1 = analyzing, 2 = acting, 3 = success

  const triggerSim = () => {
    if (animating) return;
    setAnimating(true);
    setSimStep(0);
    setTimeout(() => setSimStep(1), 600);
    setTimeout(() => setSimStep(2), 1400);
    setTimeout(() => {
      setSimStep(3);
      setAnimating(false);
    }, 2200);
  };

  useEffect(() => {
    // Replay sequence on tab switch
    triggerSim();
  }, [mode]);

  return (
    <div className="relative w-full max-w-xl rounded-2xl border border-white/10 bg-[#0a0e17]/90 p-5 shadow-[0_0_50px_-10px_rgba(2,132,199,0.25)] backdrop-blur-2xl">
      {/* Decorative top lighting */}
      <div className="absolute -top-px left-1/4 right-1/4 h-px bg-gradient-to-r from-transparent via-sky-400 to-transparent opacity-75" />
      <div className="pointer-events-none absolute -right-12 -top-12 h-36 w-36 rounded-full bg-sky-500/10 blur-2xl" />

      {/* Card Header & Mode Switcher */}
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3 border-b border-white/10 pb-4">
        <div className="flex items-center gap-2">
          <div className="flex size-7 items-center justify-center rounded-lg bg-sky-500/10 border border-sky-500/30 text-sky-400">
            <Zap className="size-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold tracking-wider uppercase text-white">Live Engine Simulator</span>
              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/15 px-2 py-0.5 text-[10px] font-medium text-emerald-400 border border-emerald-500/30">
                <span className="size-1.5 rounded-full bg-emerald-400 animate-pulse" />
                ACTIVE
              </span>
            </div>
            <p className="text-[11px] text-zinc-400">Razorpay Optimizer + Revene Guardrail</p>
          </div>
        </div>

        {/* Tab Buttons with Animated Sliding Pill */}
        <div className="flex rounded-lg bg-white/5 p-1 border border-white/10 text-xs relative">
          <button
            type="button"
            onClick={() => setMode("preempt")}
            className={`relative rounded-md px-3.5 py-1.5 font-medium transition-colors ${
              mode === "preempt" ? "text-white" : "text-zinc-400 hover:text-white"
            }`}
          >
            {mode === "preempt" && (
              <motion.div
                layoutId="simTabPill"
                className="absolute inset-0 rounded-md bg-sky-500 shadow-[0_0_15px_rgba(14,165,233,0.5)]"
                transition={{ type: "spring", stiffness: 380, damping: 30 }}
              />
            )}
            <span className="relative z-10 flex items-center gap-1.5">
              <Zap className="size-3" />
              Preempt Lane
            </span>
          </button>
          <button
            type="button"
            onClick={() => setMode("recover")}
            className={`relative rounded-md px-3.5 py-1.5 font-medium transition-colors ${
              mode === "recover" ? "text-white" : "text-zinc-400 hover:text-white"
            }`}
          >
            {mode === "recover" && (
              <motion.div
                layoutId="simTabPill"
                className="absolute inset-0 rounded-md bg-emerald-500 shadow-[0_0_15px_rgba(16,185,129,0.5)]"
                transition={{ type: "spring", stiffness: 380, damping: 30 }}
              />
            )}
            <span className="relative z-10 flex items-center gap-1.5">
              <RefreshCw className="size-3" />
              Recover Lane
            </span>
          </button>
        </div>
      </div>

      {/* Simulation Stage Container */}
      <div className="relative min-h-[220px] rounded-xl border border-white/5 bg-black/40 p-4 font-mono text-xs">
        <AnimatePresence mode="wait">
          {mode === "preempt" ? (
            <motion.div
              key="preempt-content"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.2 }}
              className="space-y-3"
            >
              {/* Event trigger */}
              <div className="flex items-center justify-between rounded-lg bg-white/[0.03] p-2.5 border border-white/5">
                <div className="flex items-center gap-2">
                  <span className="text-zinc-400">Incoming Txn:</span>
                  <span className="text-white font-semibold">₹4,999.00</span>
                  <span className="text-zinc-500">via</span>
                  <span className="rounded bg-white/10 px-1.5 py-0.5 text-zinc-300">HDFC UPI</span>
                </div>
                <span className="text-[11px] text-amber-400 font-sans flex items-center gap-1">
                  <ShieldAlert className="size-3.5" />
                  Z-Score +3.82 (Degrading)
                </span>
              </div>

              {/* Step progression */}
              <div className="space-y-2 pt-1 font-sans">
                <div className="flex items-center gap-2 text-[11px]">
                  <span className={`size-2 rounded-full ${simStep >= 1 ? "bg-amber-400" : "bg-zinc-700"}`} />
                  <span className="text-zinc-400">Degradation Radar:</span>
                  <span className="text-zinc-200">HDFC failure rate spiked to 64% in last 120s</span>
                </div>

                <div className="flex items-center gap-2 text-[11px]">
                  <span className={`size-2 rounded-full ${simStep >= 2 ? "bg-emerald-400 animate-ping" : "bg-zinc-700"}`} />
                  <span className="text-zinc-400">Policy Engine:</span>
                  <PolicyLight light="GREEN" />
                  <span className="text-zinc-300">Preemptive Reroute Approved (41ms)</span>
                </div>

                {/* Visual Reroute Animation */}
                <div className="relative overflow-hidden rounded-lg border border-sky-500/20 bg-sky-950/20 p-3">
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <span className="text-zinc-500 line-through">HDFC Direct</span>
                      <ArrowRight className="size-3.5 text-sky-400" />
                      <span className="font-semibold text-sky-300">Razorpay ICICI FastPath</span>
                    </div>
                    {simStep >= 3 ? (
                      <span className="flex items-center gap-1 rounded bg-emerald-500/20 px-2 py-0.5 font-mono text-[11px] text-emerald-400">
                        <CheckCircle2 className="size-3" />
                        PREEMPTED (0 Dropouts)
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-[11px] text-sky-400 font-mono">
                        <RefreshCw className="size-3 animate-spin" />
                        Rerouting...
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="recover-content"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.2 }}
              className="space-y-3"
            >
              {/* Failed event */}
              <div className="flex items-center justify-between rounded-lg bg-rose-500/10 p-2.5 border border-rose-500/20">
                <div className="flex items-center gap-2">
                  <span className="text-rose-400 font-semibold">Payment Failed:</span>
                  <span className="text-white font-semibold">₹14,200.00</span>
                  <span className="text-zinc-400">#txn_8921</span>
                </div>
                <span className="text-[11px] font-mono text-rose-400">GATEWAY_TIMEOUT</span>
              </div>

              {/* Diagnosis Grid */}
              <div className="grid grid-cols-3 gap-2 text-[11px] font-sans">
                <div className="rounded bg-white/[0.02] p-2 border border-white/5">
                  <p className="text-zinc-500">Fatigue Score</p>
                  <p className="font-semibold text-emerald-400">0 / LOW (Fresh)</p>
                </div>
                <div className="rounded bg-white/[0.02] p-2 border border-white/5">
                  <p className="text-zinc-500">Win Probability</p>
                  <p className="font-semibold text-sky-400">89.4%</p>
                </div>
                <div className="rounded bg-white/[0.02] p-2 border border-white/5">
                  <p className="text-zinc-500">Policy Gate</p>
                  <div className="flex items-center gap-1 mt-0.5">
                    <PolicyLight light="GREEN" />
                    <span className="text-emerald-300 font-medium">Smart Link</span>
                  </div>
                </div>
              </div>

              {/* Recovery result */}
              <div className="rounded-lg border border-emerald-500/20 bg-emerald-950/20 p-3">
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2 font-mono">
                    <Smartphone className="size-3.5 text-emerald-400" />
                    <span className="text-zinc-300">rzp.io/i/rev_9421 dispatched</span>
                  </div>
                  {simStep >= 3 ? (
                    <span className="flex items-center gap-1 rounded bg-emerald-500/20 px-2 py-0.5 font-mono text-[11px] text-emerald-400">
                      <CheckCircle2 className="size-3" />
                      ₹14,200 CAPTURED
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-[11px] text-zinc-400 font-mono">
                      <RefreshCw className="size-3 animate-spin" />
                      Awaiting webhook...
                    </span>
                  )}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Cryptographic hash chain footer */}
        <div className="mt-3 flex items-center justify-between border-t border-white/5 pt-2 text-[10px] text-zinc-500">
          <div className="flex items-center gap-1.5">
            <Lock className="size-3 text-sky-400" />
            <span>Audit Proof:</span>
            <span className="font-mono text-zinc-400">sha256:7e9b...41a0</span>
          </div>
          <span className="text-emerald-400">Verified & Chained</span>
        </div>
      </div>

      {/* Simulator Action Controls */}
      <div className="mt-4 flex items-center justify-between">
        <span className="text-xs text-zinc-400">
          {mode === "preempt"
            ? "Preempts 4-8% of checkouts before abandonment"
            : "Recovers 35-50% of transient payment failures"}
        </span>
        <button
          type="button"
          onClick={triggerSim}
          disabled={animating}
          className="group flex items-center gap-1.5 rounded-lg border border-sky-500/30 bg-sky-500/10 px-3 py-1.5 text-xs font-medium text-sky-300 transition-all hover:bg-sky-500/20 hover:border-sky-500/50 active:scale-95 disabled:opacity-50"
        >
          <RefreshCw className={`size-3 transition-transform ${animating ? "animate-spin" : "group-hover:rotate-45"}`} />
          {animating ? "Simulating..." : mode === "preempt" ? "Trigger Bank Flap" : "Replay Recovery"}
        </button>
      </div>
    </div>
  );
}
