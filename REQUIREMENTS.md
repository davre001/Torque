# Requirements.md — Suture

Everything required for Suture to be **live, runnable, demoable, and competitive** under neatHack judging.

---

## 1. Goal

Suture must take a real GitHub issue URL, investigate the codebase, implement a fix, recover from failure using its own traces, verify the result, and open a pull request—with full evidence for neatlogs, Entire, and cfo.ai.

---

## 2. neatHack Mandatory Requirements (non-negotiable)

| Requirement | Detail | Done when |
|---|---|---|
| Use **neatlogs** | Trace every agent run (model and tool calls, retries, failures, cost/latency) | Public/shareable trace links or screenshots in `/evidence` |
| Use **Entire** | Checkpoints and/or Entire graph / agentic search for repository context | Checkpoint IDs or graph/search output in the repository and evidence |
| Use **cfo.ai** | Business plan covering pricing, costs, revenue, and runway | `/business/cfo-plan.md` (or an export) is included in the submission |
| Code written during event | Commits dated **October 10–12, 2026** only | Public repository shows commit timestamps |
| Public repository | Open source; judges can clone and inspect | Repository URL included in the X submission |
| Demo video ≤ 3 min | Explains the agent and all three tools (architecture, runtime, results) | MP4, YouTube, or Loom link |
| Submission on X | Quote the official neatlogs post during the **October 12, 7:00–11:55 PM IST** window | Team name, project name, repository, and demo link are included |
| Evidence of recovery | A run where an action failed and the agent recovered | Before/after neatlogs traces plus a note |
| Building in public | Posts during the event tagged `#neatHack` | Links collected in `/evidence/public.md` |

Late or incomplete submissions are not judged.

---

## 3. Runtime Requirements

### 3.1 Accounts and API keys

| Service | Required? | Purpose | Notes |
|---|---|---|---|
| **neatlogs** | Yes | Tracing | Free tier is enough; requires `NEATLOGS_API_KEY` |
| **GitHub** | Yes | Issues, pull requests, and repository access | Personal access token with `repo` scope (`GITHUB_TOKEN`) |
| **LLM provider** | Yes | Agent reasoning | OpenAI, Anthropic, Bedrock, or another supported provider |
| **Entire** | Yes | Code context and checkpoints | CLI installed and logged in; search usable at runtime |
| **cfo.ai** | Yes, for the plan | Business model | Account to build/export the plan; not required in the live agent loop |
| AWS (Bedrock) | Optional | Models and infrastructure | Credits for the first 200 teams that check in |
| Crustdata | Optional | Company and people data | 5,000 credits for all participants |

### 3.2 Environment variables

```bash
NEATLOGS_API_KEY=...
GITHUB_TOKEN=...
OPENAI_API_KEY=...          # or ANTHROPIC_API_KEY / AWS credentials

# Optional
SUTURE_DEFAULT_REPO=...
SUTURE_MAX_ATTEMPTS=3
```

### 3.3 Local and runtime software

- Python **3.11+**
- Git
- Project test runner available in `PATH` or via script (e.g. `pytest`)
- Entire CLI installed and working
- Network access to GitHub, neatlogs, and the LLM provider
- Node.js only if you ship a heavier frontend; not required for CLI-only

### 3.4 Permissions and repository setup

- Token can read issues and write branches/pull requests on the target repository (or a fork you control)
- Ability to create an isolated worktree/branch so failed edits do not destroy the main branch
- At least one fixture issue prepared for the demo (known to fail once, then succeed after recovery)

### 3.5 Minimum runnable paths

Suture is considered **live** when the following CLI path works:

```bash
python -m suture run https://github.com/org/repo/issues/42
```

Optional UI path:

- Paste issue URL → start run → see status updates → receive final PR link

---

## 4. Functional Requirements

| # | Capability | Acceptance criteria |
|---|---|---|
| F1 | Accept GitHub issue URL | CLI and/or UI |
| F2 | Investigate | Uses Entire search/graph and produces a written plan |
| F3 | Implement | Edits code in an isolated worktree and commits changes |
| F4 | Test | Runs real tests; test result is a hard signal |
| F5 | Verify | Compares the diff and test results against issue acceptance criteria |
| F6 | Recover | On failure, reads the neatlogs failure signal, changes strategy, and retries a bounded number of times |
| F7 | Open PR | Only after verification passes; PR body includes issue link, plan summary, and trace IDs |
| F8 | Persist state | Run record saved as `runs/{id}.json` so progress is inspectable |
| F9 | Emit evidence | Trace IDs, checkpoint references, and attempt history written to `/evidence` |

