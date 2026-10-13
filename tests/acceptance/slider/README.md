# Slider acceptance

Pinned public fork revision: 218143b523252ee95c2368adc83fef95b324b156.
Also reviewed: 513883a43ea33474431c933018b6267d08acb8f5. Its only change
from the original pin is a comment in `src/components/Gallery.tsx`; slider
HTML and CSS are unchanged. The default `backend/recipes.remote.json` fork
entry now selects this slider profile for issue #7, replacing the already
completed gallery task. Other source revisions remain rejected.
Current-revision baseline checked October 13, 2026 with Edge: 1/5 groups
passed; slider semantics, keyboard input, sweep/focus, and image descriptions
failed assertions. Pointer/selection/media regressions passed. This reproduces
the unresolved issue; it is not a completed fix or recovery result.
Real site HTML/CSS run in a browser. External downloads and media are fixture
I/O; playback calls test reduced-motion/manual/normal branching, not decoding.
Five groups test semantics, keyboard bounds, sweep/focus, image descriptions,
and pointer/selection/media-call regressions. The suite is outside agent scope.
Local baseline: 1/5 passes. Temporary positive calibration fixture: 5/5 passes.
Neither is agent recovery evidence. See evidence/slider/acceptance-validation.json.

Run locally with an installed browser and Python Playwright:
python tests/acceptance/slider/test_slider.py <reviewed-workspace>
Set TORQUE_TEST_BROWSER to the browser executable if needed.
Hosted execution uses the reviewed Docker image and network-disabled container.
