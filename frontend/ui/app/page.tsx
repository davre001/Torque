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
  Layers,
} from "lucide-react";
import { SonarGrid } from "@/components/ui/sonar-grid";
import Demo from "@/components/ui/sonar-grid-demo";
import HeaderDemo from "@/components/ui/header-2-demo";
import { Button, buttonVariants } from "@/components/ui/button";
import { MenuToggleIcon } from "@/components/ui/menu-toggle-icon";
import { useScroll } from "@/components/ui/use-scroll";
import { cn } from "@/lib/utils";

type AgentStatus =
  | "idle"
  | "queued"
  | "investigating"
  | "implementing"
  | "recovering"
  | "verifying"
  | "completed"
  | "failed";

interface AttemptRecord {
  number: number;
  status: "failed" | "passed" | "running";
  trace_id: string;
  summary: string;
  detail: string;
  duration?: string;
}

const PRESET_ISSUES = [
  {
    title: "FastAPI 404 router handler bug",
    url: "https://github.com/tiangolo/fastapi/issues/4821",
    scenario: "Fails Attempt 1 (direct re-raise) → Recovers Attempt 2 (fallback middleware)",
  },
  {
    title: "SQLAlchemy async pool deadlock",
    url: "https://github.com/sqlalchemy/sqlalchemy/issues/8912",
    scenario: "Fails Attempt 1 (hard reconnect) → Recovers Attempt 2 (exponential backoff)",
  },
];

