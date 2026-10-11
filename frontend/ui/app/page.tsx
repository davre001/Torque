"use client";

import * as React from "react";
import {
  ArrowRight,
  CheckCircle2,
  RotateCcw,
  GitPullRequest,
  Terminal,
  Search,
  Wrench,
  ShieldCheck,
  ExternalLink,
  Play,
  Layers,
  ChevronDown,
} from "lucide-react";
import { SonarGrid } from "@/components/ui/sonar-grid";
import { Button } from "@/components/ui/button";
import { MenuToggleIcon } from "@/components/ui/menu-toggle-icon";
import { useScroll } from "@/components/ui/use-scroll";
import { Reveal } from "@/components/ui/reveal";
import { cn } from "@/lib/utils";

// Official GitHub Octocat SVG mark
function GitHubIcon(props: React.ComponentProps<"svg">) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      width="1em"
      height="1em"
      aria-hidden="true"
      {...props}
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
      />
    </svg>
  );
}

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

// Three candidate example URLs cycling in the typing animation (identifiable as examples)
const EXAMPLE_ISSUE_URLS = [
  "https://github.com/acme/web-service/issues/104",
  "https://github.com/kokon/kokon/issues/42", // Selected kokon issue candidate
  "https://github.com/example/api-gateway/issues/89",
];

const FAQ_ITEMS = [
  {
    q: "What repository access does Torque require?",
    a: "Torque requires read access to inspect your source repository and create isolated worktrees for testing, plus permission to open pull requests. It operates strictly within the repositories you authorize.",
  },
  {
    q: "What happens if an initial fix attempt fails tests?",
    a: "Torque uses bounded recovery: when pytest or your test runner fails, the Recovery agent analyzes the neatlogs trace span, identifies why the attempt broke, pivots strategy, and retries. If recovery limits are reached, the run terminates safely with full diagnostic evidence.",
  },
  {
    q: "How does pull request publishing work?",
    a: "Torque never pushes unverified code directly to main branches. Only when the Verifier confirms 0 regressions and full test suite passes will a pull request be prepared with unified diff and trace links for operator review.",
  },
  {
    q: "How does disconnecting GitHub work?",
    a: "Disconnecting invalidates your active session and removes stored connection credentials. Any active run is requested to cancel cleanly. Previously submitted pull requests remain intact in your GitHub repository.",
  },
];

// Custom hook for typing/deleting animation with reduced motion support
function useCyclingTypewriter(examples: string[], prefersReducedMotion: boolean) {
  const [displayText, setDisplayText] = React.useState(examples[0]);
  const [index, setIndex] = React.useState(0);
  const [subIndex, setSubIndex] = React.useState(examples[0].length);
  const [isDeleting, setIsDeleting] = React.useState(false);
  const [pause, setPause] = React.useState(true);

  React.useEffect(() => {
    if (prefersReducedMotion) {
      setDisplayText(examples[0]);
      return;
    }

    let timer: NodeJS.Timeout;

    if (pause) {
      timer = setTimeout(() => {
        setPause(false);
        setIsDeleting(true);
      }, 2600);
      return () => clearTimeout(timer);
    }

    if (isDeleting) {
      if (subIndex > 0) {
        timer = setTimeout(() => {
          setSubIndex((prev) => prev - 1);
          setDisplayText(examples[index].substring(0, subIndex - 1));
        }, 25);
      } else {
        setIsDeleting(false);
        const nextIndex = (index + 1) % examples.length;
        setIndex(nextIndex);
      }
    } else {
      if (subIndex < examples[index].length) {
        timer = setTimeout(() => {
          setSubIndex((prev) => prev + 1);
          setDisplayText(examples[index].substring(0, subIndex + 1));
        }, 40);
      } else {
        setPause(true);
      }
    }

    return () => clearTimeout(timer);
  }, [examples, index, subIndex, isDeleting, pause, prefersReducedMotion]);

  return displayText;
}

