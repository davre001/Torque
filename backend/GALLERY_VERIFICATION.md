# Gallery keyboard task

The new `gallery-keyboard` profile targets upstream
[kokon issue #2](https://github.com/GabrieleLozupone/kokon/issues/2).
The reviewed fork source is `davre001/kokon` at
`3b7fe6d714cf7764e54a877c69c64eb0bdb38655`. It already includes the earlier
reduced-motion fix, and the gallery accessibility bug remains present.

`backend/recipes.remote.json` now assigns this profile to `davre001/kokon`.
The legacy upstream recipe retains the reduced-motion profile. Historic evidence
and completed PRs are unchanged. Older unpublished fork runs must not use the new
recipe; the acceptance policy check rejects mismatched criteria.

The agent may edit only `src/components/Gallery.tsx` and `src/styles.css`.
The independent suite renders the actual Gallery component with fixture images,
API responses, icons, and native confirmation. It checks real browser keyboard
and mouse events. It does not run repository package scripts or require a GPU.
Full-app/Tauri/backend integration is outside this acceptance scope.

[Local calibration evidence](../evidence/gallery/acceptance-validation.json) records
the unchanged baseline failing three accessibility groups while mouse regression
passes, and a temporary positive fixture passing all four groups. The fixture patch
is saved for reproducibility; it is not an agent-generated fix or a verified PR.
The full automated backend suite passed 132 tests, with one Windows skip.

The remote workflow builds locked trusted test tooling before running the browser
in the existing Docker sandbox with no network, credentials, or writable source.
The compressed input is capped at 60,000 encoded bytes and 250,000 decoded bytes,
requires exactly the two approved file paths, and is checked against the profile
and pinned source. The remote job downloads the actual fork revision, rather than
substituting the upstream source. Result readback checks source/profile identity
as well as the request, workflow revision, and stable suite digest.
Preflight also rejects a deployed workflow that lacks gallery inputs, before
dispatching or constructing model clients.

## Before a live user run

- [ ] Commit and push the updated workflow and acceptance suite to Torque's runner branch.
- [ ] Run a hosted gallery baseline and confirm an assertion failure, not infrastructure failure.
- [ ] Create an open gallery issue on the fork; do not reuse its closed reduced-motion issue #2.
- [ ] Start/restart the API and worker using the updated code; submit the new fork issue URL.
- [ ] Verify the agent patch against all four acceptance criteria.
- [ ] Perform the publication-crash/reconciliation trial after verification; no automatic PR publication.

Suggested fork issue title:
`Gallery: make image cards and actions keyboard accessible`

Suggested body:

```text
Controlled Torque demo for upstream GabrieleLozupone/kokon#2.
The gallery keyboard bug remains at fork revision 3b7fe6d714cf7764e54a877c69c64eb0bdb38655.

Reproduce with two saved images: open Gallery, press Tab, then try opening a card
and accessing Favorite/Delete without using the mouse. Cards are skipped, actions
are hover-only, and thumbnails have empty alt text.

Expected:
- Cards are reachable with Tab and open with Enter or Space.
- Actions become visible on focus, have aria-labels, and work without opening the card.
- Thumbnails have meaningful prompt-derived alt text.
- Mouse opening, favoriting, and confirmed deletion continue to work.

Relevant files: src/components/Gallery.tsx and src/styles.css.
```

Changing GitHub App installation access does not change this reviewed test policy.
Additional repositories, tasks, or source revisions need explicit reviewed profiles.