Out of scope for v1 (must not block “live”): multi-repo support, end-user authentication, production hosting, and automatic webhooks for every new issue.

---

## 5. Evidence Requirements

Place the following under `/evidence` and reference it in the README:

- **Before trace:** failed attempt (neatlogs link or screenshots)
- **After trace:** successful recovered attempt
- **Comparison note:** what failed, what changed, and metrics if available
- **Entire evidence:** checkpoint IDs and/or graph/search snippets used
- **cfo.ai business plan:** pricing, costs, revenue, and runway
- **Recovery story:** one paragraph plus links
- **Public posts:** list of `#neatHack` posts
- **Commit-window confirmation:** confirmation that all product commits fall within October 10–12, 2026

---

## 6. Judging Requirements

Judges score each category out of 100, then apply the weights below.

### 6.1 The agent — **30%**

**Need:** A substantial task completed from start to finish.

Must show:

- Clear goal: issue → verified PR
- Planning, tool use, state, execution, verification, and iteration
- At least one **failure → recovery → success** path
- Real tests and a real PR (or equivalent verifiable artifact)

**Fail condition:** The agent only chats or plans but never lands a green, verified change.

### 6.2 Use of neatlogs, Entire, and cfo.ai — **25%**

**Need:** Tools are load-bearing, not decorative.

| Tool | Minimum bar | Strong bar |
|---|---|---|
| neatlogs | Traces for runs exist | Before/after comparison; recovery is driven by trace inspection |
| Entire | Checkpoints or search output are present | Runtime Investigator uses Entire; development commits have checkpoints |
| cfo.ai | Written business plan in the repository | Pricing, unit economics, and runway scenarios |

The demo must explicitly cover architecture, implementation, runtime, and results for each tool.

### 6.3 Demo video — **20%**

**Need:** At most 3 minutes, clear, and verifiable.

Recommended structure:

1. Problem and issue URL
2. Architecture (four agents)
3. Entire context in action
4. First failure and neatlogs failure span
5. Recovery and second run passing
6. Pull request opened
7. cfo.ai economics (briefly)

Avoid long setup, silent screen time, and missing tool call-outs.

### 6.4 Building in public — **15%**

**Need:** Genuine sharing during the event.

- Multiple posts tagged **`#neatHack`** while building (architecture, red test, recovery, PR)
- Links collected for judges
- Quality of narrative matters more than follower count

### 6.5 Usefulness and originality — **10%**

**Need:** A real problem and a distinctive angle.

- **Useful:** Maintainers are overwhelmed by issues; automated investigation → fix → PR solves a real problem.
- **Original angle for Suture:** Recovery driven by the agent’s own neatlogs traces, not simply “retry harder.”

---

## 7. Definition of “Live and Running”

Suture is live and running when all of the following are true:

1. `python -m suture run <issue_url>` completes without manual code edits mid-run.
2. neatlogs shows at least one full agent trace for that run.
3. Entire was used (search and/or checkpoints), with evidence saved.
4. On a prepared demo issue, the system demonstrates **fail → recover → PR**.
5. The cfo.ai plan exists in the repository.
6. The public repository, demo video, and X submission materials are ready for the October 12 submission window.

---

## 8. Launch Checklist (pre-submission)

### Runtime

- [ ] `.env` is filled in; CLI run succeeds on the fixture issue
- [ ] Isolated worktree/branch behavior works
- [ ] Maximum attempts are enforced (no infinite loops)
- [ ] PR only opens after verifier passes

### Integrations

- [ ] neatlogs before/after traces exported
- [ ] Entire evidence saved
- [ ] cfo.ai plan saved in `/business`

### Submission pack

- [ ] README is accurate
- [ ] Demo video is ≤ 3:00 and covers all three tools
- [ ] Public repository commits fall within the event window
- [ ] `#neatHack` links are listed
- [ ] X quote-tweet draft is ready for the submission window

### Judging alignment

- [ ] Substantial end-to-end agent path (30%)
- [ ] Deep tool use with evidence (25%)
- [ ] Clear demo (20%)
- [ ] Public building trail (15%)
- [ ] Clear usefulness and recovery originality (10%)

---

## 9. Out of Scope (explicit non-requirements)

- Production multi-tenant SaaS
- Guaranteed fix rate on arbitrary issues
- Support for every language/build system
- Paid neatlogs/Entire tiers
- Perfect UI polish

Ship one reliable, evidence-rich path that judges can verify.

---

## 10. One-line Success Criterion

**A judge can paste a GitHub issue link, watch Suture fail once, recover using its neatlogs trace, open a PR, and find matching evidence for neatlogs, Entire, and cfo.ai in the repository—all from work done during neatHack.**
