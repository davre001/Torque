# Slider acceptance

Pinned public fork revision: 218143b523252ee95c2368adc83fef95b324b156.
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
