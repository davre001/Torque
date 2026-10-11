# Independent gallery browser acceptance

This suite bundles the real public `Gallery.tsx` with trusted React and fixture I/O.
It serves the real CSS with its external font import removed. Icons preserve their
requested sizes; only icon geometry, shared toolbar controls, API/store I/O, and
native confirmation are fixtures. Card and action event handling is actual source.

Four independent groups check card keyboard access, action keyboard access and
confirmation, prompt-derived alt text, and mouse regressions. A mount failure is
infrastructure, not an acceptance failure. Each group starts with fresh fixtures.

`package-lock.json` pins test dependencies. Docker installs them with scripts
disabled; repository package scripts are never run. The bundle is built in /tmp,
outside the read-only source mount. The agent cannot edit this suite.

For a local fixture check with installed trusted tooling and Playwright:

```powershell
$env:NODE_PATH=(Resolve-Path var/gallery-tools/node_modules).Path
$env:TORQUE_TEST_BROWSER='C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
.\.venv\Scripts\python.exe tests/acceptance/gallery/test_gallery.py <reviewed-source-directory>
```

Local browser checks do not prove the hosted Docker image works. The hosted
baseline is a separate deployment gate; see backend/GALLERY_VERIFICATION.md.
