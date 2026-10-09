# Torque

**An agent that turns a GitHub issue into a verified pull request — and recovers when it fails.**

Suture is a multi-agent system built for [neatHack](https://neatlogs.com/hackathon).
Give it a GitHub issue URL. It investigates the codebase (via Entire), implements a fix, runs tests, and opens a PR. If an attempt fails, a Recovery agent reads the neatlogs trace of that failure, changes strategy, and tries again.

> Agents you’d trust to run without watching.

## How it works

```text
Issue URL
   ↓
Investigator (+ Entire search/graph)
   ↓ diagnosis + plan
Implementer → edit code, run tests, commit
   ↓
   ├─ Pass → Verifier → open Pull Request ✅
   └─ Fail → Recovery reads neatlogs trace → new strategy → retry
```

## Agents

- **Investigator** – reads the issue and uses Entire for precise code context
- **Implementer** – makes changes in an isolated worktree and runs tests
- **Verifier** – checks the diff and test output against the issue
- **Recovery** – inspects the failed neatlogs trace and decides what to do next

## Quick start

### Prerequisites

- Python 3.11+
- GitHub token with `repo` scope (`GITHUB_TOKEN`)
- neatlogs API key (`NEATLOGS_API_KEY`)
- LLM key (OpenAI / Anthropic / Bedrock)
- Entire CLI (for checkpoints and search)

### Install

```bash
git clone https://github.com/<you>/suture
cd suture
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
```

Fill in your `.env` file:

```dotenv
NEATLOGS_API_KEY=
GITHUB_TOKEN=
OPENAI_API_KEY=
# Or configure ANTHROPIC_API_KEY / AWS credentials
```

### Run from the CLI

```bash
python -m suture run https://github.com/org/repo/issues/42
```

### Run from the web UI

```bash
uvicorn frontend.app:app --reload --port 8000
```

Then open [http://localhost:8000](http://localhost:8000), paste an issue URL, and click **Run Suture**. Live status, attempt history, and the final PR link appear on the page.

## Required neatHack integrations

| Tool | How Suture uses it |
|---|---|
| **neatlogs** | Every agent run is traced. Failed and recovered attempts are compared (before/after). |
| **Entire** | Runtime code search/graph for the Investigator. Checkpoints on every commit made during development. |

## Business model and judge evidence

- **Business model:** The business model (pricing, unit economics, and runway) lives in `/business`.
- **Judge evidence:** Trace links, checkpoints, and recovery notes are in `/evidence`.

## Project structure

```text
suture/
├── agents/           # Investigator, Implementer, Verifier, Recovery
├── tools/            # GitHub, Entire, test runner, trace reader, repo edit
├── runs/             # Per-run state records
├── evidence/         # Traces, checkpoints, before/after material
├── business/         # cfo.ai plan
├── frontend/         # Minimal web UI
├── demo/             # Demo script and assets
└── README.md
```

## Demo path (what judges should see)

1. Paste a real issue that will initially fail with a naïve fix.
2. The first attempt fails; neatlogs shows the exact failure span.
3. The Recovery agent changes strategy.
4. The second attempt passes tests.
5. A pull request is opened with trace IDs and a plan summary.
6. Show side-by-side before/after traces, Entire context, and cfo.ai economics.

## Building in public

- All development commits are dated during neatHack (October 10–12, 2026).
- Progress posts are tagged `#neatHack`.

## License

MIT
