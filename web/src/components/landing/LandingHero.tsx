import { useState } from "react";
import { Link } from "react-router-dom";
import { motion, AnimatePresence, type Variants } from "framer-motion";
import { ArrowRight, Zap, ShieldCheck, ArrowDown, Activity, RefreshCw } from "lucide-react";

/**
 * Watermelon UI Hero-35 implementation for Revene:
 * - Ultra-airy cinematic background with subtle fintech cybernetic graphics
 * - Floating frosted glass navbar (clean Revene brand, no buildathon badge)
 * - Interactive mode toggle with spring animation
 * - Left column: massive title + minimalist 4-dot stats counter
 * - Right column: editorial copy + dual specular pill CTA buttons
 */
export function LandingHero() {
  const [activeMode, setActiveMode] = useState<"preempt" | "recover">("preempt");

  const navVariants: Variants = {
    hidden: { opacity: 0, y: -18, filter: "blur(6px)" },
    show: {
      opacity: 1,
      y: 0,
      filter: "blur(0px)",
      transition: { type: "spring", damping: 22, stiffness: 150, delay: 0.1 },
    },
  };

  const titleWords = ["Autonomous", "Revenue", "Recovery", "for", "Modern", "Payment", "Stacks"];
  const titleContainerVariants: Variants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.08, delayChildren: 0.35 },
    },
  };
  const titleWordVariants: Variants = {
    hidden: { opacity: 0, y: 32, filter: "blur(10px)", rotateX: 8 },
    show: {
      opacity: 1,
      y: 0,
      filter: "blur(0px)",
      rotateX: 0,
      transition: { type: "spring", damping: 26, stiffness: 95, mass: 1.1 },
    },
  };

  const statsVariants: Variants = {
    hidden: { opacity: 0, y: 16, filter: "blur(4px)" },
    show: {
      opacity: 1,
      y: 0,
      filter: "blur(0px)",
      transition: { type: "spring", damping: 24, stiffness: 110, delay: 0.95 },
    },
  };

  const rightContainerVariants: Variants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.14, delayChildren: 0.65 },
    },
  };
  const rightItemVariants: Variants = {
    hidden: { opacity: 0, x: 20, filter: "blur(5px)" },
    show: {
      opacity: 1,
      x: 0,
      filter: "blur(0px)",
      transition: { type: "spring", damping: 20, stiffness: 100, mass: 0.9 },
    },
  };

  const navLinks = [
    { label: "SIMULATOR", href: "#simulator" },
    { label: "TWO LANES", href: "#lanes" },
    { label: "5-STAGE PIPELINE", href: "#how" },
    { label: "STOPPING RULES", href: "#why" },
    { label: "DEVELOPER API", href: "#api" },
  ];

  return (
    <div className="relative min-h-screen w-full overflow-hidden bg-[#03050a] font-sans text-white antialiased selection:bg-sky-500/30 selection:text-white">
      {/* Cinematic Cybernetic Background with Image Overlay */}
      <div className="pointer-events-none absolute inset-0 z-0 overflow-hidden">
        {/* Generated Futuristic Cybernetic Grid Image */}
        <motion.img
          initial={{ scale: 1.08, opacity: 0 }}
          animate={{ scale: 1, opacity: 0.28 }}
          transition={{ duration: 1.5, ease: "easeOut" }}
          src="/assets/hero-bg.jpg"
          alt="Fintech Cybernetic Grid"
          className="h-full w-full object-cover object-center mix-blend-luminosity brightness-95 contrast-125"
        />

        {/* Ambient atmospheric lighting */}
        <div className="absolute -top-[15%] left-1/2 h-[600px] w-[900px] -translate-x-1/2 rounded-full bg-sky-500/12 blur-[150px]" />
        <div className="absolute top-[35%] -left-[10%] h-[450px] w-[500px] rounded-full bg-blue-600/10 blur-[140px]" />
        <div className="absolute bottom-[10%] -right-[5%] h-[500px] w-[500px] rounded-full bg-indigo-600/10 blur-[150px]" />

        {/* Subtle grid pattern overlay */}
        <div
          className="absolute inset-0 opacity-[0.06]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255, 255, 255, 0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.08) 1px, transparent 1px)",
            backgroundSize: "72px 72px",
            maskImage: "radial-gradient(ellipse 85% 70% at 50% 35%, black 30%, transparent 80%)",
          }}
        />

        {/* Cinematic Vignette */}
        <div className="absolute inset-0 bg-gradient-to-b from-[#03050a]/80 via-[#03050a]/45 to-[#03050a]" />
      </div>

      <div className="relative z-10 mx-auto flex min-h-screen w-full max-w-[1720px] flex-col justify-between px-6 py-6 md:px-12">
        {/* Floating Frosted Glass Navbar */}
        <motion.nav
          variants={navVariants}
          initial="hidden"
          animate="show"
          className="mx-auto flex w-full max-w-6xl items-center justify-between rounded-full border border-white/10 bg-[#0d121c]/75 px-5 py-2.5 shadow-[0_4px_30px_rgba(0,0,0,0.5)] backdrop-blur-xl"
        >
          {/* Clean Enterprise Brand Logo (No buildathon badge) */}
          <Link to="/" className="group flex items-center gap-3">
            <div className="relative flex size-8 items-center justify-center rounded-lg bg-gradient-to-br from-sky-400 via-blue-600 to-indigo-600 p-[1px] shadow-[0_0_15px_rgba(14,165,233,0.4)]">
              <div className="flex size-full items-center justify-center rounded-lg bg-[#070b12]">
                <Zap className="size-4 text-sky-400" />
              </div>
            </div>
            <span className="font-heading text-lg font-bold tracking-tight text-white group-hover:text-sky-300 transition-colors">
              Revene
            </span>
          </Link>

          {/* Spaced Nav Links (Watermelon UI style) */}
          <div className="hidden items-center gap-8 text-[12px] font-medium tracking-[0.06em] text-zinc-300 md:flex">
            {navLinks.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="transition-colors hover:text-white"
              >
                {item.label}
              </a>
            ))}
          </div>

          {/* Right Action */}
          <div className="flex items-center gap-4">
            <Link
              to="/demo"
              className="hidden text-xs text-zinc-400 transition-colors hover:text-white sm:block"
            >
              Console
            </Link>
            <Link
              to="/demo"
              className="group flex min-h-[38px] items-center gap-2 rounded-full bg-zinc-200 px-5 py-2 text-[13px] font-medium text-black shadow-[inset_0_-2px_0px_rgba(0,0,0,0.2),inset_0_2px_0px_rgba(255,255,255,0.2)] transition-all will-change-transform hover:bg-white active:scale-[0.96]"
            >
              Book Demo
              <ArrowRight className="size-3.5 transition-transform group-hover:translate-x-0.5" />
            </Link>
          </div>
        </motion.nav>

        {/* Bottom Content Area (Exact Watermelon UI Hero-35 Architecture) */}
        <div className="flex flex-col items-end justify-between gap-12 pt-16 pb-12 lg:flex-row lg:pb-16">
          {/* Left Column: Title & Minimalist Stats */}
          <div className="flex w-full flex-col gap-10 lg:w-3/5" style={{ perspective: "1000px" }}>
            {/* Interactive Mode Toggle Badge */}
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] p-1 pr-3.5 text-xs text-zinc-300 backdrop-blur-md w-fit"
            >
              <div className="flex items-center rounded-full bg-white/[0.06] p-0.5 border border-white/5">
                <button
                  onClick={() => setActiveMode("preempt")}
                  className={`relative px-2.5 py-0.5 rounded-full font-mono text-[11px] font-medium transition-colors ${
                    activeMode === "preempt" ? "text-sky-300" : "text-zinc-400 hover:text-zinc-200"
                  }`}
                >
                  {activeMode === "preempt" && (
                    <motion.span
                      layoutId="heroModePill"
                      className="absolute inset-0 rounded-full bg-sky-500/20 border border-sky-400/40"
                      transition={{ type: "spring", stiffness: 350, damping: 30 }}
                    />
                  )}
                  <span className="relative z-10 flex items-center gap-1.5">
                    <span className="size-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    Preempt
                  </span>
                </button>
                <button
                  onClick={() => setActiveMode("recover")}
                  className={`relative px-2.5 py-0.5 rounded-full font-mono text-[11px] font-medium transition-colors ${
                    activeMode === "recover" ? "text-emerald-300" : "text-zinc-400 hover:text-zinc-200"
                  }`}
                >
                  {activeMode === "recover" && (
                    <motion.span
                      layoutId="heroModePill"
                      className="absolute inset-0 rounded-full bg-emerald-500/20 border border-emerald-400/40"
                      transition={{ type: "spring", stiffness: 350, damping: 30 }}
                    />
                  )}
                  <span className="relative z-10 flex items-center gap-1.5">
                    <span className="size-1.5 rounded-full bg-sky-400" />
                    Recover
                  </span>
                </button>
              </div>

              <span className="text-zinc-600">|</span>
              <AnimatePresence mode="wait">
                {activeMode === "preempt" ? (
                  <motion.span
                    key="preempt-txt"
                    initial={{ opacity: 0, x: -6 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 6 }}
                    className="text-sky-300 font-mono text-[11px]"
                  >
                    Reroute &lt; 45ms before failure
                  </motion.span>
                ) : (
                  <motion.span
                    key="recover-txt"
                    initial={{ opacity: 0, x: -6 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 6 }}
                    className="text-emerald-300 font-mono text-[11px]"
                  >
                    Bounded policy recovery with audit
                  </motion.span>
                )}
              </AnimatePresence>
            </motion.div>

            {/* Word-by-word cascade headline */}
            <motion.h1
              variants={titleContainerVariants}
              initial="hidden"
              animate="show"
              className="font-heading text-[3.25rem] leading-[1.03] font-normal tracking-tight text-white sm:text-[4.5rem] lg:text-[5.25rem]"
            >
              {titleWords.map((word, i) => (
                <motion.span
                  key={`${word}-${i}`}
                  variants={titleWordVariants}
                  className={`mr-[0.24em] inline-block last:mr-0 ${
                    word === "Recovery" || word === "Autonomous"
                      ? "font-medium bg-gradient-to-r from-white via-sky-200 to-sky-400 bg-clip-text text-transparent"
                      : ""
                  }`}
                >
                  {word}
                </motion.span>
              ))}
            </motion.h1>

            {/* Minimalist Watermelon UI Stats Row */}
            <motion.div
              variants={statsVariants}
              initial="hidden"
              animate="show"
              className="flex flex-wrap items-center gap-8 sm:gap-14 pt-2"
            >
              {[
                { value: "₹43.8L+", label: "Revenue Rescued" },
                { value: "< 45ms", label: "Intervention SLA" },
                { value: "99.98%", label: "Route Resilience" },
                { value: "SHA-256", label: "Tamper-Evident" },
              ].map(({ value, label }) => (
                <div key={label} className="flex flex-col gap-1.5">
                  <div className="flex items-center gap-2 text-white">
                    <svg
                      width="14"
                      height="14"
                      viewBox="0 0 16 16"
                      fill="currentColor"
                      className="text-sky-400 opacity-80"
                    >
                      <circle cx="4" cy="4" r="1.5" />
                      <circle cx="12" cy="4" r="1.5" />
                      <circle cx="4" cy="12" r="1.5" />
                      <circle cx="12" cy="12" r="1.5" />
                    </svg>
                    <span className="font-mono text-xl font-medium tracking-tight tabular-nums sm:text-2xl">
                      {value}
                    </span>
                  </div>
                  <span className="ml-5 text-[12px] font-medium tracking-wide text-zinc-400">
                    {label}
                  </span>
                </div>
              ))}
            </motion.div>
          </div>

          {/* Right Column: Editorial Paragraph & Dual Specular CTAs */}
          <motion.div
            variants={rightContainerVariants}
            initial="hidden"
            animate="show"
            className="flex w-full flex-col items-start gap-8 lg:w-[460px]"
          >
            <motion.p
              variants={rightItemVariants}
              className="text-[1.125rem] leading-[1.65] font-normal text-pretty text-zinc-300"
            >
              Stop losing revenue to silent bank outages and dropouts. Revene dynamically switches routes
              while customers are at checkout, recovers failed checkouts with bounded policy rules, and records every decision in a hash-chained audit ledger.
            </motion.p>

            <motion.div variants={rightItemVariants} className="flex flex-wrap items-center gap-4">
              <Link
                to="/demo"
                className="group flex min-h-[44px] items-center gap-2 rounded-full bg-zinc-200 px-7 py-3 text-[14px] font-medium text-black shadow-[inset_0_-2px_0px_rgba(0,0,0,0.2),inset_0_2px_0px_rgba(255,255,255,0.2)] transition-all will-change-transform hover:bg-white active:scale-[0.96]"
              >
                Open Live Demo
                <ArrowRight className="size-4 transition-transform group-hover:translate-x-0.5" />
              </Link>

              <a
                href="#simulator"
                className="group flex min-h-[44px] items-center gap-2 rounded-full border border-white/15 bg-white/[0.04] px-6 py-3 text-[14px] font-medium text-white/90 backdrop-blur-md transition-all hover:bg-white/10 hover:border-white/30 active:scale-[0.96]"
              >
                <Zap className="size-3.5 text-sky-400 transition-transform group-hover:scale-110" />
                Try Sandbox
                <ArrowDown className="size-3.5 opacity-60 transition-transform group-hover:translate-y-0.5" />
              </a>
            </motion.div>

            <motion.div
              variants={rightItemVariants}
              className="flex items-center gap-2 pt-2 text-[11px] font-mono text-zinc-500 tracking-wider uppercase"
            >
              <ShieldCheck className="size-3.5 text-emerald-400" />
              <span>Razorpay Test Mode Verified · HMAC Webhooks</span>
            </motion.div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