export default function TorqueLandingPage() {
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);
  useScroll(12);

  const [issueUrl, setIssueUrl] = React.useState("");
  const [validationError, setValidationError] = React.useState<string | null>(null);
  const [status, setStatus] = React.useState<AgentStatus>("idle");
  const [currentAgent, setCurrentAgent] = React.useState<string | null>(null);
  const [attempts, setAttempts] = React.useState<AttemptRecord[]>([]);
  const [logMessages, setLogMessages] = React.useState<string[]>([]);
  const [prUrl, setPrUrl] = React.useState<string | null>(null);
  const [planSummary, setPlanSummary] = React.useState<string | null>(null);
  const [openFaqIndex, setOpenFaqIndex] = React.useState<number | null>(null);

  const timerRef = React.useRef<NodeJS.Timeout[]>([]);
  const inputSectionRef = React.useRef<HTMLDivElement | null>(null);
  const issueInputRef = React.useRef<HTMLInputElement | null>(null);
  const mobileToggleRef = React.useRef<HTMLButtonElement | null>(null);

  // Reduced motion detection
  const [reducedMotion, setReducedMotion] = React.useState(false);
  React.useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReducedMotion(mq.matches);
    const handler = (e: MediaQueryListEvent) => setReducedMotion(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  const animatedExampleText = useCyclingTypewriter(EXAMPLE_ISSUE_URLS, reducedMotion);

  // Check URL query parameters for ?demo=1 on initial load
  React.useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      if (params.get("demo") === "1") {
        setIssueUrl("https://github.com/kokon/kokon/issues/42");
      }
    }
  }, []);

  // Lock body scroll when mobile menu is open & handle Escape key
  React.useEffect(() => {
    if (mobileMenuOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && mobileMenuOpen) {
        setMobileMenuOpen(false);
        mobileToggleRef.current?.focus();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("keydown", onKeyDown);
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
    setValidationError(null);
  };

  // Validate exact GitHub issue URL: https://github.com/<owner>/<repo>/issues/<positive-int>
  const validateUrl = (url: string): boolean => {
    const trimmed = url.trim();
    if (!trimmed) {
      setValidationError("Please enter a GitHub issue URL.");
      return false;
    }
    const githubIssueRegex = /^https:\/\/github\.com\/([a-zA-Z0-9._-]+)\/([a-zA-Z0-9._-]+)\/issues\/([1-9][0-9]*)$/;
    if (!githubIssueRegex.test(trimmed)) {
      setValidationError(
        "Please provide a valid GitHub issue URL (e.g. https://github.com/owner/repo/issues/42) with a positive issue number."
      );
      return false;
    }
    setValidationError(null);
    return true;
  };

  // Scroll to input section and focus the input field
  const handleConnectGitHub = () => {
    inputSectionRef.current?.scrollIntoView({ behavior: reducedMotion ? "auto" : "smooth" });
    setTimeout(() => {
      issueInputRef.current?.focus();
    }, 350);
  };

  // UI Preview Simulation (clearly labeled as a UI preview per changes.md)
  const startPreviewRun = () => {
    if (!validateUrl(issueUrl)) return;

    resetRun();
    setStatus("queued");
    setLogMessages([
      "[UI Preview] Run queued (UI simulation mode — no agent runs or PRs created).",
    ]);

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
        "[Investigator] Parsing ticket context & reproduction steps...",
        "[Investigator] Entire index search completed: identified candidate call sites.",
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
          trace_id: "nl_tr_kokon_01",
          summary: "Initial patch in isolated worktree",
          detail: "Executing test suite...",
        },
      ]);
      setLogMessages((prev) => [
        ...prev,
        "[Implementer] Worktree torque/worktree-patch created.",
        "[Implementer] Initial patch applied. Executing tests...",
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
          trace_id: "nl_tr_kokon_01",
          summary: "Direct patch failed assertion in test runner",
          detail: "AssertionError: Expected valid response payload, received error state",
          duration: "2.1s",
        },
        {
          number: 2,
          status: "running",
          trace_id: "nl_tr_kokon_rec2",
          summary: "Strategy pivot: adjusted error handling & fallback layer",
          detail: "Recovery agent analyzing neatlogs trace span...",
        },
      ]);
      setLogMessages((prev) => [
        ...prev,
        "⚠️ [Test Suite] FAIL: 1 failed, 14 passed (AssertionError encountered)",
        "[neatlogs] Failure span recorded: trace_id=nl_tr_kokon_01",
        "[Recovery] Inspecting neatlogs trace nl_tr_kokon_01...",
        "[Recovery] Root cause isolated. Strategy shift: applying bounded recovery approach.",
      ]);
    });

    // 4. Implementer Retry with Checkpoint (Attempt 2)
    schedule(7600, () => {
      setStatus("implementing");
      setCurrentAgent("implementer");
      setLogMessages((prev) => [
        ...prev,
        "[Implementer] Applying recovered strategy via Entire checkpoint...",
        "[Implementer] Rerunning test suite...",
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
          trace_id: "nl_tr_kokon_01",
          summary: "Direct patch failed assertion in test runner",
          detail: "AssertionError: Expected valid response payload, received error state",
          duration: "2.1s",
        },
        {
          number: 2,
          status: "passed",
          trace_id: "nl_tr_kokon_rec2",
          summary: "Adjusted error handling passed",
          detail: "All tests passing cleanly with 0 regressions",
          duration: "1.7s",
        },
      ]);
      setLogMessages((prev) => [
        ...prev,
        "✅ [Verifier] All tests PASSED (0 regressions)",
        "[Verifier] Validating unified diff against acceptance criteria...",
        "[Verifier] Preparing verified pull request payload with trace references...",
      ]);
    });

    // 6. Completed
    schedule(11800, () => {
      setStatus("completed");
      setCurrentAgent(null);
      setPrUrl("https://github.com/kokon/kokon/pull/43");
      setPlanSummary(
        "Candidate fix verified with 0 regressions. Recovery strategy confirmed through neatlogs telemetry."
      );
      setLogMessages((prev) => [
        ...prev,
        "🎉 [Verifier] Pull Request draft verified: https://github.com/kokon/kokon/pull/43",
        "[Torque] Preview complete. Multi-agent self-healing verified.",
      ]);
    });
  };

  const handleSelectExample = (url: string) => {
    setIssueUrl(url);
    setValidationError(null);
    if (status !== "idle") resetRun();
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
      {/* Background radial gradient */}
      <div
        aria-hidden="true"
        className="pointer-events-none fixed inset-0 -z-10 bg-[radial-gradient(ellipse_60%_50%_at_50%_0%,rgba(255,255,255,0.98)_0%,rgba(255,255,255,0.7)_100%)]"
      />

      {/* Solid, clean navigation header */}
      <header className="sticky top-0 z-50 w-full bg-white border-b border-black/10 shadow-xs animate-appear-fade-in">
        <nav
          className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-4 sm:px-8"
          aria-label="Main navigation"
        >
          {/* Top Left: Torque logo + name */}
          <div className="flex items-center gap-3">
            <a href="/" className="flex items-center gap-2.5 focus:outline-hidden focus:ring-2 focus:ring-black rounded-lg">
              <img
                src="/logo.png"
                alt="Torque Logo"
                className="h-8 w-8 object-contain transition-transform duration-200 hover:rotate-6 cursor-pointer"
              />
              <span className="text-xl font-bold tracking-tight text-black">Torque</span>
            </a>
            <span className="hidden sm:inline-flex rounded-full border border-black/10 bg-zinc-100 px-2.5 py-0.5 text-[10px] font-mono font-semibold uppercase tracking-wider text-zinc-700">
              neatHack
            </span>
          </div>

          {/* Center Links (Working anchor navigation) */}
          <div className="hidden md:flex items-center gap-6 text-sm font-medium text-zinc-600">
            <a href="#how-it-works" className="hover:text-black transition-colors">
              How it works
            </a>
            <a href="#getting-started" className="hover:text-black transition-colors">
              Getting started
            </a>
            <a href="#why-torque" className="hover:text-black transition-colors">
              Why Torque
            </a>
            <a href="#evidence" className="hover:text-black transition-colors">
              Evidence
            </a>
            <a href="#faq" className="hover:text-black transition-colors">
              FAQ
            </a>
          </div>

          {/* Top Right: Connect GitHub / Get started CTA */}
          <div className="hidden sm:flex items-center gap-3">
            <Button
              size="sm"
              onClick={handleConnectGitHub}
              className="rounded-xl bg-black px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-zinc-800 transition-all flex items-center gap-2 cursor-pointer active:scale-95"
            >
              <GitHubIcon className="h-4 w-4" />
              <span>Get started</span>
            </Button>
          </div>

          {/* Mobile Menu Toggle Button */}
          <button
            ref={mobileToggleRef}
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden flex h-10 w-10 items-center justify-center rounded-lg border border-black/10 bg-white text-zinc-800 hover:bg-zinc-100 focus:outline-hidden focus:ring-2 focus:ring-black"
            aria-label="Toggle navigation menu"
            aria-expanded={mobileMenuOpen}
            aria-controls="mobile-nav-drawer"
          >
            <MenuToggleIcon open={mobileMenuOpen} className="size-5" duration={300} />
          </button>
        </nav>

        {/* Mobile Accessible Navigation Drawer */}
        <div
          id="mobile-nav-drawer"
          className={cn(
            "fixed inset-x-0 top-16 bottom-0 z-50 flex flex-col bg-white border-t border-black/10 p-6 md:hidden transition-all duration-300",
            mobileMenuOpen ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
          )}
          aria-hidden={!mobileMenuOpen}
        >
          <div className="flex flex-col gap-4 text-base font-medium text-zinc-800">
            <a
              href="#how-it-works"
              onClick={() => setMobileMenuOpen(false)}
              className="py-2 border-b border-black/5 hover:text-black"
            >
              How it works
            </a>
            <a
              href="#getting-started"
              onClick={() => setMobileMenuOpen(false)}
              className="py-2 border-b border-black/5 hover:text-black"
            >
              Getting started
            </a>
            <a
              href="#why-torque"
              onClick={() => setMobileMenuOpen(false)}
              className="py-2 border-b border-black/5 hover:text-black"
            >
              Why Torque
            </a>
            <a
              href="#evidence"
              onClick={() => setMobileMenuOpen(false)}
              className="py-2 border-b border-black/5 hover:text-black"
            >
              Evidence & Integrations
            </a>
            <a
              href="#faq"
              onClick={() => setMobileMenuOpen(false)}
              className="py-2 border-b border-black/5 hover:text-black"
            >
              FAQ
            </a>
          </div>

          <div className="mt-8 flex flex-col gap-3">
            <Button
              className="w-full h-12 rounded-xl bg-black text-sm font-semibold text-white flex items-center justify-center gap-2"
              onClick={() => {
                setMobileMenuOpen(false);
                handleConnectGitHub();
              }}
            >
              <GitHubIcon className="h-4 w-4" />
              <span>Get started with GitHub</span>
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 w-full flex flex-col">
        {/* 1. HERO SECTION WITH APPEARING ANIMATIONS */}
        <section className="w-full max-w-5xl mx-auto px-4 sm:px-8 pt-14 pb-12 sm:pt-20 sm:pb-16 flex flex-col items-center text-center">
          {/* Badge Pill with scale-up entrance */}
          <Reveal delay={50} variant="scale-up">
            <div className="inline-flex items-center gap-2 rounded-full border border-black/10 bg-zinc-50 px-4 py-1.5 text-xs font-mono font-medium text-zinc-800 mb-6 shadow-2xs">
              <span className="h-2 w-2 rounded-full bg-black animate-pulse" />
              <span>AUTONOMOUS ISSUE-TO-PR WORKFLOW</span>
            </div>
          </Reveal>

          {/* Hero Heading with smooth fade-up */}
          <Reveal delay={120} variant="fade-up">
            <h1 className="text-4xl sm:text-6xl md:text-7xl font-bold tracking-tight text-black text-balance leading-[1.08]">
              Turn a GitHub issue into a verified pull request
            </h1>
          </Reveal>

          {/* Explanatory Body with fade-up */}
          <Reveal delay={200} variant="fade-up">
            <p className="mt-6 text-lg sm:text-xl md:text-[22px] text-zinc-600 max-w-3xl text-pretty leading-relaxed">
              Torque orchestrates an investigation via Entire, creates isolated test worktrees, runs your
              test suite, and authors a pull request. If tests fail, a Recovery agent analyzes neatlogs
              telemetry and retries with a new strategy.
            </p>
          </Reveal>

          {/* Decorative Typewriter URL Display with scale-up appearance */}
          <Reveal delay={280} variant="scale-up" className="w-full max-w-xl mx-auto mt-8">
            <div className="flex flex-col items-center gap-1.5 w-full">
              <div
                className="w-full rounded-xl border border-black/10 bg-zinc-50/80 px-4 py-3 font-mono text-xs sm:text-sm text-zinc-700 flex items-center gap-2 shadow-2xs select-none"
                aria-hidden="true"
              >
                <Search className="h-4 w-4 text-zinc-400 shrink-0" />
                <span className="text-zinc-400 shrink-0">issue:</span>
                <span className="truncate text-black font-semibold">
                  {animatedExampleText}
                </span>
                <span className="inline-block w-1.5 h-4 bg-black animate-pulse shrink-0" />
              </div>
              <span className="text-[11px] font-mono text-zinc-500">
                Candidate issue examples • Not active submissions
              </span>
            </div>
          </Reveal>

          {/* Hero CTAs */}
          <Reveal delay={360} variant="fade-up" className="mt-8">
            <div className="flex flex-col sm:flex-row items-center gap-3 w-full sm:w-auto">
              <Button
                size="lg"
                onClick={handleConnectGitHub}
                className="w-full sm:w-auto h-13 px-7 rounded-xl bg-black text-white hover:bg-zinc-800 font-semibold text-base shadow-sm flex items-center justify-center gap-2.5 cursor-pointer active:scale-95 transition-all"
              >
                <GitHubIcon className="h-5 w-5" />
                <span>Connect GitHub</span>
              </Button>
              <a
                href="#how-it-works"
                className="w-full sm:w-auto h-13 px-6 rounded-xl border border-black/15 bg-white text-zinc-900 hover:bg-zinc-50 hover:border-black/30 font-semibold text-base transition-all flex items-center justify-center gap-2 active:scale-95"
              >
                <span>How it works</span>
                <ArrowRight className="h-4 w-4 text-zinc-500" />
              </a>
            </div>
          </Reveal>
        </section>

        {/* INTERACTIVE WORKSPACE PREVIEW / ISSUE INPUT */}
        <section
          ref={inputSectionRef}
          id="workspace-preview"
          className="w-full max-w-4xl mx-auto px-4 sm:px-8 py-8"
        >
          <Reveal delay={100} variant="scale-up">
            <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-black/10 shadow-lg">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-5 border-b border-black/10 gap-2">
                <div>
                  <h2 className="text-xl sm:text-2xl font-bold text-black tracking-tight">
                    Run Torque Workspace
                  </h2>
                  <p className="text-xs sm:text-sm text-zinc-500 mt-0.5">
                    Supply a GitHub issue to simulate the multi-agent investigation, execution, and recovery loop.
                  </p>
                </div>
                <div className="self-start sm:self-auto inline-flex items-center gap-1.5 rounded-full bg-zinc-100 px-3 py-1 text-xs font-mono text-zinc-700">
                  <span className="h-2 w-2 rounded-full bg-emerald-600" />
                  <span>UI Preview Mode</span>
                </div>
              </div>

              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  startPreviewRun();
                }}
                className="mt-6 flex flex-col gap-4"
                noValidate
              >
                <div>
                  <label
                    htmlFor="issue-url-input"
                    className="block text-xs font-mono uppercase tracking-wider font-bold text-zinc-700 mb-2"
                  >
                    GitHub Issue URL <span className="text-rose-500">*</span>
                  </label>
                  <div className="relative flex items-center">
                    <Search className="absolute left-4 h-4 w-4 text-zinc-400 pointer-events-none" />
                    <input
                      ref={issueInputRef}
                      type="url"
                      id="issue-url-input"
                      value={issueUrl}
                      onChange={(e) => {
                        setIssueUrl(e.target.value);
                        if (validationError) setValidationError(null);
                      }}
                      placeholder="https://github.com/kokon/kokon/issues/42"
                      aria-invalid={validationError ? "true" : "false"}
                      aria-describedby={validationError ? "issue-url-error" : undefined}
                      required
                      className={cn(
                        "w-full rounded-xl bg-white py-3.5 pl-11 pr-4 text-sm font-mono text-black placeholder:text-zinc-400 border transition-colors outline-hidden focus:ring-2",
                        validationError
                          ? "border-rose-400 focus:ring-rose-200"
                          : "border-black/15 focus:ring-black/20 focus:border-black"
                      )}
                    />
                  </div>
                  {validationError && (
                    <p id="issue-url-error" role="alert" className="mt-2 text-xs font-medium text-rose-600">
                      {validationError}
                    </p>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="flex flex-wrap items-center gap-3 pt-1">
                  <Button
                    type="submit"
                    id="run-torque-btn"
                    disabled={status !== "idle" && status !== "completed"}
                    className="h-12 px-6 rounded-xl bg-black text-white hover:bg-zinc-800 font-semibold text-sm disabled:opacity-50 flex items-center gap-2 cursor-pointer active:scale-95 transition-all"
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
                        <span className="h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin mr-1" />
                        <span>Running Simulation...</span>
                      </>
                    )}
                  </Button>

                  {status !== "idle" && (
                    <Button
                      type="button"
                      variant="outline"
                      onClick={resetRun}
                      className="h-12 px-4 rounded-xl border-black/15 text-zinc-700 hover:text-black flex items-center gap-1.5 active:scale-95 transition-all"
                      aria-label="Reset run state"
                    >
                      <RotateCcw className="h-4 w-4" />
                      <span>Reset</span>
                    </Button>
                  )}
                </div>

                {/* Quick candidate presets */}
                <div className="pt-3 border-t border-black/5 flex flex-wrap items-center gap-2 text-xs">
                  <span className="font-mono text-zinc-500">Candidate preset:</span>
                  <button
                    type="button"
                    onClick={() => handleSelectExample("https://github.com/kokon/kokon/issues/42")}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-black/10 bg-zinc-50 px-2.5 py-1 text-zinc-800 hover:bg-zinc-100 hover:border-black/20 transition-all font-mono active:scale-95"
                  >
                    <span className="h-1.5 w-1.5 rounded-full bg-black" />
                    <span>kokon/kokon#42 (Candidate Reproduction)</span>
                  </button>
                </div>
              </form>

              {/* LIVE SIMULATION STATUS PANEL */}
              {status !== "idle" && (
                <div
                  className="mt-8 pt-6 border-t border-black/10 flex flex-col gap-6 animate-appear-fade-up"
                  aria-live="polite"
                >
                  {/* Status Bar */}
                  <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-black/5">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono uppercase tracking-wider text-zinc-500 font-bold">
                        Current Stage:
                      </span>
                      <span className="text-sm font-mono font-bold text-black capitalize">
                        {status === "recovering"
                          ? "Recovery (Conditional Attempt 2)"
                          : status}
                      </span>
                    </div>
                    <span className="text-xs font-mono text-zinc-500">
                      UI Preview Simulation
                    </span>
                  </div>

                  {/* 4 Agent Status Cards */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-sm">
                    {/* Investigator */}
                    <div className="rounded-xl border border-black/10 bg-white/80 p-3.5 flex flex-col justify-between transition-all">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold text-black">1. Investigator</span>
                        <Search className="h-4 w-4 text-zinc-400" />
                      </div>
                      <span className="font-mono text-xs text-zinc-600">
                        {status !== "queued" && status !== "investigating" ? (
                          <span className="text-emerald-700 flex items-center gap-1 font-semibold">
                            <CheckCircle2 className="h-3.5 w-3.5" /> Done
                          </span>
                        ) : currentAgent === "investigator" ? (
                          <span className="text-black font-semibold animate-pulse">Entire Search...</span>
                        ) : (
                          "Pending"
                        )}
                      </span>
                    </div>

                    {/* Implementer */}
                    <div className="rounded-xl border border-black/10 bg-white/80 p-3.5 flex flex-col justify-between transition-all">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold text-black">2. Implementer</span>
                        <Wrench className="h-4 w-4 text-zinc-400" />
                      </div>
                      <span className="font-mono text-xs text-zinc-600">
                        {attempts.some((a) => a.number === 2 && a.status === "passed") ? (
                          <span className="text-emerald-700 flex items-center gap-1 font-semibold">
                            <CheckCircle2 className="h-3.5 w-3.5" /> Passed tests
                          </span>
                        ) : currentAgent === "implementer" ? (
                          <span className="text-black font-semibold animate-pulse">Running pytest...</span>
                        ) : attempts.some((a) => a.status === "failed") ? (
                          <span className="text-amber-700 font-semibold">Attempt 1 failed</span>
                        ) : (
                          "Pending"
                        )}
                      </span>
                    </div>

                    {/* Recovery */}
                    <div
                      className={cn(
                        "rounded-xl border p-3.5 flex flex-col justify-between transition-all",
                        status === "recovering"
                          ? "border-black/40 bg-zinc-100"
                          : "border-black/10 bg-white/80"
                      )}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold text-black">3. Recovery</span>
                        <RotateCcw className="h-4 w-4 text-zinc-400" />
                      </div>
                      <span className="font-mono text-xs text-zinc-600">
                        {status === "recovering" ? (
                          <span className="text-black font-bold animate-pulse">
                            → Pivot Strategy
                          </span>
                        ) : attempts.some((a) => a.number === 2) ? (
                          <span className="text-emerald-700 flex items-center gap-1 font-semibold">
                            <CheckCircle2 className="h-3.5 w-3.5" /> Strategy shifted
                          </span>
                        ) : (
                          "Conditional standby"
                        )}
                      </span>
                    </div>

                    {/* Verifier */}
                    <div className="rounded-xl border border-black/10 bg-white/80 p-3.5 flex flex-col justify-between transition-all">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold text-black">4. Verifier</span>
                        <ShieldCheck className="h-4 w-4 text-zinc-400" />
                      </div>
                      <span className="font-mono text-xs text-zinc-600">
                        {status === "completed" ? (
                          <span className="text-emerald-700 flex items-center gap-1 font-semibold">
                            <CheckCircle2 className="h-3.5 w-3.5" /> PR Created
                          </span>
                        ) : currentAgent === "verifier" ? (
                          <span className="text-black font-semibold animate-pulse">Diff verification...</span>
                        ) : (
                          "Pending"
                        )}
                      </span>
                    </div>
                  </div>

                  {/* Console Log Output */}
                  <div
                    className="rounded-xl bg-zinc-950 p-4 font-mono text-xs text-zinc-200 max-h-40 overflow-y-auto space-y-1 shadow-inner"
                    role="log"
                    aria-label="Simulation log output"
                  >
                    {logMessages.map((msg, idx) => (
                      <div
                        key={idx}
                        className={
                          msg.includes("FAIL")
                            ? "text-rose-400"
                            : msg.includes("PASSED") || msg.includes("Pull Request")
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

                  {/* Attempt History */}
                  {attempts.length > 0 && (
                    <div className="flex flex-col gap-3">
                      <div className="flex items-center justify-between">
                        <h3 className="text-xs font-mono uppercase tracking-wider text-black font-bold flex items-center gap-1.5">
                          <Layers className="h-3.5 w-3.5" />
                          Attempts History
                        </h3>
                        <span className="text-[11px] font-mono text-zinc-500">
                          neatlogs trace inspection
                        </span>
                      </div>

                      <div className="space-y-2">
                        {attempts.map((att) => (
                          <div
                            key={att.number}
                            className={cn(
                              "rounded-xl border p-3 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2",
                              att.status === "failed"
                                ? "border-rose-300/80 bg-rose-50/50"
                                : att.status === "passed"
                                ? "border-emerald-300/80 bg-emerald-50/50"
                                : "border-black/10 bg-zinc-50"
                            )}
                          >
                            <div className="flex items-start gap-2.5">
                              <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-black text-white text-[10px] font-bold">
                                #{att.number}
                              </span>
                              <div>
                                <div className="font-semibold text-black">{att.summary}</div>
                                <div className="text-zinc-600 text-[11px]">{att.detail}</div>
                              </div>
                            </div>
                            <div className="flex items-center gap-2 font-mono text-[11px] text-zinc-500 self-end sm:self-auto">
                              <span className="rounded bg-black/5 px-2 py-0.5 text-zinc-800">
                                trace: {att.trace_id}
                              </span>
                              {att.duration && <span>{att.duration}</span>}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Pull Request Output Result */}
                  {prUrl && (
                    <div className="rounded-2xl border border-black/20 bg-white p-5 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4 animate-appear-scale-up">
                      <div>
                        <div className="flex items-center gap-1.5 text-xs font-mono font-bold uppercase text-emerald-700">
                          <CheckCircle2 className="h-4 w-4" />
                          Verified Pull Request Candidate
                        </div>
                        <h4 className="text-lg font-bold text-black mt-1 flex items-center gap-2">
                          <GitPullRequest className="h-5 w-5" />
                          {prUrl.replace("https://github.com/", "")}
                        </h4>
                        {planSummary && (
                          <p className="text-xs text-zinc-600 mt-1 max-w-xl">{planSummary}</p>
                        )}
                      </div>

                      <a
                        href={prUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="rounded-xl bg-black px-4 py-2.5 text-xs font-bold text-white hover:bg-zinc-800 transition-colors flex items-center gap-1.5 shrink-0 self-start sm:self-auto active:scale-95"
                      >
                        <span>Inspect PR</span>
                        <ExternalLink className="h-3.5 w-3.5" />
                      </a>
                    </div>
                  )}
                </div>
              )}
            </div>
          </Reveal>
        </section>

        {/* 2. HOW IT WORKS SECTION */}
        <section
          id="how-it-works"
          className="w-full max-w-5xl mx-auto px-4 sm:px-8 py-16 sm:py-24 border-t border-black/10"
        >
          <Reveal delay={50} variant="fade-up">
            <div className="text-center mb-12 sm:mb-16">
              <h2 className="text-3xl sm:text-5xl font-bold text-black tracking-tight">
                How it works
              </h2>
              <p className="mt-4 text-base sm:text-xl text-zinc-600 max-w-2xl mx-auto">
                A transparent, stage-gated pipeline from issue diagnosis to peer-reviewed PR.
              </p>
            </div>
          </Reveal>

          {/* 5 Readable Large Steps with Staggered Entrance Animations */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {[
              {
                step: "01",
                title: "Connect GitHub",
                desc: "Authorize Torque on your repository with fine-grained read and pull request access.",
                footer: "GitHub App OAuth",
                highlight: false,
              },
              {
                step: "02",
                title: "Select Issue",
                desc: "Point Torque to a specific GitHub issue or bug ticket from your authorized repository.",
                footer: "Issue validation",
                highlight: false,
              },
              {
                step: "03",
                title: "Investigate & Implement",
                desc: "Investigator queries Entire for call sites; Implementer applies code edits and runs tests in an isolated worktree.",
                footer: "Worktree + Pytest",
                highlight: false,
              },
              {
                step: "04",
                title: "Recover If Needed",
                desc: "If initial tests fail, Recovery reads neatlogs trace spans, isolates the flaw, and directs a new strategy.",
                footer: "neatlogs Telemetry",
                highlight: true,
                badge: "Conditional",
              },
              {
                step: "05",
                title: "Review Verified PR",
                desc: "Verifier audits acceptance criteria and opens a pull request with complete execution evidence attached.",
                footer: "Verified patch",
                highlight: false,
              },
            ].map((item, idx) => (
              <Reveal key={item.step} delay={idx * 90} variant="fade-up">
                <div
                  className={cn(
                    "glass-panel p-5 rounded-2xl flex flex-col justify-between h-full transition-all duration-200 hover:-translate-y-1 hover:shadow-md",
                    item.highlight ? "border-black/30 bg-zinc-50/70" : ""
                  )}
                >
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs font-bold text-zinc-400">{item.step}</span>
                      {item.badge && (
                        <span className="text-[10px] font-mono uppercase bg-black text-white px-1.5 py-0.5 rounded">
                          {item.badge}
                        </span>
                      )}
                    </div>
                    <h3 className="font-bold text-base text-black mt-2">{item.title}</h3>
                    <p className="text-xs sm:text-sm text-zinc-600 mt-2 leading-relaxed">
                      {item.desc}
                    </p>
                  </div>
                  <div
                    className={cn(
                      "mt-4 pt-3 border-t text-[11px] font-mono",
                      item.highlight ? "border-black/10 text-black font-semibold" : "border-black/5 text-zinc-500"
                    )}
                  >
                    {item.footer}
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </section>

        {/* 3. GETTING STARTED SECTION */}
        <section
          id="getting-started"
          className="w-full max-w-5xl mx-auto px-4 sm:px-8 py-16 sm:py-24 border-t border-black/10"
        >
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 items-center">
            <Reveal delay={50} variant="fade-up">
              <div>
                <h2 className="text-3xl sm:text-5xl font-bold text-black tracking-tight">
                  Getting started
                </h2>
                <p className="mt-4 text-base sm:text-lg text-zinc-600 leading-relaxed">
                  Connect your account, choose a repository, and let Torque handle the rest.
                  Access permissions are kept minimal and strictly scoped.
                </p>

                <div className="mt-8 space-y-4">
                  {[
                    {
                      num: "1",
                      title: "Connect an account",
                      desc: "Log in through GitHub OAuth to identify your developer session.",
                    },
                    {
                      num: "2",
                      title: "Authorize a repository",
                      desc: "Install the Torque app exclusively on the repositories where you want fixes created.",
                    },
                    {
                      num: "3",
                      title: "Supply or select an issue",
                      desc: "Paste the URL of an issue or bug report requiring remediation.",
                    },
                    {
                      num: "4",
                      title: "Run Torque in the workspace",
                      desc: "Monitor live agent attempts, trace logs, and inspect the resulting pull request.",
                    },
                  ].map((step, sIdx) => (
                    <Reveal key={step.num} delay={sIdx * 80} variant="fade-up">
                      <div className="flex items-start gap-3.5">
                        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-black text-white font-mono text-xs font-bold">
                          {step.num}
                        </div>
                        <div>
                          <h4 className="font-bold text-black text-sm">{step.title}</h4>
                          <p className="text-xs sm:text-sm text-zinc-600 mt-0.5">
                            {step.desc}
                          </p>
                        </div>
                      </div>
                    </Reveal>
                  ))}
                </div>

                <div className="mt-8">
                  <Button
                    onClick={handleConnectGitHub}
                    className="rounded-xl bg-black text-white px-5 py-2.5 text-sm font-semibold flex items-center gap-2 cursor-pointer active:scale-95 transition-all"
                  >
                    <GitHubIcon className="h-4 w-4" />
                    <span>Connect GitHub</span>
                  </Button>
                </div>
              </div>
            </Reveal>

            {/* Plain language access statement box with entrance animation */}
            <Reveal delay={150} variant="scale-up">
              <div className="rounded-2xl border border-black/10 bg-zinc-50 p-6 sm:p-8 space-y-4 shadow-sm hover:shadow-md transition-shadow">
                <h3 className="font-bold text-black text-base flex items-center gap-2">
                  <ShieldCheck className="h-5 w-5 text-zinc-700" />
                  Plain-Language Access Requirements
                </h3>
                <p className="text-xs sm:text-sm text-zinc-600 leading-relaxed">
                  Torque requires repository read access to analyze your code and write access to push
                  patch branches and open PRs. Torque does not:
                </p>
                <ul className="text-xs sm:text-sm text-zinc-700 space-y-2 list-disc list-inside">
                  <li>Merge code directly to main or protected branches</li>
                  <li>Access repositories outside your authorized list</li>
                  <li>Store private source code beyond active execution jobs</li>
                </ul>
              </div>
            </Reveal>
          </div>
        </section>

        {/* 4. WHY TORQUE SECTION */}
        <section
          id="why-torque"
          className="w-full max-w-5xl mx-auto px-4 sm:px-8 py-16 sm:py-24 border-t border-black/10"
        >
          <Reveal delay={50} variant="fade-up">
            <div className="text-center mb-12 sm:mb-16">
              <h2 className="text-3xl sm:text-5xl font-bold text-black tracking-tight">
                Why Torque
              </h2>
              <p className="mt-4 text-base sm:text-xl text-zinc-600 max-w-2xl mx-auto">
                Built on three foundational principles for trustworthy code generation.
              </p>
            </div>
          </Reveal>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                icon: <ShieldCheck className="h-5 w-5" />,
                title: "Test-gated changes",
                desc: "No patch is proposed without verification. Torque runs your project's existing tests and newly synthesized regression tests in clean worktrees before opening a PR.",
              },
              {
                icon: <RotateCcw className="h-5 w-5" />,
                title: "Bounded recovery",
                desc: "When fixes fail, Torque doesn't hallucinate repeatedly. The Recovery agent inspects telemetry traces to alter strategy with explicit retry caps to avoid infinite loops.",
              },
              {
                icon: <Terminal className="h-5 w-5" />,
                title: "Inspectable evidence",
                desc: "Every decision, diff, pytest run, and recovery rationale is recorded in neatlogs trace spans and Entire checkpoints for full human audibility.",
              },
            ].map((card, idx) => (
              <Reveal key={card.title} delay={idx * 120} variant="fade-up">
                <div className="glass-panel p-6 rounded-2xl flex flex-col justify-between h-full hover:-translate-y-1 hover:shadow-md transition-all duration-200">
                  <div>
                    <div className="h-10 w-10 rounded-xl bg-black text-white flex items-center justify-center mb-4 shadow-2xs">
                      {card.icon}
                    </div>
                    <h3 className="font-bold text-lg text-black">{card.title}</h3>
                    <p className="text-sm text-zinc-600 mt-2 leading-relaxed">
                      {card.desc}
                    </p>
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </section>

        {/* 5. EVIDENCE & INTEGRATIONS SECTION */}
        <section
          id="evidence"
          className="w-full max-w-5xl mx-auto px-4 sm:px-8 py-16 sm:py-24 border-t border-black/10"
        >
          <Reveal delay={50} variant="fade-up">
            <div className="text-center mb-12 sm:mb-16">
              <h2 className="text-3xl sm:text-5xl font-bold text-black tracking-tight">
                Evidence & Integrations
              </h2>
              <p className="mt-4 text-base sm:text-xl text-zinc-600 max-w-2xl mx-auto">
                Torque integrates with production-grade tooling created during neatHack.
              </p>
            </div>
          </Reveal>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                name: "neatlogs",
                role: "Execution Telemetry & Traces",
                desc: "Provides high-fidelity trace logging of agent tool calls, execution times, and pytest assertion failures that feed directly into the Recovery agent's diagnostics.",
                footer: "Trace correlation engine",
              },
              {
                name: "Entire",
                role: "Codebase Context & Checkpoints",
                desc: "Powers the Investigator's code retrieval, call graph navigation, and checkpoint state snapshots to ensure patches target the correct architectural layers.",
                footer: "Context & checkpointing",
              },
              {
                name: "cfo.ai",
                role: "Business & Unit Economics Plan",
                desc: "The business strategy, unit costs, and ROI models for autonomous bug resolution and developer acceleration created for the neatHack submission.",
                footer: "Economic viability model",
              },
            ].map((tool, idx) => (
              <Reveal key={tool.name} delay={idx * 120} variant="fade-up">
                <div className="rounded-2xl border border-black/10 bg-zinc-50 p-6 flex flex-col justify-between h-full hover:shadow-md transition-all duration-200">
                  <div>
                    <h3 className="text-lg font-bold text-black">{tool.name}</h3>
                    <p className="text-xs font-mono text-zinc-500 mt-0.5">{tool.role}</p>
                    <p className="text-sm text-zinc-600 mt-3 leading-relaxed">
                      {tool.desc}
                    </p>
                  </div>
                  <div className="mt-5 pt-3 border-t border-black/5 text-xs font-mono text-zinc-500">
                    {tool.footer}
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </section>

        {/* 6. FAQ SECTION */}
        <section
          id="faq"
          className="w-full max-w-4xl mx-auto px-4 sm:px-8 py-16 sm:py-24 border-t border-black/10"
        >
          <Reveal delay={50} variant="fade-up">
            <div className="text-center mb-12 sm:mb-16">
              <h2 className="text-3xl sm:text-5xl font-bold text-black tracking-tight">
                Frequently Asked Questions
              </h2>
            </div>
          </Reveal>

          <div className="space-y-3">
            {FAQ_ITEMS.map((item, index) => {
              const isOpen = openFaqIndex === index;
              return (
                <Reveal key={index} delay={index * 60} variant="fade-up">
                  <div className="rounded-2xl border border-black/10 bg-white overflow-hidden transition-colors">
                    <button
                      type="button"
                      onClick={() => setOpenFaqIndex(isOpen ? null : index)}
                      className="w-full flex items-center justify-between p-5 text-left font-semibold text-black hover:bg-zinc-50/50 transition-colors"
                      aria-expanded={isOpen}
                      aria-controls={`faq-answer-${index}`}
                    >
                      <span className="text-base sm:text-lg">{item.q}</span>
                      <ChevronDown
                        className={cn(
                          "h-5 w-5 text-zinc-400 transition-transform duration-200 shrink-0 ml-4",
                          isOpen && "rotate-180 text-black"
                        )}
                      />
                    </button>
                    {isOpen && (
                      <div
                        id={`faq-answer-${index}`}
                        className="px-5 pb-5 text-sm sm:text-base text-zinc-600 leading-relaxed border-t border-black/5 pt-3 animate-appear-fade-in"
                      >
                        {item.a}
                      </div>
                    )}
                  </div>
                </Reveal>
              );
            })}
          </div>
        </section>

        {/* Subtle Canvas Ping Hint */}
        <Reveal delay={100} variant="fade-in">
          <div className="text-center py-6 text-xs font-mono text-zinc-400 select-none">
            Click anywhere to trigger a Sonar wave ping across the canvas
          </div>
        </Reveal>
      </main>

      {/* 7. FOOTER SECTION */}
      <footer className="w-full bg-white border-t border-black/10 py-8">
        <Reveal delay={50} variant="fade-in">
          <div className="mx-auto flex max-w-6xl flex-col sm:flex-row items-center justify-between gap-4 px-4 sm:px-8 text-xs text-zinc-600">
            <div className="flex items-center gap-2.5">
              <img src="/logo.png" alt="Torque Logo" className="h-5 w-5 object-contain" />
              <span className="font-bold text-black text-sm">Torque</span>
              <span className="text-zinc-400">|</span>
              <span>Built for neatHack • October 2026</span>
            </div>

            <div className="flex items-center gap-6 font-medium">
              <a href="#how-it-works" className="hover:text-black transition-colors">
                How it works
              </a>
              <a href="#getting-started" className="hover:text-black transition-colors">
                Getting started
              </a>
              <a href="#why-torque" className="hover:text-black transition-colors">
                Why Torque
              </a>
              <a href="#evidence" className="hover:text-black transition-colors">
                Evidence
              </a>
              <a href="#faq" className="hover:text-black transition-colors">
                FAQ
              </a>
              <a
                href="https://github.com/davre001/Torque"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 hover:text-black transition-colors"
              >
                <GitHubIcon className="h-3.5 w-3.5" />
                <span>Repository</span>
              </a>
            </div>

            <div className="flex items-center gap-2 font-mono text-zinc-500 text-[11px]">
              <span>neatlogs</span>
              <span>•</span>
              <span>Entire</span>
              <span>•</span>
              <span>cfo.ai</span>
            </div>
          </div>
        </Reveal>
      </footer>
    </SonarGrid>
  );
}
