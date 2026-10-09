# Torque
**An agent that turns a GitHub issue into a verified pull request — and recovers when it fails.**

Suture is a multi-agent system built for [neatHack](https://neatlogs.com/hackathon).  
Give it a GitHub issue URL. It investigates the codebase (via Entire), implements a fix, runs tests, and opens a PR. If an attempt fails, a Recovery agent reads the neatlogs trace of that failure, changes strategy, and tries again.

> Agents you’d trust to run without watching.

## How it works

Issue URL
↓
Investigator  (+ Entire search/graph)  → diagnosis + plan
↓
Implementer   → edit code, run tests, commit
↓
├─ Pass → Verifier → open Pull Request  ✅
└─ Fail → Recovery reads neatlogs trace → new strategy → retry


**Agents**
- **Investigator** – reads the issue + uses Entire for precise code context
- **Implementer** – makes changes in an isolated worktree and runs tests
- **Verifier** – checks the diff and test output against the issue
- **Recovery** – inspects the failed neatlogs trace and decides what to do next

## Quick start

### Prerequisites
- Python 3.11+
- GitHub token with `repo` scope (`GITHUB_TOKEN`)
- neatlogs API key (`NEATLOGS_API_KEY`)
- LLM key (OpenAI / Anthropic / Bedrock)
- Entire CLI (for checkpoints + search)

### Install
```bash
git clone https://github.com/<you>/suture
cd suture
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# fill in:
# NEATLOGS_API_KEY=
# GITHUB_TOKEN=
# OPENAI_API_KEY=   # or ANTHROPIC_API_KEY / AWS creds

Run from CLI
Bashpython -m suture run https://github.com/org/repo/issues/42
Run from the web UI
Bashuvicorn frontend.app:app --reload --port 8000
# open http://localhost:8000
Paste an issue URL and click Run Suture. Live status, attempt history, and final PR link appear on the page.
Required neatHack integrations

ToolHow Suture uses itneatlogsEvery agent run is traced. Failed attempt + recovered attempt are compared (before/after).EntireRuntime code search/graph for the Investigator. Checkpoints on every commit made during development.cfo.aiBusiness model (pricing, unit economics, runway) lives in /business.
Evidence for judges is in /evidence (trace links, checkpoints, recovery notes).
Project structure
textsuture/
├── agents/           # Investigator, Implementer, Verifier, Recovery
├── tools/            # GitHub, Entire, test runner, trace reader, repo edit
├── runs/             # Per-run state records
├── evidence/         # Traces, checkpoints, before/after material
├── business/         # cfo.ai plan
├── frontend/         # Minimal web UI
├── demo/             # Demo script & assets
└── README.md
Demo path (what judges should see)

Paste a real issue that will initially fail a naïve fix.
First attempt fails → neatlogs shows the exact failure span.
Recovery agent changes strategy.
Second attempt passes tests.
PR is opened with trace IDs and plan summary.
Side-by-side before/after traces + Entire context + cfo.ai economics.

Building in public
All development commits are dated during neatHack (Oct 10–12, 2026).

Progress posts are tagged #neatHack.
License
MIT
