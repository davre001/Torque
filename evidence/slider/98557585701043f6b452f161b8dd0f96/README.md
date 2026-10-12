# Live slider recovery trial ? failed, preserved honestly

Issue: https://github.com/davre001/kokon/issues/7
Run: `98557585701043f6b452f161b8dd0f96` (GitHub App user davre001).
Real Claude calls, real pinned source, runtime Entire history, independent hosted
browser tests. No failure was injected and no positive calibration fixture entered
this run. Attempts 1/2 passed 4/5 groups but mishandled zero slider value. Attempt 3
returned an incremental edit against the original baseline and lost prior changes,
passing only 1/5. Both configured recovery retries were used; the run safely failed.

Recovery 1 used local artifacts after an HTTP 404. Recovery 2 retrieved its actual
failed Neatlogs trace; see failed-trace-2.json and recovery-2.json. This demonstrates
real live failure/readback/recovery attempts, not successful verified recovery.
Actual estimated model cost: $0.281697. No PR was created.

The implementation prompt now explicitly requires a complete replacement solution
from pinned originals on every retry. That change has not had a new live trial.
See manifest.json for references and exported file hashes.
