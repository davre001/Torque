"use client";

import * as React from "react";
import {
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  GitPullRequest,
  Terminal,
  Search,
  Wrench,
  ShieldCheck,
  ExternalLink,
  Sparkles,
  Play,
} from "lucide-react";
import { SonarGrid } from "@/components/ui/sonar-grid";
import Demo from "@/components/ui/sonar-grid-demo";

type AgentStatus =
  | "idle"
  | "investigating"
  | "implementing"
  | "recovering"
  | "verifying"
  | "completed";

interface Attempt {
  number: number;
  strategy: string;
  status: "failed" | "passed";
  detail: string;
  traceId: string;
  duration: string;
}

const PRESET_ISSUES = [
  {
    title: "FastAPI 404 router handler bug",
    url: "https://github.com/tiangolo/fastapi/issues/4821",
    scenario: "Fails attempt 1 (router collision) → Recovers on attempt 2 (middleware fallback)",
  },
  {
    title: "SQLAlchemy async connection pool timeout",
    url: "https://github.com/sqlalchemy/sqlalchemy/issues/8912",
    scenario: "Fails attempt 1 (hard reconnect) → Recovers on attempt 2 (backoff retry)",
  },
];

export default function TorquePage() {
  const [viewMode, setViewMode] = React.useState<"torque" | "demo">("torque");
  const [issueUrl, setIssueUrl] = React.useState(
    "https://github.com/tiangolo/fastapi/issues/4821"
  );
  const [status, setStatus] = React.useState<AgentStatus>("idle");
  const [stepIndex, setStepIndex] = React.useState<number>(0);
  const [attempts, setAttempts] = React.useState<Attempt[]>([]);
  const [logMessages, setLogMessages] = React.useState<string[]>([]);
  const [prCreated, setPrCreated] = React.useState<boolean>(false);
  const timerRef = React.useRef<NodeJS.Timeout | null>(null);

  const resetRun = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    setStatus("idle");
    setStepIndex(0);
    setAttempts([]);
    setLogMessages([]);
    setPrCreated(false);
  };

  const startSimulation = () => {
    resetRun();
    setStatus("investigating");
    setStepIndex(1);
    setLogMessages(["[Investigator] Initializing Entire code graph for target repository..."]);

    // Timeline of multi-agent recovery demo
    const timeline = [
      {
        delay: 1500,
        action: () => {
          setLogMessages((prev) => [
            ...prev,
            "[Investigator] Entire index scan complete: found 3 relevant call sites in routing.py and test_routing.py",
            "[Implementer] Spawning isolated worktree torque/worktree-patch-4821...",
          ]);
          setStatus("implementing");
          setStepIndex(2);
        },
      },
      {
        delay: 3500,
        action: () => {
          setLogMessages((prev) => [
            ...prev,
            "[Implementer] Naive patch applied: direct exception re-raise in Starlette router",
            "[Implementer] Running test suite: pytest tests/test_routing.py...",
            "⚠️ [Test Suite] FAIL: 1 failed, 14 passed (AssertionError: Expected 404 got 500)",
            "[neatlogs] Failure span captured: trace_id=nl_tr_4821_f1",
          ]);
          setAttempts([
            {
              number: 1,
              strategy: "Direct router exception re-raise",
              status: "failed",
              detail: "Unhandled internal error triggered 500 instead of RFC-compliant 404 response",
              traceId: "nl_tr_4821_f1",
              duration: "2.1s",
            },
          ]);
          setStatus("recovering");
          setStepIndex(3);
        },
      },
      {
        delay: 6000,
        action: () => {
          setLogMessages((prev) => [
            ...prev,
            "[Recovery] Inspecting neatlogs trace nl_tr_4821_f1...",
            "[Recovery] Root cause diagnosed: direct re-raise bypasses FastAPI custom exception handlers",
            "[Recovery] Strategy shift: wrap routing dispatch in fallback middleware layer with status mapping",
            "[Implementer] Applying recovered patch via Entire checkpoint ckp_torque_rec02...",
          ]);
          setStatus("implementing");
          setStepIndex(4);
        },
      },
      {
        delay: 8500,
        action: () => {
          setLogMessages((prev) => [
            ...prev,
            "[Verifier] Rerunning test suite: pytest tests/test_routing.py...",
            "✅ [Verifier] All 15 tests PASSED (0 regressions)",
            "[Verifier] Generating PR description with neatlogs trace diff & cfo.ai unit cost...",
          ]);
          setAttempts((prev) => [
            ...prev,
            {
              number: 2,
              strategy: "Fallback middleware exception mapper (Recovered)",
              status: "passed",
              detail: "Safely intercepts missing routes without interfering with user-defined handlers",
              traceId: "nl_tr_4821_rec2",
              duration: "1.8s",
            },
          ]);
          setStatus("verifying");
          setStepIndex(5);
        },
      },
      {
        delay: 10500,
        action: () => {
          setLogMessages((prev) => [
            ...prev,
            "[Verifier] PR created: https://github.com/tiangolo/fastapi/pull/4822",
            "[Torque] Run completed successfully with self-healing recovery!",
          ]);
          setStatus("completed");
          setStepIndex(6);
          setPrCreated(true);
        },
      },
    ];

    timeline.forEach((step) => {
      setTimeout(step.action, step.delay);
    });
  };

  const handleSelectPreset = (url: string) => {
    setIssueUrl(url);
    if (status !== "idle") {
      resetRun();
    }
  };

  return (
    <SonarGrid
      id="torque-main-viewport"
      color="#F0813A"
      baseOpacity={0.22}
      dotRadius={1.3}
      spacing={26}
      pingEvery={2.4}
      speed={260}
      ringWidth={90}
      amplitude={2.2}
      interactive={true}
      seedPing={true}
      className="min-h-screen w-full bg-[#0D1117] text-[#E6EDF3] selection:bg-[#F0813A]/30 selection:text-[#FA924D] relative flex flex-col font-sans"
    >
      {/* Background vignette wash */}
      <div
        aria-hidden="true"
        className="pointer-events-none fixed inset-0 -z-10 bg-[radial-gradient(circle_at_50%_0%,rgba(240,129,58,0.12)_0%,transparent_60%)]"
      />

      {/* Top Header */}
      <header className="sticky top-0 z-40 w-full border-b border-white/[0.07] bg-[#0D1117]/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-8">
          {/* Brand */}
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#F0813A]/10 border border-[#F0813A]/30 text-[#F0813A] shadow-[0_0_15px_rgba(240,129,58,0.2)]">
              <svg
                viewBox="0 0 32 32"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5"
                aria-hidden="true"
              >
                <circle cx="16" cy="16" r="13" stroke="currentColor" strokeWidth="2.5" />
                <path
                  d="M16 8 L16 16 L22 20"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                <circle cx="16" cy="16" r="2.5" fill="currentColor" />
              </svg>
            </div>
            <div className="flex flex-col">
              <span className="text-lg font-bold tracking-tight text-[#E6EDF3] flex items-center gap-2">
                Torque
                <span className="rounded-full bg-[#F0813A]/15 border border-[#F0813A]/30 px-2 py-0.5 text-[10px] font-mono uppercase text-[#F0813A]">
                  neatHack
                </span>
              </span>
            </div>
          </div>

          {/* Navigation Controls */}
          <div className="flex items-center gap-3">
            {/* View switcher */}
            <div className="flex rounded-full border border-white/10 bg-[#161B22]/70 p-1 text-xs">
              <button
                type="button"
                id="view-toggle-app"
                onClick={() => setViewMode("torque")}
                className={`rounded-full px-3 py-1 font-medium transition-all ${
                  viewMode === "torque"
                    ? "bg-[#F0813A] text-[#0D1117] shadow-sm"
                    : "text-zinc-400 hover:text-white"
                }`}
              >
                App Interface
              </button>
              <button
                type="button"
                id="view-toggle-demo"
                onClick={() => setViewMode("demo")}
                className={`rounded-full px-3 py-1 font-medium transition-all ${
                  viewMode === "demo"
                    ? "bg-[#F0813A] text-[#0D1117] shadow-sm"
                    : "text-zinc-400 hover:text-white"
                }`}
              >
                Component Demo
              </button>
            </div>

            {/* Run Status Pill */}
            <div
              id="status-chip"
              className="hidden sm:inline-flex items-center gap-2 rounded-full border border-white/10 bg-[#161B22] px-3 py-1 text-xs font-mono"
            >
              <span
                className={`h-2 w-2 rounded-full ${
                  status === "idle"
                    ? "bg-zinc-500"
                    : status === "completed"
                    ? "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]"
                    : "bg-[#F0813A] animate-ping shadow-[0_0_8px_rgba(240,129,58,0.8)]"
                }`}
              />
              <span className="capitalize text-zinc-300">
                {status === "idle" ? "Idle" : status}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      {viewMode === "demo" ? (
        <main className="flex-1">
          <Demo />
        </main>
      ) : (
        <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-8 py-8 md:py-12 flex flex-col gap-10">
          {/* Hero Section */}
          <section className="flex flex-col items-center text-center max-w-3xl mx-auto pt-4 pb-2">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-[#F0813A]/30 bg-[#F0813A]/10 px-3.5 py-1 text-xs font-medium text-[#F0813A]">
              <span className="h-1.5 w-1.5 rounded-full bg-[#F0813A] animate-pulse" />
              MULTI-AGENT AUTONOMOUS RECOVERY
            </div>

            <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight text-balance text-[#E6EDF3] leading-[1.15]">
              Turn a GitHub issue into a{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#F0813A] via-[#FA924D] to-[#FFAB70]">
                verified pull request.
              </span>
            </h1>

            <p className="mt-5 text-base sm:text-lg text-zinc-400 max-w-2xl text-pretty">
              Torque investigates code with <strong className="text-zinc-200">Entire</strong>, implements
              fixes, runs tests, and opens a PR. When an attempt fails, our{" "}
              <strong className="text-[#F0813A]">Recovery agent</strong> inspects{" "}
              <strong className="text-zinc-200">neatlogs</strong> traces, alters strategy, and self-heals.
            </p>
          </section>

          {/* Interactive Input Form */}
          <section className="w-full max-w-3xl mx-auto">
            <div className="glass-panel p-2.5 sm:p-3 rounded-2xl border border-white/10 shadow-2xl transition-all focus-within:border-[#F0813A]/50 focus-within:shadow-[0_0_30px_rgba(240,129,58,0.15)]">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  if (status === "idle") startSimulation();
                }}
                className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5"
              >
                <div className="relative flex-1 flex items-center">
                  <Search className="absolute left-4 h-4 w-4 text-zinc-500 pointer-events-none" />
                  <input
                    type="url"
                    id="issue-url-input"
                    value={issueUrl}
                    onChange={(e) => setIssueUrl(e.target.value)}
                    placeholder="https://github.com/owner/repo/issues/123"
                    required
                    className="w-full rounded-xl bg-[#0D1117]/60 py-3.5 pl-11 pr-4 text-sm text-[#E6EDF3] placeholder:text-zinc-500 outline-none transition-colors border border-transparent focus:border-white/10 font-mono"
                  />
                </div>

                <div className="flex items-center gap-2">
                  {status !== "idle" && (
                    <button
                      type="button"
                      id="reset-run-btn"
                      onClick={resetRun}
                      className="inline-flex h-12 w-12 items-center justify-center rounded-xl border border-white/10 bg-[#161B22] text-zinc-300 hover:text-white hover:border-white/20 transition-all"
                      title="Reset Run"
                    >
                      <RotateCcw className="h-4 w-4" />
                    </button>
                  )}

                  <button
                    type="submit"
                    id="run-torque-btn"
                    disabled={status !== "idle" && status !== "completed"}
                    className="flex-1 sm:flex-none inline-flex h-12 cursor-pointer items-center justify-center gap-2 rounded-xl bg-[#F0813A] px-6 text-sm font-semibold text-[#0D1117] shadow-lg shadow-[#F0813A]/20 transition-all hover:bg-[#FA924D] hover:shadow-[#F0813A]/30 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {status === "idle" ? (
                      <>
                        <span>Run Torque</span>
                        <ArrowRight className="h-4 w-4" />
                      </>
                    ) : status === "completed" ? (
                      <>
                        <span>Run Again</span>
                        <Play className="h-4 w-4" />
                      </>
                    ) : (
                      <>
                        <span className="h-4 w-4 rounded-full border-2 border-[#0D1117] border-t-transparent animate-spin" />
                        <span>Running...</span>
                      </>
                    )}
                  </button>
                </div>
              </form>

              {/* Sample Presets */}
              <div className="mt-3 pt-3 border-t border-white/[0.06] flex flex-wrap items-center gap-2 px-2 text-xs">
                <span className="text-zinc-500 font-mono">Try fixture:</span>
                {PRESET_ISSUES.map((preset, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleSelectPreset(preset.url)}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-white/[0.08] bg-[#0D1117]/50 px-2.5 py-1 text-zinc-300 hover:border-[#F0813A]/40 hover:text-white transition-all text-left"
                  >
                    <span className="h-1.5 w-1.5 rounded-full bg-[#F0813A]" />
                    <span>{preset.title}</span>
                  </button>
                ))}
              </div>
            </div>
          </section>

          {/* Live Multi-Agent Pipeline Visualization */}
          {status !== "idle" && (
            <section className="w-full max-w-4xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-500 flex flex-col gap-6">
              {/* Agent Pipeline Steps */}
              <div className="glass-panel p-6 rounded-2xl border border-white/10 flex flex-col gap-6">
                <div className="flex items-center justify-between">
                  <h2 className="text-sm font-mono uppercase tracking-wider text-zinc-400 flex items-center gap-2">
                    <Terminal className="h-4 w-4 text-[#F0813A]" />
                    Live Orchestration Pipeline
                  </h2>
                  <span className="text-xs font-mono text-[#F0813A]">
                    {status === "completed"
                      ? "2/2 Attempts · Recovered ✅"
                      : `Step ${stepIndex}/5 Active`}
                  </span>
                </div>

                {/* Steps Bar */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {/* Investigator */}
                  <div
                    className={`p-3.5 rounded-xl border transition-all ${
                      status === "investigating"
                        ? "border-[#F0813A] bg-[#F0813A]/10 shadow-[0_0_15px_rgba(240,129,58,0.2)]"
                        : stepIndex > 1
                        ? "border-emerald-500/30 bg-emerald-500/5 text-zinc-300"
                        : "border-white/5 bg-[#0D1117]/40 text-zinc-500"
                    }`}
                  >
                    <div className="flex items-center justify-between text-xs mb-1.5">
                      <span className="font-mono">01 Investigator</span>
                      {stepIndex > 1 ? (
                        <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                      ) : status === "investigating" ? (
                        <span className="h-2 w-2 rounded-full bg-[#F0813A] animate-ping" />
                      ) : null}
                    </div>
                    <p className="text-xs font-semibold text-zinc-200">Entire Graph Search</p>
                  </div>

                  {/* Implementer */}
                  <div
                    className={`p-3.5 rounded-xl border transition-all ${
                      status === "implementing"
                        ? "border-[#F0813A] bg-[#F0813A]/10 shadow-[0_0_15px_rgba(240,129,58,0.2)]"
                        : stepIndex > 4
                        ? "border-emerald-500/30 bg-emerald-500/5 text-zinc-300"
                        : "border-white/5 bg-[#0D1117]/40 text-zinc-500"
                    }`}
                  >
                    <div className="flex items-center justify-between text-xs mb-1.5">
                      <span className="font-mono">02 Implementer</span>
                      {stepIndex > 4 ? (
                        <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                      ) : status === "implementing" ? (
                        <span className="h-2 w-2 rounded-full bg-[#F0813A] animate-ping" />
                      ) : null}
                    </div>
                    <p className="text-xs font-semibold text-zinc-200">Worktree & Pytest</p>
                  </div>

                  {/* Recovery */}
                  <div
                    className={`p-3.5 rounded-xl border transition-all ${
                      status === "recovering"
                        ? "border-[#F0813A] bg-[#F0813A]/15 shadow-[0_0_20px_rgba(240,129,58,0.3)] animate-pulse"
                        : attempts.some((a) => a.number === 2)
                        ? "border-emerald-500/30 bg-emerald-500/5 text-zinc-300"
                        : "border-white/5 bg-[#0D1117]/40 text-zinc-500"
                    }`}
                  >
                    <div className="flex items-center justify-between text-xs mb-1.5">
                      <span className="font-mono text-[#F0813A]">03 Recovery</span>
                      {status === "recovering" ? (
                        <AlertTriangle className="h-4 w-4 text-[#F0813A] animate-bounce" />
                      ) : attempts.some((a) => a.number === 2) ? (
                        <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                      ) : null}
                    </div>
                    <p className="text-xs font-semibold text-zinc-200">neatlogs Trace Healer</p>
                  </div>

                  {/* Verifier */}
                  <div
                    className={`p-3.5 rounded-xl border transition-all ${
                      status === "verifying"
                        ? "border-[#F0813A] bg-[#F0813A]/10 shadow-[0_0_15px_rgba(240,129,58,0.2)]"
                        : status === "completed"
                        ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-300"
                        : "border-white/5 bg-[#0D1117]/40 text-zinc-500"
                    }`}
                  >
                    <div className="flex items-center justify-between text-xs mb-1.5">
                      <span className="font-mono">04 Verifier</span>
                      {status === "completed" ? (
                        <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                      ) : status === "verifying" ? (
                        <span className="h-2 w-2 rounded-full bg-[#F0813A] animate-ping" />
                      ) : null}
                    </div>
                    <p className="text-xs font-semibold text-zinc-200">Diff & Pull Request</p>
                  </div>
                </div>

                {/* Console Execution Log */}
                <div className="rounded-xl bg-[#090D12] border border-white/5 p-4 font-mono text-xs text-zinc-300 max-h-48 overflow-y-auto space-y-1.5 shadow-inner">
                  {logMessages.map((msg, i) => (
                    <div
                      key={i}
                      className={
                        msg.includes("FAIL")
                          ? "text-rose-400"
                          : msg.includes("PASSED") || msg.includes("PR created")
                          ? "text-emerald-400"
                          : msg.includes("[Recovery]")
                          ? "text-[#FA924D]"
                          : "text-zinc-400"
                      }
                    >
                      {msg}
                    </div>
                  ))}
                </div>
              </div>

              {/* Attempts Comparison Table */}
              {attempts.length > 0 && (
                <div className="glass-panel p-6 rounded-2xl border border-white/10 flex flex-col gap-4">
                  <h3 className="text-sm font-mono uppercase tracking-wider text-zinc-300 flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-[#F0813A]" />
                    Attempt History & Trace Comparison
                  </h3>

                  <div className="grid gap-3">
                    {attempts.map((att) => (
                      <div
                        key={att.number}
                        className={`p-4 rounded-xl border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 ${
                          att.status === "failed"
                            ? "border-rose-500/30 bg-rose-500/[0.04]"
                            : "border-emerald-500/30 bg-emerald-500/[0.04]"
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <span
                            className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                              att.status === "failed"
                                ? "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                                : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                            }`}
                          >
                            #{att.number}
                          </span>
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-sm text-zinc-200">
                                {att.strategy}
                              </span>
                              <span
                                className={`rounded px-1.5 py-0.5 text-[10px] uppercase font-mono ${
                                  att.status === "failed"
                                    ? "bg-rose-500/20 text-rose-300"
                                    : "bg-emerald-500/20 text-emerald-300"
                                }`}
                              >
                                {att.status}
                              </span>
                            </div>
                            <p className="text-xs text-zinc-400 mt-0.5">{att.detail}</p>
                          </div>
                        </div>

                        <div className="flex items-center gap-3 font-mono text-xs text-zinc-400">
                          <span className="rounded bg-white/5 px-2 py-1">
                            neatlogs: {att.traceId}
                          </span>
                          <span>{att.duration}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Final PR Card Result */}
              {prCreated && (
                <div className="glass-panel-amber p-6 rounded-2xl flex flex-col gap-4 animate-in zoom-in-95 duration-500">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-emerald-400 font-mono text-xs uppercase font-bold tracking-wider">
                      <CheckCircle2 className="h-4 w-4" />
                      Verification Complete · PR Opened
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="rounded-full bg-white/10 px-2.5 py-0.5 text-[10px] font-mono text-zinc-300">
                        Entire Checkpoint: ckp_torque_rec02
                      </span>
                    </div>
                  </div>

                  <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pt-2">
                    <div>
                      <h4 className="text-xl font-bold text-white flex items-center gap-2">
                        <GitPullRequest className="h-5 w-5 text-[#F0813A]" />
                        tiangolo/fastapi #4822
                      </h4>
                      <p className="text-sm text-zinc-300 mt-1">
                        fix: route dispatch fallback middleware to preserve custom 404 handlers
                      </p>
                    </div>

                    <a
                      href="https://github.com/tiangolo/fastapi/pull/4821"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 rounded-xl bg-[#F0813A] px-5 py-2.5 text-xs font-bold text-[#0D1117] hover:bg-[#FA924D] transition-all shadow-md shadow-[#F0813A]/20"
                    >
                      <span>View Pull Request</span>
                      <ExternalLink className="h-3.5 w-3.5" />
                    </a>
                  </div>
                </div>
              )}
            </section>
          )}

          {/* How It Works: 4 Agent Architectural Overview */}
          <section className="w-full max-w-5xl mx-auto pt-6">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-[#E6EDF3] tracking-tight">
                Autonomous Recovery Architecture
              </h2>
              <p className="text-sm text-zinc-400 mt-2">
                Four specialized agents collaborating in an automated feedback loop.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Investigator */}
              <div className="glass-panel p-5 rounded-2xl border border-white/5 hover:border-[#F0813A]/40 transition-all flex flex-col justify-between group">
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <span className="font-mono text-xs text-[#F0813A] font-bold">01</span>
                    <Search className="h-4 w-4 text-zinc-500 group-hover:text-[#F0813A] transition-colors" />
                  </div>
                  <h3 className="font-bold text-base text-white">Investigator</h3>
                  <p className="text-xs text-zinc-400 mt-2 leading-relaxed">
                    Parses the issue ticket and runs code graph queries via Entire for pinpoint
                    source context.
                  </p>
                </div>
                <div className="mt-4 pt-3 border-t border-white/5 text-[11px] font-mono text-[#F0813A]">
                  Entire Search & Graph
                </div>
              </div>

              {/* Implementer */}
              <div className="glass-panel p-5 rounded-2xl border border-white/5 hover:border-[#F0813A]/40 transition-all flex flex-col justify-between group">
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <span className="font-mono text-xs text-[#F0813A] font-bold">02</span>
                    <Wrench className="h-4 w-4 text-zinc-500 group-hover:text-[#F0813A] transition-colors" />
                  </div>
                  <h3 className="font-bold text-base text-white">Implementer</h3>
                  <p className="text-xs text-zinc-400 mt-2 leading-relaxed">
                    Executes code edits in an isolated worktree and triggers test suites for
                    immediate feedback.
                  </p>
                </div>
                <div className="mt-4 pt-3 border-t border-white/5 text-[11px] font-mono text-[#F0813A]">
                  Isolated Git Worktree
                </div>
              </div>

              {/* Recovery */}
              <div className="glass-panel p-5 rounded-2xl border border-[#F0813A]/30 bg-[#F0813A]/[0.03] hover:border-[#F0813A] transition-all flex flex-col justify-between group">
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <span className="font-mono text-xs text-[#F0813A] font-bold">03</span>
                    <RotateCcw className="h-4 w-4 text-[#F0813A] group-hover:rotate-180 transition-transform duration-500" />
                  </div>
                  <h3 className="font-bold text-base text-white">Recovery</h3>
                  <p className="text-xs text-zinc-400 mt-2 leading-relaxed">
                    When tests fail, reads neatlogs trace spans, analyzes error causality, and formulates
                    an alternate fix.
                  </p>
                </div>
                <div className="mt-4 pt-3 border-t border-white/5 text-[11px] font-mono text-[#F0813A]">
                  neatlogs Trace Analysis
                </div>
              </div>

              {/* Verifier */}
              <div className="glass-panel p-5 rounded-2xl border border-white/5 hover:border-[#F0813A]/40 transition-all flex flex-col justify-between group">
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <span className="font-mono text-xs text-[#F0813A] font-bold">04</span>
                    <ShieldCheck className="h-4 w-4 text-zinc-500 group-hover:text-[#F0813A] transition-colors" />
                  </div>
                  <h3 className="font-bold text-base text-white">Verifier</h3>
                  <p className="text-xs text-zinc-400 mt-2 leading-relaxed">
                    Validates unified diffs against ticket criteria and authors a pull request with
                    reproducible traces.
                  </p>
                </div>
                <div className="mt-4 pt-3 border-t border-white/5 text-[11px] font-mono text-[#F0813A]">
                  Verification & PR Opening
                </div>
              </div>
            </div>
          </section>

          {/* Interactive Hint */}
          <div className="text-center py-4">
            <p className="text-xs font-mono text-zinc-500 inline-flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-[#F0813A]" />
              Tap or click anywhere on the background to send a Sonar wave ping
            </p>
          </div>
        </main>
      )}

      {/* Footer */}
      <footer className="w-full border-t border-white/[0.07] bg-[#0D1117]/80 backdrop-blur-md py-6 mt-auto">
        <div className="mx-auto flex max-w-7xl flex-col sm:flex-row items-center justify-between gap-4 px-4 sm:px-8 text-xs text-zinc-500">
          <div className="flex items-center gap-2">
            <span>Built for neatHack · October 2026</span>
          </div>
          <div className="flex items-center gap-4 font-mono">
            <span>neatlogs</span>
            <span>·</span>
            <span>Entire</span>
            <span>·</span>
            <span>cfo.ai</span>
          </div>
        </div>
      </footer>
    </SonarGrid>
  );
}
