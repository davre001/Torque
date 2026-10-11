# Live worker restart and cancellation verification

The isolated local drill uses actual Python worker processes, a real localhost API,
and a separate SQLite database. Its processor deliberately performs fixture work;
it does not call models, GitHub, or execute repository code.

```powershell
.\.venv\Scripts\python.exe -m backend.lifecycle_probe
```

Saved [local results](../evidence/lifecycle/ebe2cff1ed6c43ab8366999cd54b1579/report.json):

- Hard kills during investigation, implementation, verification, and recovery were
  followed by a worker restart after lease expiry. Each run became interrupted,
  executed once, was not replayed, and rejected the stale owner's heartbeat.
- Cancelling a queued job through the HTTP API prevented execution.
- A running job renewed its lease while the API process was killed and restarted.
  The restarted API read its persisted verifying state.
- Cancelling that running job through the restarted API stopped the worker
  cooperatively and persisted cancelled status.
- Calling `Worker.stop()` from a fixture trigger produced an interrupted outcome.
  This last check does not test delivery of an operating-system shutdown signal.

The separate remote drill dispatches one reviewed public kokon test job and cancels
it while in progress using the real `ActionsRunner` cancellation path:

```powershell
.\.venv\Scripts\python.exe -m backend.lifecycle_probe --remote
```

It requires the existing cached reviewed workspace and Actions configuration.
Saved [remote results](../evidence/lifecycle/95cecd4f46a5427ea5f34436633402b0/report.json)
confirm [Actions run 38177020201](https://github.com/davre001/Torque/actions/runs/38177020201)
completed with conclusion `cancelled`. No model calls or PR writes occurred.

These drills do not modify the production database. They prove local lifecycle
and remote cancellation behavior, not interruption inside a real provider request,
OS-signal-specific graceful shutdown, or a crash during GitHub PR publication.
Publication lost-response reconciliation remains covered by mocked tests; a live
publication crash/recovery acceptance trial is still pending.
