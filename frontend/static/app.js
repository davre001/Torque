/**
 * app.js — Torque Frontend
 *
 * Handles:
 *  - Form submit → POST /api/runs → get run_id
 *  - Poll GET /api/runs/{run_id} every 2 s while non-terminal
 *  - Render pipeline steps, attempt list, and final result
 *  - Demo mode: ?demo=1 pre-fills a known issue URL
 */

(function () {
  'use strict';

  /* ── Constants ── */
  const POLL_INTERVAL_MS = 2000;
  const TERMINAL_STATUSES = new Set(['completed', 'failed']);
  const AGENT_ORDER = ['investigator', 'implementer', 'recovery', 'verifier'];

  const STATUS_LABEL_MAP = {
    queued:        'Queued',
    investigating: 'Investigating',
    implementing:  'Implementing',
    verifying:     'Verifying',
    recovering:    'Recovering',
    completed:     'Completed',
    failed:        'Failed',
  };

  /* ── State ── */
  let pollTimer = null;
  let currentRunId = null;

  /* ── DOM refs ── */
  const form         = document.getElementById('run-form');
  const urlInput     = document.getElementById('issue-url');
  const runBtn       = document.getElementById('run-btn');
  const formError    = document.getElementById('form-error');
  const dashboard    = document.getElementById('dashboard');
  const agentsOv     = document.getElementById('agents-overview');

  const chipLabel    = document.getElementById('chip-label');
  const chipDot      = document.getElementById('chip-dot');
  const agentChip    = document.getElementById('agent-chip');

  const statusBadge  = document.getElementById('status-badge');
  const statusIssue  = document.getElementById('status-issue');
  const attemptCtr   = document.getElementById('attempt-counter');

  const pipelineEl   = document.getElementById('pipeline');
  const attemptsList = document.getElementById('attempts-list');
  const attemptEmpty = document.getElementById('attempt-empty');

  const resultSection = document.getElementById('result-section');
  const resultCard    = document.getElementById('result-card');

  /* ── Demo mode ── */
  const params = new URLSearchParams(window.location.search);
  if (params.get('demo') === '1') {
    urlInput.value = 'https://github.com/org/repo/issues/42';
  }

  /* ── Form submit ── */
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    formError.textContent = '';

    const issueUrl = urlInput.value.trim();
    if (!isValidGitHubIssueUrl(issueUrl)) {
      formError.textContent = 'Please enter a valid GitHub issue URL (e.g. https://github.com/org/repo/issues/42)';
      return;
    }

    runBtn.disabled = true;
    runBtn.querySelector('.btn-text').textContent = 'Starting…';

    try {
      const runId = await startRun(issueUrl);
      currentRunId = runId;
      showDashboard(issueUrl);
      startPolling(runId);
    } catch (err) {
      formError.textContent = err.message || 'Failed to start run. Is the server running?';
      runBtn.disabled = false;
      runBtn.querySelector('.btn-text').textContent = 'Run Torque';
    }
  });

  /* ── API helpers ── */
  async function startRun(issueUrl) {
    // In demo / standalone mode, use mock data if server isn't available
    try {
      const res = await fetch('/api/runs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ issue_url: issueUrl }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Server error ${res.status}`);
      }
      const data = await res.json();
      return data.run_id;
    } catch (err) {
      // If no server, fall through to demo simulation
      if (err instanceof TypeError && err.message.includes('fetch')) {
        return startDemoSimulation(issueUrl);
      }
      throw err;
    }
  }

  async function fetchRunState(runId) {
    // If it's a demo run, return simulated state
    if (runId.startsWith('demo_')) {
      return getDemoState(runId);
    }
    const res = await fetch(`/api/runs/${runId}`);
    if (!res.ok) throw new Error(`Failed to fetch run state: ${res.status}`);
    return res.json();
  }

  /* ── Demo simulation ── */
  // Simulates the agent pipeline locally for UI preview when no backend is running
  const demoTimeline = [
    { t: 0,    status: 'investigating', current_agent: 'investigator', attempts: [] },
    { t: 3000, status: 'implementing',  current_agent: 'implementer',
      attempts: [{ number: 1, status: 'running', trace_id: 'abc123', summary: 'Implementing fix in src/auth.py' }] },
    { t: 7000, status: 'recovering',    current_agent: 'recovery',
      attempts: [
        { number: 1, status: 'failed', trace_id: 'abc123', summary: 'Tests failed: AssertionError in test_auth.py::test_validate_token' },
        { number: 2, status: 'running', trace_id: 'def456', summary: 'Changing strategy: updating validation logic in src/utils.py instead' },
      ] },
    { t: 11000, status: 'verifying', current_agent: 'verifier',
      attempts: [
        { number: 1, status: 'failed', trace_id: 'abc123', summary: 'Tests failed: AssertionError in test_auth.py::test_validate_token' },
        { number: 2, status: 'done',   trace_id: 'def456', summary: 'All 42 tests passed' },
      ] },
    { t: 14000, status: 'completed', current_agent: null,
      pr_url: 'https://github.com/org/repo/pull/87',
      plan_summary: 'Updated token validation in src/utils.py and added regression test for edge case #42',
      attempts: [
        { number: 1, status: 'failed', trace_id: 'abc123', summary: 'Tests failed: AssertionError in test_auth.py::test_validate_token' },
        { number: 2, status: 'done',   trace_id: 'def456', summary: 'All 42 tests passed' },
      ] },
  ];

  let demoState = null;
  let demoStartTime = null;
  let demoIssueUrl = '';

  function startDemoSimulation(issueUrl) {
    const runId = `demo_${Date.now()}`;
    demoStartTime = Date.now();
    demoIssueUrl = issueUrl;
    demoState = null;
    return runId;
  }

  function getDemoState(runId) {
    const elapsed = Date.now() - demoStartTime;
    let frame = demoTimeline[0];
    for (const f of demoTimeline) {
      if (elapsed >= f.t) frame = f;
    }
    return {
      run_id: runId,
      issue_url: demoIssueUrl,
      status: frame.status,
      current_agent: frame.current_agent,
      attempts: frame.attempts || [],
      pr_url: frame.pr_url || null,
      plan_summary: frame.plan_summary || null,
    };
  }

  /* ── Polling ── */
  function startPolling(runId) {
    stopPolling();
    poll(runId);
  }

  function stopPolling() {
    if (pollTimer) { clearTimeout(pollTimer); pollTimer = null; }
  }

  async function poll(runId) {
    try {
      const state = await fetchRunState(runId);
      renderState(state);
      if (!TERMINAL_STATUSES.has(state.status)) {
        pollTimer = setTimeout(() => poll(runId), POLL_INTERVAL_MS);
      } else {
        setChip('idle');
        runBtn.disabled = false;
        runBtn.querySelector('.btn-text').textContent = 'Run Again';
      }
    } catch (err) {
      console.error('Poll error:', err);
      pollTimer = setTimeout(() => poll(runId), POLL_INTERVAL_MS * 2);
    }
  }

  /* ── UI show/hide ── */
  function showDashboard(issueUrl) {
    dashboard.removeAttribute('hidden');
    agentsOv.setAttribute('hidden', '');
    statusIssue.textContent = shortenIssueUrl(issueUrl);
    resetPipeline();
    attemptsList.innerHTML = '';
    if (attemptEmpty) {
      const li = document.createElement('li');
      li.className = 'attempt-empty';
      li.id = 'attempt-empty';
      li.textContent = 'No attempts yet';
      attemptsList.appendChild(li);
    }
    resultSection.setAttribute('hidden', '');
    resultCard.innerHTML = '';
    setChip('active');
  }

  /* ── State renderer ── */
  function renderState(state) {
    // Status badge
    statusBadge.dataset.status = state.status;
    statusBadge.textContent = STATUS_LABEL_MAP[state.status] || state.status;

    // Attempt counter
    const count = state.attempts ? state.attempts.length : 0;
    attemptCtr.textContent = count > 0 ? `Attempt ${count} of 3` : '';

    // Chip
    if (TERMINAL_STATUSES.has(state.status)) {
      setChip('idle');
    } else {
      setChip('active', STATUS_LABEL_MAP[state.status] || state.status);
    }

    // Pipeline
    renderPipeline(state);

    // Attempts
    renderAttempts(state.attempts || []);

    // Result
    if (state.status === 'completed' && state.pr_url) {
      renderResult(state);
    } else if (state.status === 'failed') {
      renderFailed(state);
    }
  }

  /* ── Pipeline renderer ── */
  function resetPipeline() {
    AGENT_ORDER.forEach(agent => {
      const step = document.getElementById(`step-${agent}`);
      if (step) {
        step.dataset.state = 'idle';
        const icon = step.querySelector('.step-status-icon');
        if (icon) { icon.textContent = ''; icon.className = 'step-status-icon'; }
      }
    });
    pipelineEl.querySelectorAll('.pipeline-connector').forEach(c => c.classList.remove('lit'));
  }

  function renderPipeline(state) {
    const activeAgent = state.current_agent;
    const isTerminal  = TERMINAL_STATUSES.has(state.status);
    const isFailed    = state.status === 'failed';

    let passedActive = false;

    AGENT_ORDER.forEach((agent, idx) => {
      const step = document.getElementById(`step-${agent}`);
      if (!step) return;

      const isActive = agent === activeAgent;
      const isPast   = !passedActive && !isActive;

      let stepState = 'idle';
      let iconContent = '';
      let iconClass = 'step-status-icon';

      if (isActive && !isTerminal) {
        stepState = 'active';
        iconClass += ' spinning';
        passedActive = true;
      } else if (isPast && activeAgent) {
        // was this agent in recovery path with failure?
        if (agent === 'implementer' && isFailed) {
          stepState = 'failed';
          iconContent = '✗';
        } else {
          stepState = 'done';
          iconContent = '✓';
        }
      } else if (isTerminal && !isActive) {
        if (agent === 'implementer' && isFailed && activeAgent !== 'verifier') {
          stepState = 'failed';
          iconContent = '✗';
        } else if (!passedActive && activeAgent) {
          // Came before active, mark done
          stepState = 'done';
          iconContent = '✓';
        }
      }

      // If completed, all done
      if (state.status === 'completed') {
        stepState = 'done';
        iconContent = '✓';
        iconClass = 'step-status-icon';
      }

      step.dataset.state = stepState;
      const icon = step.querySelector('.step-status-icon');
      if (icon) {
        icon.textContent = iconContent;
        icon.className = iconClass;
      }

      // Light connector before this step if step is done or active
      if (idx > 0) {
        const connectors = pipelineEl.querySelectorAll('.pipeline-connector');
        const connector = connectors[idx - 1];
        if (connector) {
          connector.classList.toggle('lit', stepState === 'done' || stepState === 'active');
        }
      }
    });
  }

  /* ── Attempts renderer ── */
  function renderAttempts(attempts) {
    attemptsList.innerHTML = '';
    if (!attempts.length) {
      const li = document.createElement('li');
      li.className = 'attempt-empty';
      li.textContent = 'No attempts yet';
      attemptsList.appendChild(li);
      return;
    }

    attempts.forEach(attempt => {
      const li = document.createElement('li');
      li.className = 'attempt-item';
      li.dataset.status = attempt.status;

      const statusText = {
        failed: 'Failed', running: 'Running', done: 'Passed',
      }[attempt.status] || attempt.status;

      li.innerHTML = `
        <span class="attempt-num">#${attempt.number}</span>
        <div class="attempt-body">
          <div class="attempt-status">${escapeHtml(statusText)}</div>
          ${attempt.summary ? `<div class="attempt-summary">${escapeHtml(attempt.summary)}</div>` : ''}
          ${attempt.trace_id ? `<div class="attempt-trace">neatlogs trace: <a href="#" aria-label="Trace ${attempt.trace_id}">${escapeHtml(attempt.trace_id)}</a></div>` : ''}
        </div>
      `;
      attemptsList.appendChild(li);
    });
  }

  /* ── Result renderers ── */
  function renderResult(state) {
    resultSection.removeAttribute('hidden');
    resultCard.innerHTML = `
      <a class="result-pr-link" href="${escapeHtml(state.pr_url)}" target="_blank" rel="noopener noreferrer">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
          <path d="M5 3.5A1.5 1.5 0 1 0 3.5 5V11a1.5 1.5 0 1 0 1 0V7.414l4.293 4.293a1 1 0 0 0 1.414-1.414L5.914 6H9.5a1.5 1.5 0 1 0 0-1H5.621A1.5 1.5 0 0 0 5 3.5z" fill="currentColor"/>
        </svg>
        Pull Request Opened ↗
      </a>
      <div class="result-meta">
        ${state.attempts ? `<span class="result-chip">${state.attempts.length} attempt${state.attempts.length !== 1 ? 's' : ''}</span>` : ''}
        <span class="result-chip">Verified ✓</span>
      </div>
      ${state.plan_summary ? `<p class="result-plan">${escapeHtml(state.plan_summary)}</p>` : ''}
    `;
  }

  function renderFailed(state) {
    resultSection.removeAttribute('hidden');
    resultCard.innerHTML = `
      <div class="result-failed">
        <span>✗</span>
        <span>Run failed after ${(state.attempts || []).length} attempt(s). Check neatlogs traces for details.</span>
      </div>
    `;
  }

  /* ── Chip ── */
  function setChip(mode, label) {
    if (mode === 'active') {
      agentChip.classList.add('active');
      chipLabel.textContent = label || 'Running';
    } else {
      agentChip.classList.remove('active');
      chipLabel.textContent = 'Idle';
    }
  }

  /* ── Utilities ── */
  function isValidGitHubIssueUrl(url) {
    return /^https:\/\/github\.com\/[^/]+\/[^/]+\/issues\/\d+/.test(url);
  }

  function shortenIssueUrl(url) {
    // "https://github.com/org/repo/issues/42" → "org/repo#42"
    const m = url.match(/github\.com\/([^/]+)\/([^/]+)\/issues\/(\d+)/);
    return m ? `${m[1]}/${m[2]}#${m[3]}` : url;
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

})();
