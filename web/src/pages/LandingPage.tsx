import { useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  ShieldAlert,
  ShieldCheck,
  Zap,
  CheckCircle2,
  Lock,
  Smartphone,
  Cpu,
  RefreshCw,
  GitBranch,
  Terminal,
  ChevronRight,
  ExternalLink,
  Code2,
  Copy,
  Check,
} from "lucide-react";
import { LandingHero } from "@/components/landing/LandingHero";
import { InteractiveSimulationCard } from "@/components/landing/InteractiveSimulationCard";
import { Button } from "@/components/ui/button";
import { PolicyLight, Badge } from "@/components/ui/badge";

export default function LandingPage() {
  const [activeStage, setActiveStage] = useState(0);
  const [codeTab, setCodeTab] = useState<"webhook" | "node" | "python">("webhook");
  const [copied, setCopied] = useState(false);

  const copyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const stages = [
    {
      step: "01",
      title: "Detect",
      subtitle: "Bank Health & Outage Telemetry",
      desc: "Monitors real-time Z-scores across Indian banks (HDFC, SBI, ICICI, Axis). Identifies deteriorating payment routes before customers face broken payment screens.",
      badge: "Real-time Telemetry",
      detail: {
        trigger: "HDFC UPI Degradation Z-Score: +3.82 (> 3.0 threshold)",
        latency: "18ms detection window",
        action: "Mark route at-risk before dropouts occur",
      },
    },
    {
      step: "02",
      title: "Diagnose",
      subtitle: "Failure Categorization & Win Probability",
      desc: "Classifies failures into transient downtime, user balance, or permanent auth rejects. Computes dynamic recovery probability and customer retry fatigue.",
      badge: "AI Triage",
      detail: {
        trigger: "GATEWAY_TIMEOUT (Transient Error)",
        latency: "Win Probability: 89.4% | Fatigue: LOW (0/3 tries)",
        action: "Candidate for autonomous Smart Link recovery",
      },
    },
    {
      step: "03",
      title: "Policy Gate",
      subtitle: "Autonomous Bounds (Green / Yellow / Red)",
      desc: "Strict policy fences. GREEN auto-executes. YELLOW routes to human team for 1-click authorization. RED enforces hard stopping rules to protect merchant reputation.",
      badge: "Guardrails",
      detail: {
        trigger: "Amount: ₹14,200 | Fatigue: LOW | Merchant Bound: OK",
        latency: "Policy Light: GREEN",
        action: "Autonomous dispatch approved with hard ROI boundary",
      },
    },
    {
      step: "04",
      title: "Execute",
      subtitle: "Razorpay Smart Links & Intent Reroute",
      desc: "In Preempt Lane: shifts route via Razorpay Optimizer. In Recover Lane: generates time-bounded, authenticated Razorpay Test/Live payment link delivered instantly.",
      badge: "Fast Dispatch",
      detail: {
        trigger: "Smart Payment Link generated: rzp.io/i/rev_9421",
        latency: "Dispatched via SMS & WhatsApp webhook in 120ms",
        action: "Customer completes checkout without re-entering cart",
      },
    },
    {
      step: "05",
      title: "Audit",
      subtitle: "Cryptographic Hash-Chained Trail",
      desc: "Every degradation score, policy evaluation, and recovery attempt is appended to a SHA-256 hash-chained ledger. Guaranteed tamper-evident compliance.",
      badge: "SHA-256 Chained",
      detail: {
        trigger: "Block #40572: Hash 7f4a9b...d91c -> Prev 8e2c...140f",
        latency: "Reconciliation with payment.captured webhook",
        action: "Honest ₹ counted only after settlement",
      },
    },
  ];

  const codeSnippets = {
    webhook: `// Razorpay Webhook Configuration: Forward to Revene
POST https://api.revene.ai/v1/webhooks/razorpay
Headers:
  x-razorpay-signature: <hmac_sha256_secret>

// Handled Events:
- payment.failed       -> Autonomous AI Diagnosis & Policy Triage
- payment.captured     -> Recovery Reconciliation & Revenue Credit
- order.paid           -> Hash Audit Finalization`,
    node: `import { Revene } from "@revene/sdk";

const revene = new Revene({
  apiKey: process.env.REVENE_KEY,
  razorpayKey: process.env.RAZORPAY_KEY_ID
});

// Guard an incoming payment checkout
const route = await revene.preempt({
  amount: 499900,
  preferredBank: "HDFC",
  method: "upi"
});

// Automatically chooses optimal route if HDFC is degrading
console.log(route.recommendedMethod); // "razorpay_direct_icici"`,
    python: `from revene import ReveneClient

client = ReveneClient(
    api_key="rev_live_...",
    razorpay_key="rzp_test_..."
)

# Intercept checkout before failure
decision = client.preempt_route(
    amount=4999.00,
    bank="HDFC",
    customer_id="cust_9410"
)

if decision.is_degrading:
    print(f"Rerouting to {decision.safe_method} (SLA {decision.latency_ms}ms)")`,
  };

  return (
    <div className="min-h-screen bg-[#06080e] text-[#f0f3f8] antialiased selection:bg-sky-500/30 selection:text-white">
      {/* Hero Section */}
      <LandingHero />

      {/* Interactive Simulation Sandbox Section */}
      <section id="simulator" className="relative z-10 mx-auto -mt-6 mb-28 max-w-5xl px-6 md:px-10">
        <div className="mb-10 flex flex-col items-center text-center">
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-sky-400/30 bg-sky-500/10 px-3.5 py-1 text-xs font-semibold text-sky-300">
            <Zap className="size-3.5 text-sky-400" />
            <span>LIVE INTERACTIVE REVENUE SANDBOX</span>
          </div>
          <h2 className="font-heading text-2xl font-bold tracking-tight text-white sm:text-3xl md:text-4xl">
            Experience the Two-Lane Guardian in Real Time
          </h2>
          <p className="mt-2 max-w-xl text-sm text-zinc-400">
            Simulate an HDFC UPI degradation before checkout, or test Razorpay autonomous payment link recovery with bounded policy rules.
          </p>
        </div>

        <InteractiveSimulationCard />
      </section>

      {/* Two Lanes Section */}
      <section id="lanes" className="relative border-t border-white/10 bg-[#080c14] py-28">
        {/* Glow ambient */}
        <div className="pointer-events-none absolute left-1/2 top-0 h-96 w-full -translate-x-1/2 bg-gradient-to-b from-sky-500/5 via-transparent to-transparent" />

        <div className="relative mx-auto max-w-6xl px-6 md:px-10">
          <div className="mb-16 flex flex-col gap-3">
            <div className="flex items-center gap-2">
              <span className="size-2 rounded-full bg-sky-400" />
              <p className="font-mono text-xs uppercase tracking-[0.2em] text-sky-400">Two Intelligent Lanes</p>
            </div>
            <h2 className="font-heading text-3xl font-bold tracking-tight sm:text-4xl md:text-5xl text-white">
              Act before failure — and recover after it.
            </h2>
            <p className="max-w-2xl text-base text-zinc-400">
              Most payment tools only trigger after the transaction is dead and the buyer has abandoned.
              Revene protects both sides of the checkout boundary.
            </p>
          </div>

          <div className="grid gap-8 lg:grid-cols-2">
            {/* Lane 1: Preempt */}
            <div className="group relative overflow-hidden rounded-2xl border border-sky-500/20 bg-gradient-to-b from-[#0c1322] to-[#080d16] p-8 shadow-[0_4px_30px_rgba(0,0,0,0.5)] transition-all hover:border-sky-400/40 hover:shadow-[0_0_40px_rgba(2,132,199,0.15)]">
              <div className="pointer-events-none absolute -right-10 -top-10 size-48 rounded-full bg-sky-500/10 blur-3xl group-hover:bg-sky-500/15" />

              <div className="mb-6 flex items-center justify-between">
                <span className="inline-flex items-center gap-1.5 rounded-full border border-sky-400/30 bg-sky-500/10 px-3 py-1 font-mono text-xs font-semibold text-sky-300">
                  <Zap className="size-3.5" />
                  LANE 01 · PREEMPT
                </span>
                <span className="font-mono text-xs text-zinc-500">Before Checkout Drop</span>
              </div>

              <h3 className="font-heading text-2xl font-bold text-white mb-3">
                Preempt Degrading Routes
              </h3>
              <p className="text-sm leading-relaxed text-zinc-300 mb-6">
                Bank success rates fluctuate constantly. When HDFC or SBI experiences latency spikes or flapping gateway timeouts, Revene detects the statistical anomaly and seamlessly reroutes the buyer to a healthy Razorpay gateway before failure.
              </p>

              {/* Visual mini-pipeline */}
              <div className="rounded-xl border border-white/10 bg-black/40 p-4 font-mono text-xs space-y-3">
                <div className="flex items-center justify-between text-zinc-400">
                  <span>Detection Signal:</span>
                  <span className="text-amber-400 font-semibold">Bank Flap (Z &gt; +3.0)</span>
                </div>
                <div className="flex items-center justify-between text-zinc-400">
                  <span>Switch Latency:</span>
                  <span className="text-sky-300 font-semibold">&lt; 42 milliseconds</span>
                </div>
                <div className="flex items-center justify-between border-t border-white/10 pt-2 text-zinc-300">
                  <span>Checkout Outcome:</span>
                  <span className="text-emerald-400 font-semibold flex items-center gap-1">
                    <CheckCircle2 className="size-3.5" /> 100% Frictionless Capture
                  </span>
                </div>
              </div>
            </div>

            {/* Lane 2: Recover */}
            <div className="group relative overflow-hidden rounded-2xl border border-emerald-500/20 bg-gradient-to-b from-[#0c1a18] to-[#080d16] p-8 shadow-[0_4px_30px_rgba(0,0,0,0.5)] transition-all hover:border-emerald-400/40 hover:shadow-[0_0_40px_rgba(16,185,129,0.15)]">
              <div className="pointer-events-none absolute -right-10 -top-10 size-48 rounded-full bg-emerald-500/10 blur-3xl group-hover:bg-emerald-500/15" />

              <div className="mb-6 flex items-center justify-between">
                <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-400/30 bg-emerald-500/10 px-3 py-1 font-mono text-xs font-semibold text-emerald-300">
                  <RefreshCw className="size-3.5" />
                  LANE 02 · RECOVER
                </span>
                <span className="font-mono text-xs text-zinc-500">After Payment Failure</span>
              </div>

              <h3 className="font-heading text-2xl font-bold text-white mb-3">
                Autonomous Failure Recovery
              </h3>
              <p className="text-sm leading-relaxed text-zinc-300 mb-6">
                When a checkout fails due to a network glitch or bank drop, Revene diagnoses the root cause in milliseconds. If bounded policy rules evaluate to GREEN, it dispatches an authorized Razorpay Smart Link to win back the sale with zero merchant effort.
              </p>

              {/* Visual mini-pipeline */}
              <div className="rounded-xl border border-white/10 bg-black/40 p-4 font-mono text-xs space-y-3">
                <div className="flex items-center justify-between text-zinc-400">
                  <span>Root Cause Triage:</span>
                  <span className="text-emerald-300 font-semibold">Transient Network Glitch</span>
                </div>
                <div className="flex items-center justify-between text-zinc-400">
                  <span>Recovery Channel:</span>
                  <span className="text-sky-300 font-semibold">Razorpay Smart Link (SMS/WhatsApp)</span>
                </div>
                <div className="flex items-center justify-between border-t border-white/10 pt-2 text-zinc-300">
                  <span>Reconciliation:</span>
                  <span className="text-emerald-400 font-semibold flex items-center gap-1">
                    <CheckCircle2 className="size-3.5" /> Verified on payment.captured
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Visual Showcase Banner with Cybernetic Shield */}
          <div className="mt-12 overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-r from-[#0c1322] via-[#09151e] to-[#0c1a18] p-6 shadow-2xl">
            <div className="grid items-center gap-8 md:grid-cols-12">
              <div className="md:col-span-7 space-y-3">
                <div className="inline-flex items-center gap-2 rounded-full border border-sky-400/30 bg-sky-500/10 px-3 py-1 font-mono text-[11px] font-semibold text-sky-300">
                  <ShieldCheck className="size-3.5 text-emerald-400" />
                  <span>TAMPER-PROOF CRYPTOGRAPHIC DEFENSE</span>
                </div>
                <h3 className="font-heading text-2xl font-bold text-white sm:text-3xl">
                  Enterprise Resilience Meets Cryptographic Proof
                </h3>
                <p className="text-sm leading-relaxed text-zinc-300">
                  Every routing decision, bank flap signal, and recovered checkout is backed by a SHA-256 hash-chained ledger. High-volume merchants get provable compliance without sacrificing microsecond latency.
                </p>
                <div className="flex flex-wrap gap-4 pt-2 font-mono text-xs text-zinc-400">
                  <span className="flex items-center gap-1 text-sky-300">
                    <CheckCircle2 className="size-3.5" /> &lt; 45ms Decision Loop
                  </span>
                  <span className="flex items-center gap-1 text-emerald-300">
                    <CheckCircle2 className="size-3.5" /> Zero Blind Retries
                  </span>
                  <span className="flex items-center gap-1 text-indigo-300">
                    <CheckCircle2 className="size-3.5" /> Razorpay Test-Verified
                  </span>
                </div>
              </div>
              <div className="relative md:col-span-5 overflow-hidden rounded-xl border border-white/15 shadow-xl group">
                <img
                  src="/assets/payment-shield.jpg"
                  alt="Digital Payment Shield"
                  className="w-full h-48 sm:h-56 object-cover transition-transform duration-500 group-hover:scale-105"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent flex items-end p-4">
                  <span className="font-mono text-[11px] text-emerald-300 bg-black/60 backdrop-blur-md px-2.5 py-1 rounded-md border border-emerald-500/30">
                    STATUS: ACTIVE GUARD (SHA-256)
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 5-Stage Pipeline Stepper Section */}
      <section id="how" className="relative border-t border-white/10 bg-[#060911] py-28">
        <div className="relative mx-auto max-w-6xl px-6 md:px-10">
          <div className="mb-16 flex flex-col gap-3">
            <div className="flex items-center gap-2">
              <span className="size-2 rounded-full bg-emerald-400" />
              <p className="font-mono text-xs uppercase tracking-[0.2em] text-emerald-400">5-Stage Execution Architecture</p>
            </div>
            <h2 className="font-heading text-3xl font-bold tracking-tight sm:text-4xl md:text-5xl text-white">
              Deterministic, bounded, and audit-proven.
            </h2>
            <p className="max-w-2xl text-base text-zinc-400">
              Explore each stage of the autonomous pipeline. No black-box guesses — every action obeys mathematically proven guardrails.
            </p>
          </div>

          {/* Stepper Navigation */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-5 mb-8">
            {stages.map((st, idx) => (
              <button
                key={st.step}
                type="button"
                onClick={() => setActiveStage(idx)}
                className={`relative flex flex-col items-start rounded-xl border p-4 text-left transition-all ${
                  activeStage === idx
                    ? "border-sky-400/50 bg-sky-950/30 shadow-[0_0_25px_rgba(2,132,199,0.2)]"
                    : "border-white/10 bg-white/[0.02] hover:bg-white/[0.04] hover:border-white/20"
                }`}
              >
                <div className="flex w-full items-center justify-between mb-2">
                  <span className={`font-mono text-xs font-bold ${activeStage === idx ? "text-sky-400" : "text-zinc-500"}`}>
                    {st.step}
                  </span>
                  {activeStage === idx && <span className="size-2 rounded-full bg-sky-400 animate-ping" />}
                </div>
                <p className="font-heading text-sm font-semibold text-white">{st.title}</p>
                <p className="text-[11px] text-zinc-400 truncate w-full">{st.subtitle}</p>
              </button>
            ))}
          </div>

          {/* Active Stage Deep Dive Display */}
          <div className="rounded-2xl border border-white/10 bg-gradient-to-b from-[#0e1422] to-[#0a0f19] p-8 shadow-2xl">
            <div className="grid gap-8 lg:grid-cols-12 items-center">
              <div className="lg:col-span-7 space-y-4">
                <div className="flex items-center gap-3">
                  <span className="font-mono text-xs font-bold text-sky-400 bg-sky-500/10 border border-sky-400/30 px-2.5 py-1 rounded-full">
                    STAGE {stages[activeStage].step}
                  </span>
                  <span className="text-xs font-semibold text-zinc-400">{stages[activeStage].badge}</span>
                </div>
                <h3 className="font-heading text-2xl font-bold text-white sm:text-3xl">
                  {stages[activeStage].title}: {stages[activeStage].subtitle}
                </h3>
                <p className="text-zinc-300 leading-relaxed text-sm sm:text-base">
                  {stages[activeStage].desc}
                </p>

                {activeStage === 2 && (
                  <div className="pt-2">
                    <p className="text-xs text-zinc-400 mb-2 font-mono uppercase tracking-wider">
                      Policy Fence Traffic Lights:
                    </p>
                    <div className="flex flex-wrap gap-4">
                      <div className="flex items-center gap-2 rounded-lg border border-emerald-500/30 bg-emerald-950/20 px-3 py-1.5 text-xs">
                        <PolicyLight light="GREEN" />
                        <span className="text-emerald-300">GREEN: Auto recovery dispatched</span>
                      </div>
                      <div className="flex items-center gap-2 rounded-lg border border-amber-500/30 bg-amber-950/20 px-3 py-1.5 text-xs">
                        <PolicyLight light="YELLOW" />
                        <span className="text-amber-300">YELLOW: Human approval required</span>
                      </div>
                      <div className="flex items-center gap-2 rounded-lg border border-rose-500/30 bg-rose-950/20 px-3 py-1.5 text-xs">
                        <PolicyLight light="RED" />
                        <span className="text-rose-300">RED: Hard stop enforcement</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Stage Schema / Live Payload Inspector */}
              <div className="lg:col-span-5">
                <div className="rounded-xl border border-white/10 bg-black/60 p-5 font-mono text-xs space-y-3">
                  <div className="flex items-center justify-between border-b border-white/10 pb-2.5">
                    <span className="text-zinc-400 flex items-center gap-1.5">
                      <Terminal className="size-3.5 text-sky-400" />
                      Runtime Inspector
                    </span>
                    <span className="text-[11px] text-emerald-400">ACTIVE EXECUTION</span>
                  </div>
                  <div>
                    <p className="text-zinc-500 text-[11px]">Evaluation Trigger:</p>
                    <p className="text-zinc-200 mt-0.5">{stages[activeStage].detail.trigger}</p>
                  </div>
                  <div>
                    <p className="text-zinc-500 text-[11px]">Performance Telemetry:</p>
                    <p className="text-sky-300 mt-0.5">{stages[activeStage].detail.latency}</p>
                  </div>
                  <div className="border-t border-white/10 pt-2">
                    <p className="text-zinc-500 text-[11px]">Engine Action:</p>
                    <p className="text-emerald-400 mt-0.5 font-semibold">{stages[activeStage].detail.action}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stopping Rules Matrix (#why) */}
      <section id="why" className="relative border-t border-white/10 bg-[#080c16] py-28">
        <div className="relative mx-auto max-w-6xl px-6 md:px-10">
          <div className="mb-16 flex flex-col gap-3">
            <div className="flex items-center gap-2">
              <span className="size-2 rounded-full bg-amber-400" />
              <p className="font-mono text-xs uppercase tracking-[0.2em] text-amber-400">The Revene Difference</p>
            </div>
            <h2 className="font-heading text-3xl font-bold tracking-tight sm:text-4xl md:text-5xl text-white">
              Why blind retries destroy customer trust.
            </h2>
            <p className="max-w-2xl text-base text-zinc-400">
              Standard retry logic spams customers, triggers bank anti-fraud locks, and burns gateway fees. Revene enforces mathematical stopping bounds.
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            {/* Bad approach */}
            <div className="rounded-2xl border border-rose-500/20 bg-rose-950/10 p-7">
              <div className="flex items-center gap-2 text-rose-400 mb-4 font-mono text-xs font-semibold">
                <ShieldAlert className="size-4" />
                CONVENTIONAL RECOVERY (BLIND RETRIES)
              </div>
              <ul className="space-y-4 text-sm text-zinc-400">
                <li className="flex items-start gap-2.5">
                  <span className="text-rose-400 font-bold">✕</span>
                  <span><strong>Customer Fatigue:</strong> Pings customers repeatedly even when they deliberately cancelled or have insufficient balance.</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="text-rose-400 font-bold">✕</span>
                  <span><strong>Negative ROI:</strong> Spends ₹15 in gateway retry fees chasing a ₹50 checkout.</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="text-rose-400 font-bold">✕</span>
                  <span><strong>Vanity Metrics:</strong> Reports "potential recovered" without reconciling real bank capture.</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="text-rose-400 font-bold">✕</span>
                  <span><strong>Zero Traceability:</strong> No tamper-proof log of why a payment link was triggered or stopped.</span>
                </li>
              </ul>
            </div>

            {/* Revene approach */}
            <div className="rounded-2xl border border-emerald-500/30 bg-emerald-950/10 p-7 shadow-[0_0_40px_rgba(16,185,129,0.1)]">
              <div className="flex items-center gap-2 text-emerald-400 mb-4 font-mono text-xs font-semibold">
                <ShieldCheck className="size-4" />
                REVENE AUTONOMOUS POLICY ENGINE
              </div>
              <ul className="space-y-4 text-sm text-zinc-300">
                <li className="flex items-start gap-2.5">
                  <CheckCircle2 className="size-4 text-emerald-400 shrink-0 mt-0.5" />
                  <span><strong>Fatigue Hard Stop:</strong> Evaluates retry fatigue score. Shuts down immediately if fatigue reaches HIGH.</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <CheckCircle2 className="size-4 text-emerald-400 shrink-0 mt-0.5" />
                  <span><strong>Strict ROI Gates:</strong> Only acts if Expected Value &gt; Execution Cost. Configurable min-amount thresholds.</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <CheckCircle2 className="size-4 text-emerald-400 shrink-0 mt-0.5" />
                  <span><strong>Honest Razorpay Math:</strong> Revenue counted strictly upon verified <code>payment.captured</code> webhook callback.</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <CheckCircle2 className="size-4 text-emerald-400 shrink-0 mt-0.5" />
                  <span><strong>SHA-256 Hash Chain:</strong> Every event, policy verdict, and recovery step recorded in an immutable audit ledger.</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Developer API & Webhook Preview (#api) */}
      <section id="api" className="relative border-t border-white/10 bg-[#060911] py-28">
        <div className="relative mx-auto max-w-6xl px-6 md:px-10">
          <div className="mb-14 flex flex-col gap-3">
            <div className="flex items-center gap-2">
              <span className="size-2 rounded-full bg-sky-400" />
              <p className="font-mono text-xs uppercase tracking-[0.2em] text-sky-400">Integration Architecture</p>
            </div>
            <h2 className="font-heading text-3xl font-bold tracking-tight sm:text-4xl md:text-5xl text-white">
              Integrate in minutes with Razorpay.
            </h2>
            <p className="max-w-2xl text-base text-zinc-400">
              Connect via Razorpay Webhook forwarder or import the 2-line SDK for checkout routing.
            </p>
          </div>

          <div className="overflow-hidden rounded-2xl border border-white/10 bg-[#090d16] shadow-2xl">
            <div className="flex items-center justify-between border-b border-white/10 bg-[#0c121e] px-5 py-3">
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setCodeTab("webhook")}
                  className={`rounded-lg px-3 py-1 text-xs font-mono transition-all ${
                    codeTab === "webhook" ? "bg-sky-500/20 text-sky-300 border border-sky-500/30" : "text-zinc-400 hover:text-white"
                  }`}
                >
                  Razorpay Webhook
                </button>
                <button
                  type="button"
                  onClick={() => setCodeTab("node")}
                  className={`rounded-lg px-3 py-1 text-xs font-mono transition-all ${
                    codeTab === "node" ? "bg-sky-500/20 text-sky-300 border border-sky-500/30" : "text-zinc-400 hover:text-white"
                  }`}
                >
                  Node.js SDK
                </button>
                <button
                  type="button"
                  onClick={() => setCodeTab("python")}
                  className={`rounded-lg px-3 py-1 text-xs font-mono transition-all ${
                    codeTab === "python" ? "bg-sky-500/20 text-sky-300 border border-sky-500/30" : "text-zinc-400 hover:text-white"
                  }`}
                >
                  Python Client
                </button>
              </div>

              <button
                type="button"
                onClick={() => copyCode(codeSnippets[codeTab])}
                className="flex items-center gap-1.5 rounded border border-white/10 bg-white/5 px-2.5 py-1 font-mono text-[11px] text-zinc-300 hover:bg-white/10 transition-colors"
              >
                {copied ? <Check className="size-3 text-emerald-400" /> : <Copy className="size-3 text-zinc-400" />}
                {copied ? "Copied" : "Copy"}
              </button>
            </div>

            <div className="p-6 font-mono text-xs leading-relaxed text-zinc-300 overflow-x-auto">
              <pre className="text-sky-300">{codeSnippets[codeTab]}</pre>
            </div>
          </div>
        </div>
      </section>

      {/* Call to Action (#proof) */}
      <section id="proof" className="relative border-t border-white/10 bg-[#080d16] py-28 overflow-hidden">
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-r from-sky-500/10 via-blue-600/10 to-transparent blur-3xl" />

        <div className="relative mx-auto flex max-w-6xl flex-col items-center justify-between gap-10 px-6 md:flex-row md:px-10">
          <div className="max-w-2xl space-y-4">
            <span className="font-mono text-xs uppercase tracking-[0.2em] text-emerald-400">
              Interactive Test Environment
            </span>
            <h2 className="font-heading text-3xl font-bold tracking-tight text-white sm:text-4xl md:text-5xl">
              Experience autonomous recovery live.
            </h2>
            <p className="text-base text-zinc-300">
              Launch the Revene command console. Simulate live bank degradation, inject failed transactions, execute Razorpay Test Smart Links, and verify the cryptographic audit chain.
            </p>
          </div>

          <div className="shrink-0 flex flex-col sm:flex-row items-center gap-4">
            <Button asChild variant="hero" size="lg" className="specular-pill shadow-[0_0_35px_rgba(255,255,255,0.3)] group text-zinc-950 font-bold">
              <Link to="/demo">
                Launch Live Demo Console
                <ArrowRight className="size-4 transition-transform group-hover:translate-x-1" />
              </Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Modern Razorpay-Style Footer */}
      <footer className="border-t border-white/10 bg-[#04060a] py-12">
        <div className="mx-auto flex max-w-6xl flex-col gap-6 px-6 md:flex-row md:items-center md:justify-between md:px-10">
          <div className="flex items-center gap-3">
            <div className="flex size-7 items-center justify-center rounded-lg bg-white/10 text-white font-bold text-xs">
              R
            </div>
            <div>
              <p className="font-heading text-sm font-bold text-white">Revene AI</p>
              <p className="text-xs text-zinc-500">Autonomous Revenue Recovery · Razorpay AI Buildathon Track 03</p>
            </div>
          </div>

          <div className="flex items-center gap-6 text-xs text-zinc-400 font-mono">
            <a
              href="https://github.com/Sradha2474/Revene-AI"
              target="_blank"
              rel="noreferrer"
              className="hover:text-white transition-colors flex items-center gap-1"
            >
              GitHub <ExternalLink className="size-3" />
            </a>
            <span className="text-zinc-700">·</span>
            <span className="text-zinc-400">MIT Open Source</span>
            <span className="text-zinc-700">·</span>
            <span className="text-emerald-400">All Systems Operational</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