export default function TorquePage() {
  const [viewMode, setViewMode] = React.useState<"torque" | "sonar-demo" | "header-demo">("torque");
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);
  const scrolled = useScroll(12);

  const [issueUrl, setIssueUrl] = React.useState(
    "https://github.com/tiangolo/fastapi/issues/4821"
  );
  const [status, setStatus] = React.useState<AgentStatus>("idle");
  const [currentAgent, setCurrentAgent] = React.useState<string | null>(null);
  const [attempts, setAttempts] = React.useState<AttemptRecord[]>([]);
  const [logMessages, setLogMessages] = React.useState<string[]>([]);
  const [prUrl, setPrUrl] = React.useState<string | null>(null);
  const [planSummary, setPlanSummary] = React.useState<string | null>(null);
  const timerRef = React.useRef<NodeJS.Timeout[]>([]);
  const inputSectionRef = React.useRef<HTMLDivElement | null>(null);

  // Check URL query parameters for ?demo=1 on initial load (implementation.md spec)
  React.useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      if (params.get("demo") === "1") {
        setIssueUrl("https://github.com/tiangolo/fastapi/issues/4821");
      }
    }
  }, []);

  // Lock body scroll when mobile menu is open
  React.useEffect(() => {
    if (mobileMenuOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileMenuOpen]);

  const clearTimers = () => {
    timerRef.current.forEach((t) => clearTimeout(t));
    timerRef.current = [];
  };

  const resetRun = () => {
    clearTimers();
    setStatus("idle");
    setCurrentAgent(null);
    setAttempts([]);
    setLogMessages([]);
    setPrUrl(null);
    setPlanSummary(null);
  };

  // Autonomous simulation following implementation.md spec:
  // investigating -> implementing -> recovering -> verifying -> completed
  const startRun = () => {
    resetRun();
    setStatus("queued");
    setLogMessages(["[System] Run queued: run_20261011_001. Starting agent dispatch..."]);

    const schedule = (delay: number, fn: () => void) => {
      const t = setTimeout(fn, delay);
      timerRef.current.push(t);
    };

    // 1. Investigator
    schedule(800, () => {
      setStatus("investigating");
      setCurrentAgent("investigator");
      setLogMessages((prev) => [
        ...prev,
        "[Investigator] Parsing ticket context & query parameters...",
        "[Investigator] Entire index search completed: 3 relevant call sites located in src/routing.py and tests/test_routing.py",
      ]);
    });

    // 2. Implementer (Attempt 1)
    schedule(2600, () => {
      setStatus("implementing");
      setCurrentAgent("implementer");
      setAttempts([
        {
          number: 1,
          status: "running",
          trace_id: "nl_tr_4821_f1",
          summary: "Direct router exception re-raise",
          detail: "Attempting patch in isolated worktree...",
        },
      ]);
      setLogMessages((prev) => [
        ...prev,
        "[Implementer] Worktree torque/worktree-patch-4821 created.",
        "[Implementer] Naive patch applied: directly re-raise unhandled route error in Starlette router.",
        "[Implementer] Executing tests: pytest tests/test_routing.py...",
      ]);
    });

    // 3. Test Failure & Recovery Trigger (Attempt 1 Fails)
    schedule(5000, () => {
      setStatus("recovering");
      setCurrentAgent("recovery");
      setAttempts([
        {
          number: 1,
          status: "failed",
          trace_id: "nl_tr_4821_f1",
          summary: "Wrong router level edited (AssertionError in test_routing)",
          detail: "Direct re-raise bypassed custom Starlette 404 exception handlers, triggering 500 response",
          duration: "2.1s",
        },
        {
          number: 2,
          status: "running",
          trace_id: "nl_tr_4821_rec2",
          summary: "Strategy pivot: Fallback middleware exception mapper",
          detail: "Recovery agent analyzing neatlogs trace span...",
        },
      ]);
      setLogMessages((prev) => [
        ...prev,
        "⚠️ [Pytest] FAIL: 1 failed, 14 passed (AssertionError: Expected status 404, received 500)",
        "[neatlogs] Failure span recorded: trace_id=nl_tr_4821_f1",
        "[Recovery] Inspecting neatlogs trace nl_tr_4821_f1...",
        "[Recovery] Root cause diagnosed: direct re-raise bypasses FastAPI application-level exception handlers",
        "[Recovery] Strategy shift: Wrap routing dispatch in fallback middleware layer with status mapping",
      ]);
    });

    // 4. Implementer Retry with Checkpoint (Attempt 2)
    schedule(7600, () => {
      setStatus("implementing");
      setCurrentAgent("implementer");
      setLogMessages((prev) => [
        ...prev,
        "[Implementer] Applying recovered strategy via Entire checkpoint ckp_torque_rec02...",
        "[Implementer] Patch applied: middleware route interceptor installed.",
        "[Implementer] Rerunning test suite: pytest tests/test_routing.py...",
      ]);
    });

    // 5. Verifier (Attempt 2 Passes)
    schedule(9800, () => {
      setStatus("verifying");
      setCurrentAgent("verifier");
      setAttempts([
        {
          number: 1,
          status: "failed",
          trace_id: "nl_tr_4821_f1",
          summary: "Wrong router level edited (AssertionError in test_routing)",
          detail: "Direct re-raise bypassed custom Starlette 404 exception handlers, triggering 500 response",
          duration: "2.1s",
        },
        {
          number: 2,
          status: "passed",
          trace_id: "nl_tr_4821_rec2",
          summary: "Fallback middleware exception mapper (Passed)",
          detail: "Safely intercepts missing routes without interfering with user-defined handlers",
          duration: "1.7s",
        },
      ]);
      setLogMessages((prev) => [
        ...prev,
        "✅ [Verifier] All 15 tests PASSED (0 regressions)",
        "[Verifier] Validating unified diff against issue acceptance criteria...",
        "[Verifier] Authoring pull request and attaching neatlogs before/after trace evidence...",
      ]);
    });

    // 6. Completed with Final PR Link
    schedule(11800, () => {
      setStatus("completed");
      setCurrentAgent(null);
      setPrUrl("https://github.com/tiangolo/fastapi/pull/4822");
      setPlanSummary(
        "Update routing dispatch with fallback middleware to preserve RFC-compliant 404 status codes and user-defined handlers."
      );
      setLogMessages((prev) => [
        ...prev,
        "🎉 [Verifier] Pull Request opened: https://github.com/tiangolo/fastapi/pull/4822",
        "[Torque] Run complete. Self-healing agent recovery verified.",
      ]);
    });
  };

  const handleSelectPreset = (url: string) => {
    setIssueUrl(url);
    if (status !== "idle") resetRun();
  };

  const scrollToInput = () => {
    inputSectionRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <SonarGrid
      id="torque-viewport"
      color="#000000"
      baseOpacity={0.16}
      dotRadius={1.3}
      spacing={26}
      pingEvery={2.4}
      speed={260}
      ringWidth={90}
      amplitude={2.0}
      interactive={true}
      seedPing={true}
      className="min-h-screen w-full bg-white text-zinc-950 selection:bg-black selection:text-white relative flex flex-col font-sans"
    >
      {/* Soft radial wash in white */}
      <div
        aria-hidden="true"
        className="pointer-events-none fixed inset-0 -z-10 bg-[radial-gradient(ellipse_60%_50%_at_50%_0%,rgba(255,255,255,0.95)_0%,rgba(255,255,255,0.6)_100%)]"
      />

      {/* Floating Island Header with Scroll Effect & Glassmorphism */}
      <header
        className={cn(
          "sticky top-0 z-50 mx-auto w-full max-w-5xl border-b border-transparent md:rounded-2xl md:border md:transition-all md:duration-300 md:ease-out",
          {
            "bg-white/80 supports-[backdrop-filter]:bg-white/65 border-black/10 backdrop-blur-xl md:top-4 md:max-w-4xl md:shadow-lg shadow-black/5":
              scrolled && !mobileMenuOpen,
            "bg-white/95 border-b border-black/10": mobileMenuOpen,
            "bg-white/40 border-b border-black/[0.06]": !scrolled && !mobileMenuOpen,
          }
        )}
      >
        <nav
          className={cn(
            "flex h-16 w-full items-center justify-between px-4 sm:px-6 md:transition-all md:duration-300 md:ease-out",
            {
              "md:h-13 md:px-4": scrolled,
            }
          )}
        >
          {/* Brand Logo */}
          <div className="flex items-center gap-2.5">
            <img
              src="/logo.png"
              alt="Torque Logo"
              className="h-8 w-8 object-contain transition-transform duration-300 hover:rotate-12 cursor-pointer"
            />
            <div className="flex items-center gap-1.5">
              <span className="text-base font-bold tracking-tight text-black">Torque</span>
              <span className="glass-pill rounded-full px-2 py-0.5 text-[9px] font-mono uppercase tracking-wider text-zinc-700 font-semibold">
                neatHack
              </span>
            </div>
          </div>

          {/* Center Navigation Links (Hidden on mobile) */}
          <div className="hidden md:flex items-center gap-1">
            <button
              type="button"
              onClick={() => setViewMode("torque")}
              className={buttonVariants({
                variant: viewMode === "torque" ? "secondary" : "ghost",
                size: "sm",
                className: cn(
                  "text-xs font-medium cursor-pointer transition-colors",
                  viewMode === "torque" ? "bg-black text-white hover:bg-black/90 hover:text-white" : "text-zinc-600 hover:text-black"
                ),
              })}
            >
              App Interface
            </button>
            <button
              type="button"
              onClick={() => setViewMode("sonar-demo")}
              className={buttonVariants({
                variant: viewMode === "sonar-demo" ? "secondary" : "ghost",
                size: "sm",
                className: cn(
                  "text-xs font-medium cursor-pointer transition-colors",
                  viewMode === "sonar-demo" ? "bg-black text-white hover:bg-black/90 hover:text-white" : "text-zinc-600 hover:text-black"
                ),
              })}
            >
              Sonar Demo
            </button>
            <button
              type="button"
              onClick={() => setViewMode("header-demo")}
              className={buttonVariants({
                variant: viewMode === "header-demo" ? "secondary" : "ghost",
                size: "sm",
                className: cn(
                  "text-xs font-medium cursor-pointer transition-colors",
                  viewMode === "header-demo" ? "bg-black text-white hover:bg-black/90 hover:text-white" : "text-zinc-600 hover:text-black"
                ),
              })}
            >
              Header Demo
            </button>
          </div>

          {/* Right Action & Status Area */}
          <div className="hidden sm:flex items-center gap-2.5">
            {/* Live Status Pill */}
            <div
              id="status-badge"
              className="glass-pill inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-mono"
            >
              <span
                className={`h-2 w-2 rounded-full ${
                  status === "idle"
                    ? "bg-zinc-400"
                    : status === "completed"
                    ? "bg-black shadow-[0_0_6px_rgba(0,0,0,0.5)]"
                    : "bg-black animate-ping"
                }`}
              />
              <span className="capitalize font-medium text-zinc-900">
                {status === "idle" ? "Idle" : status}
              </span>
            </div>

            <Button
              size="sm"
              onClick={scrollToInput}
              className="glass-btn-primary rounded-xl text-xs h-8 px-3.5 cursor-pointer"
            >
              <span>Run Torque</span>
              <ArrowRight className="h-3 w-3 ml-1" />
            </Button>
          </div>

          {/* Mobile Menu Toggle Button */}
          <Button
            size="icon"
            variant="outline"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden h-9 w-9 border-black/10 bg-white/70 backdrop-blur-md"
            aria-label="Toggle navigation menu"
          >
            <MenuToggleIcon open={mobileMenuOpen} className="size-4" duration={300} />
          </Button>
        </nav>

        {/* Mobile Slide-down Drawer */}
        <div
          className={cn(
            "bg-white/95 backdrop-blur-2xl fixed top-16 right-0 bottom-0 left-0 z-50 flex flex-col overflow-hidden border-y border-black/10 md:hidden transition-all duration-300",
            mobileMenuOpen ? "block" : "hidden"
          )}
        >
          <div className="flex h-full w-full flex-col justify-between p-6 gap-y-4">
            <div className="grid gap-y-2">
              <button
                type="button"
                onClick={() => {
                  setViewMode("torque");
                  setMobileMenuOpen(false);
                }}
                className={buttonVariants({
                  variant: viewMode === "torque" ? "secondary" : "ghost",
                  className: "justify-start text-sm font-medium",
                })}
              >
                App Interface
              </button>
              <button
                type="button"
                onClick={() => {
                  setViewMode("sonar-demo");
                  setMobileMenuOpen(false);
                }}
                className={buttonVariants({
                  variant: viewMode === "sonar-demo" ? "secondary" : "ghost",
                  className: "justify-start text-sm font-medium",
                })}
              >
                Sonar Grid Demo
              </button>
              <button
                type="button"
                onClick={() => {
                  setViewMode("header-demo");
                  setMobileMenuOpen(false);
                }}
                className={buttonVariants({
                  variant: viewMode === "header-demo" ? "secondary" : "ghost",
                  className: "justify-start text-sm font-medium",
                })}
              >
                Header Component Demo
              </button>
            </div>

            <div className="flex flex-col gap-2 pt-4 border-t border-black/10">
              <Button
                variant="outline"
                className="w-full text-sm"
                onClick={() => {
                  setMobileMenuOpen(false);
                  resetRun();
                }}
              >
                Reset Run
              </Button>
              <Button
                className="w-full text-sm glass-btn-primary"
                onClick={() => {
                  setMobileMenuOpen(false);
                  startRun();
                }}
              >
                Run Torque Demo
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area based on View Mode */}
      {viewMode === "sonar-demo" ? (
        <main className="flex-1">
          <Demo />
        </main>
      ) : viewMode === "header-demo" ? (
        <main className="flex-1">
          <HeaderDemo />
        </main>
      ) : (
        <main className="flex-1 w-full max-w-5xl mx-auto px-4 sm:px-8 py-8 md:py-12 flex flex-col gap-8">
          {/* Hero Section */}
          <section className="flex flex-col items-center text-center max-w-3xl mx-auto pt-2 pb-1">
            <div className="glass-pill mb-4 inline-flex items-center gap-2 rounded-full px-3.5 py-1 text-xs font-medium text-black">
              <span className="h-1.5 w-1.5 rounded-full bg-black animate-pulse" />
              MULTI-AGENT RECOVERY SYSTEM
            </div>

            <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight text-balance text-black leading-[1.12]">
              Turn a GitHub issue into a verified pull request
            </h1>

            <p className="mt-4 text-base sm:text-lg text-zinc-600 max-w-2xl text-pretty">
              An agent that investigates the codebase via Entire, implements a fix, runs tests, and
              opens a PR. If it fails, a Recovery agent reads the neatlogs trace, changes strategy,
              and retries.
            </p>
          </section>

          {/* Issue Input & Run Form */}
          <section ref={inputSectionRef} className="w-full max-w-3xl mx-auto">
            <div className="glass-input-container p-3 sm:p-3.5 rounded-2xl">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  if (status === "idle" || status === "completed") startRun();
                }}
                className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5"
              >
                <div className="relative flex-1 flex items-center">
                  <Search className="absolute left-4 h-4 w-4 text-zinc-400 pointer-events-none" />
                  <input
                    type="url"
                    id="issue-url-input"
                    value={issueUrl}
                    onChange={(e) => setIssueUrl(e.target.value)}
                    placeholder="https://github.com/org/repo/issues/42"
                    required
                    className="w-full rounded-xl bg-white/70 py-3.5 pl-11 pr-4 text-sm text-black placeholder:text-zinc-400 outline-none transition-colors border border-black/5 focus:border-black/30 font-mono"
                  />
                </div>

                <div className="flex items-center gap-2">
                  {status !== "idle" && (
                    <Button
                      type="button"
                      id="reset-run-btn"
                      variant="outline"
                      onClick={resetRun}
                      className="glass-btn-secondary h-12 w-12 rounded-xl p-0"
                      title="Reset run"
                    >
                      <RotateCcw className="h-4 w-4" />
                    </Button>
                  )}

                  <Button
                    type="submit"
                    id="run-torque-btn"
                    disabled={status !== "idle" && status !== "completed"}
                    className="glass-btn-primary flex-1 sm:flex-none h-12 rounded-xl px-6 text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {status === "idle" ? (
                      <>
                        <span>Run Torque</span>
                        <ArrowRight className="h-4 w-4 ml-1.5" />
                      </>
                    ) : status === "completed" ? (
                      <>
                        <span>Run Again</span>
                        <Play className="h-4 w-4 ml-1.5" />
                      </>
                    ) : (
                      <>
                        <span className="h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin mr-1.5" />
                        <span>Running Torque...</span>
                      </>
                    )}
                  </Button>
                </div>
              </form>

              {/* Quick Presets / Fixture Links */}
              <div className="mt-3 pt-3 border-t border-black/[0.06] flex flex-wrap items-center gap-2 px-1 text-xs">
                <span className="text-zinc-500 font-mono">Fixture presets:</span>
                {PRESET_ISSUES.map((preset, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleSelectPreset(preset.url)}
                    className="glass-pill inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-zinc-700 hover:text-black hover:border-black/25 transition-all text-left"
                  >
                    <span className="h-1.5 w-1.5 rounded-full bg-black" />
                    <span>{preset.title}</span>
                  </button>
                ))}
              </div>
            </div>
          </section>

          {/* Implementation.md Layout Section: Live Status, Pipeline, Attempts & Result */}
          {status !== "idle" && (
            <section className="w-full max-w-3xl mx-auto flex flex-col gap-6 animate-in fade-in slide-in-from-bottom-4 duration-400">
              {/* Single Screen Status & Pipeline Panel */}
              <div className="glass-panel p-6 rounded-2xl flex flex-col gap-5">
                <div className="flex items-center justify-between pb-3 border-b border-black/[0.07]">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs uppercase tracking-wider text-zinc-500 font-bold">
                      Status:
                    </span>
                    <span className="font-mono text-sm font-bold text-black capitalize">
                      {status === "recovering"
                        ? "Recovery · Attempt 2 of 3"
                        : status === "completed"
                        ? "Completed · Recovered ✅"
                        : `${status} · Step ${
                            status === "queued"
                              ? "0"
                              : status === "investigating"
                              ? "1"
                              : status === "implementing"
                              ? "2"
                              : status === "verifying"
                              ? "4"
                              : "5"
                          } of 4`}
                    </span>
                  </div>
                  <span className="text-xs font-mono text-zinc-500">
                    run_id: run_20261011_001
                  </span>
                </div>

                {/* 4 Agent Status Indicators (matching implementation.md layout) */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
                  {/* Investigator */}
                  <div className="glass-pill p-3.5 rounded-xl flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <span
                        className={`h-2.5 w-2.5 rounded-full ${
                          currentAgent === "investigator"
                            ? "bg-black animate-ping"
                            : status !== "queued"
                            ? "bg-black"
                            : "bg-zinc-300"
                        }`}
                      />
                      <span className="font-medium text-black">Investigator</span>
                    </div>
                    <span className="font-mono text-xs text-zinc-500">
                      {status !== "queued" && status !== "investigating" ? (
                        <CheckCircle2 className="h-4 w-4 text-black inline" />
                      ) : currentAgent === "investigator" ? (
                        "Searching Entire..."
                      ) : (
                        "Pending"
                      )}
                    </span>
                  </div>

                  {/* Implementer */}
                  <div className="glass-pill p-3.5 rounded-xl flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <span
                        className={`h-2.5 w-2.5 rounded-full ${
                          currentAgent === "implementer"
                            ? "bg-black animate-ping"
                            : attempts.length > 0
                            ? "bg-black"
                            : "bg-zinc-300"
                        }`}
                      />
                      <span className="font-medium text-black">Implementer</span>
                    </div>
                    <span className="font-mono text-xs text-zinc-500">
                      {attempts.some((a) => a.number === 2 && a.status === "passed") ? (
                        <CheckCircle2 className="h-4 w-4 text-black inline" />
                      ) : attempts.some((a) => a.status === "failed") ? (
                        "✓ (failed tests)"
                      ) : currentAgent === "implementer" ? (
                        "Running pytest..."
                      ) : (
                        "Pending"
                      )}
                    </span>
                  </div>

                  {/* Recovery */}
                  <div
                    className={`glass-pill p-3.5 rounded-xl flex items-center justify-between ${
                      status === "recovering" ? "border-black/40 bg-black/[0.04]" : ""
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <span
                        className={`h-2.5 w-2.5 rounded-full ${
                          status === "recovering"
                            ? "bg-black animate-bounce"
                            : attempts.some((a) => a.number === 2)
                            ? "bg-black"
                            : "bg-zinc-300"
                        }`}
                      />
                      <span className="font-medium text-black">Recovery</span>
                    </div>
                    <span className="font-mono text-xs text-zinc-500">
                      {status === "recovering" ? (
                        <span className="font-bold text-black animate-pulse">
                          → changing strategy…
                        </span>
                      ) : attempts.some((a) => a.number === 2) ? (
                        <CheckCircle2 className="h-4 w-4 text-black inline" />
                      ) : (
                        "On standby"
                      )}
                    </span>
                  </div>

                  {/* Verifier */}
                  <div className="glass-pill p-3.5 rounded-xl flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <span
                        className={`h-2.5 w-2.5 rounded-full ${
                          currentAgent === "verifier"
                            ? "bg-black animate-ping"
                            : status === "completed"
                            ? "bg-black"
                            : "bg-zinc-300"
                        }`}
                      />
                      <span className="font-medium text-black">Verifier</span>
                    </div>
                    <span className="font-mono text-xs text-zinc-500">
                      {status === "completed" ? (
                        <CheckCircle2 className="h-4 w-4 text-black inline" />
                      ) : currentAgent === "verifier" ? (
                        "Checking PR diff..."
                      ) : (
                        "Pending"
                      )}
                    </span>
                  </div>
                </div>

                {/* Live Console Output */}
                <div className="rounded-xl bg-zinc-950 p-4 font-mono text-xs text-zinc-200 max-h-40 overflow-y-auto space-y-1.5 shadow-inner">
                  {logMessages.map((msg, idx) => (
                    <div
                      key={idx}
                      className={
                        msg.includes("FAIL")
                          ? "text-rose-400"
                          : msg.includes("PASSED") || msg.includes("PR opened")
                          ? "text-emerald-400"
                          : msg.includes("[Recovery]")
                          ? "text-amber-300 font-semibold"
                          : "text-zinc-300"
                      }
                    >
                      {msg}
                    </div>
                  ))}
                </div>
              </div>

              {/* Attempts Table (as specified in implementation.md) */}
              {attempts.length > 0 && (
                <div className="glass-panel p-6 rounded-2xl flex flex-col gap-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-mono uppercase tracking-wider text-black font-bold flex items-center gap-2">
                      <Layers className="h-4 w-4" />
                      Attempts History
                    </h3>
                    <span className="text-xs text-zinc-500 font-mono">
                      neatlogs trace correlation
                    </span>
                  </div>

                  <div className="grid gap-2.5">
                    {attempts.map((att) => (
                      <div
                        key={att.number}
                        className={`glass-pill p-4 rounded-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 ${
                          att.status === "failed"
                            ? "border-rose-400/40 bg-rose-50/50"
                            : att.status === "passed"
                            ? "border-emerald-500/40 bg-emerald-50/40"
                            : "border-black/20 bg-zinc-50/70"
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <span
                            className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                              att.status === "failed"
                                ? "bg-rose-100 text-rose-700"
                                : att.status === "passed"
                                ? "bg-emerald-100 text-emerald-800"
                                : "bg-black text-white"
                            }`}
                          >
                            #{att.number}
                          </span>
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-sm text-black">
                                {att.summary}
                              </span>
                              <span
                                className={`rounded px-1.5 py-0.5 text-[10px] uppercase font-mono font-bold ${
                                  att.status === "failed"
                                    ? "bg-rose-200/70 text-rose-800"
                                    : att.status === "passed"
                                    ? "bg-emerald-200/70 text-emerald-800"
                                    : "bg-black text-white"
                                }`}
                              >
                                {att.status}
                              </span>
                            </div>
                            <p className="text-xs text-zinc-600 mt-0.5">{att.detail}</p>
                          </div>
                        </div>

                        <div className="flex items-center gap-3 font-mono text-xs text-zinc-500">
                          <span className="glass-pill px-2 py-1 rounded text-black font-semibold">
                            neatlogs: {att.trace_id}
                          </span>
                          {att.duration && <span>{att.duration}</span>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Final Result Panel (PR URL, neatlogs traces, Entire checkpoints) */}
              {prUrl && (
                <div className="glass-panel p-6 rounded-2xl flex flex-col gap-4 border-black/20 shadow-xl animate-in zoom-in-95 duration-400">
                  <div className="flex items-center justify-between pb-2 border-b border-black/[0.07]">
                    <div className="flex items-center gap-2 text-black font-mono text-xs uppercase font-bold tracking-wider">
                      <CheckCircle2 className="h-4 w-4" />
                      Result · Verified Pull Request
                    </div>
                    <span className="glass-pill px-2.5 py-0.5 rounded-full text-[10px] font-mono text-zinc-600 font-semibold">
                      Entire Checkpoint: ckp_torque_rec02
                    </span>
                  </div>

                  <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pt-1">
                    <div>
                      <h4 className="text-xl font-bold text-black flex items-center gap-2">
                        <GitPullRequest className="h-5 w-5 text-black" />
                        {prUrl.replace("https://github.com/", "")}
                      </h4>
                      {planSummary && (
                        <p className="text-sm text-zinc-600 mt-1 max-w-xl">{planSummary}</p>
                      )}
                    </div>

                    <a
                      href={prUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="glass-btn-primary inline-flex items-center gap-2 rounded-xl px-5 py-2.5 text-xs font-bold text-white shadow-md"
                    >
                      <span>Open Pull Request</span>
                      <ExternalLink className="h-3.5 w-3.5" />
                    </a>
                  </div>

                  <div className="pt-2 text-xs font-mono text-zinc-500 flex flex-wrap gap-4 border-t border-black/[0.06]">
                    <span>Traces: neatlogs nl_tr_4821_f1 ➔ nl_tr_4821_rec2</span>
                    <span>Checkpoints: Entire ckp_torque_rec02</span>
                    <span>cfo.ai Cost: $0.034</span>
                  </div>
                </div>
              )}
            </section>
          )}

          {/* 4 Agent Architecture Grid ("How It Works") */}
          <section id="how-it-works" className="w-full max-w-5xl mx-auto pt-6">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-black tracking-tight">
                How Torque Works
              </h2>
              <p className="text-sm text-zinc-600 mt-1.5">
                Multi-agent architecture built for neatHack with autonomous error recovery.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Investigator */}
              <div className="glass-panel-interactive p-5 rounded-2xl flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <span className="font-mono text-xs font-bold text-black">01</span>
                    <Search className="h-4 w-4 text-zinc-500" />
                  </div>
                  <h3 className="font-bold text-base text-black">Investigator</h3>
                  <p className="text-xs text-zinc-600 mt-2 leading-relaxed">
                    Reads the issue ticket and queries Entire for precise code context and dependency
                    graphs.
                  </p>
                </div>
                <div className="mt-4 pt-3 border-t border-black/5 text-[11px] font-mono text-zinc-700 font-semibold">
                  Entire Search & Graph
                </div>
              </div>

              {/* Implementer */}
              <div className="glass-panel-interactive p-5 rounded-2xl flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <span className="font-mono text-xs font-bold text-black">02</span>
                    <Wrench className="h-4 w-4 text-zinc-500" />
                  </div>
                  <h3 className="font-bold text-base text-black">Implementer</h3>
                  <p className="text-xs text-zinc-600 mt-2 leading-relaxed">
                    Applies source code edits in an isolated worktree and runs tests immediately.
                  </p>
                </div>
                <div className="mt-4 pt-3 border-t border-black/5 text-[11px] font-mono text-zinc-700 font-semibold">
                  Isolated Git Worktree
                </div>
              </div>

              {/* Recovery */}
              <div className="glass-panel-interactive p-5 rounded-2xl flex flex-col justify-between border-black/25">
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <span className="font-mono text-xs font-bold text-black">03</span>
                    <RotateCcw className="h-4 w-4 text-black" />
                  </div>
                  <h3 className="font-bold text-base text-black">Recovery</h3>
                  <p className="text-xs text-zinc-600 mt-2 leading-relaxed">
                    Inspects failed neatlogs trace spans, analyzes error patterns, and changes strategy.
                  </p>
                </div>
                <div className="mt-4 pt-3 border-t border-black/5 text-[11px] font-mono text-black font-semibold">
                  neatlogs Trace Analysis
                </div>
              </div>

              {/* Verifier */}
              <div className="glass-panel-interactive p-5 rounded-2xl flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <span className="font-mono text-xs font-bold text-black">04</span>
                    <ShieldCheck className="h-4 w-4 text-zinc-500" />
                  </div>
                  <h3 className="font-bold text-base text-black">Verifier</h3>
                  <p className="text-xs text-zinc-600 mt-2 leading-relaxed">
                    Validates unified diffs and test results, authoring a pull request with full evidence.
                  </p>
                </div>
                <div className="mt-4 pt-3 border-t border-black/5 text-[11px] font-mono text-zinc-700 font-semibold">
                  Pull Request Authoring
                </div>
              </div>
            </div>
          </section>

          {/* Interactive Hint */}
          <div className="text-center py-2">
            <p className="text-xs font-mono text-zinc-500 inline-flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-black" />
              Tap or click anywhere to send a Sonar wave ping across the canvas
            </p>
          </div>
        </main>
      )}

      {/* Glassmorphic Footer */}
      <footer className="glass-header w-full py-6 mt-auto">
        <div className="mx-auto flex max-w-7xl flex-col sm:flex-row items-center justify-between gap-4 px-4 sm:px-8 text-xs text-zinc-500">
          <div className="flex items-center gap-2.5">
            <img src="/logo.png" alt="Torque Logo" className="h-5 w-5 object-contain" />
            <span>Built for neatHack · October 2026</span>
          </div>
          <div className="flex items-center gap-4 font-mono font-medium text-zinc-700">
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
