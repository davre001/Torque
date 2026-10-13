# TORQUE demo video — script and motion direction

Status: approved plan in production. Supplied Belle B narration is aligned locally; the updated white-background 1080p export is rendering.

## Creative brief

**Audience:** submission judges seeing TORQUE for the first time.

**Message:** TORQUE turns a GitHub issue into a tested, independently verified pull request, with evidence that makes both results and failures reviewable.

**Mood:** precise, polished, confident. Premium motion personality: restrained movement, clear hierarchy, deliberate pauses. Target approximately **2 minutes 20 seconds**, adjusted to the measured ElevenLabs narration rather than forcing speech into fixed windows.

The video must show the problem TORQUE solves, how cfo.ai and Entire contributed, and how Neatlogs' critical-incidents feature helped identify and resolve an incident. The Neatlogs section receives the longest evidence hold.

## Skills and visual identity

Use the supplied instructions directly:

- `SKILL (2).md`: motion art direction; governs the complete film.
- `SKILL.md`: motion background; subtle, periodic ambience behind graphics on a white canvas.
- `SKILL (1).md`: logo animation; one reveal technique and intact geometry.
- `SKILL (3).md`: beat-sync editing; narrative arc and frame-accurate cut plan.

**Logo:** `frontend/ui/public/logo.png`, inspected and confirmed as the actual white circular TORQUE mark. Preserve its proportions, cutouts and clear space. Reveal the existing image with a mask; do not redraw it as a clock or substitute another symbol. Deliver a static final-frame poster alongside the video.

**Palette:** black and white only. White background with black text. Background motion uses subtle black-opacity elements over white. Convert recordings and screenshots to grayscale for the export so the whole film obeys the palette; keep originals untouched.

**Layout:** 1920×1080, 30 fps, 16:9. Use 96 px safe margins and a consistent 12-column grid. Full-screen evidence should occupy most of the frame. Avoid persistent dashboard-like headings, numbered footers and boxed cards around every shot. Alternate spacious typography with close, readable application footage.

**Typography:** one sans-serif family, two weights. Titles 76–100 px; short supporting text 34–42 px; evidence labels at least 28 px. Headlines contain one idea, usually 3–7 words. The voiceover explains details; screen text carries the takeaway.

## Locked motion language

| Property | Decision |
| --- | --- |
| Personality | Premium; calm, precise, deliberate |
| Signature easing | `cubic-bezier(0.4, 0, 0.2, 1)` for entrances, exits and camera moves |
| Timing unit | 0.4 s / 12 frames; title entrances 0.4 s, major moves 0.8 s, logo reveal 1.6 s |
| Text movement | Masked line reveal with a maximum 24 px vertical translation; opacity settles once |
| Stagger | 2 frames between grouped lines; complete grouped reveal within 0.8 s |
| Scale budget | Evidence camera 1.00→1.025 over 1.6 s; no overshoot |
| Transitions | Hard cuts within evidence; shape-matched cuts at section boundaries; one restrained dissolve if needed |
| Hold discipline | At least 0.4 s after a reveal; 3–6 s on readable evidence details |
| Ambient layer | Subtle black-opacity circles/soft monochrome mesh, 3–6% visual strength, seamless 24 s loop |
| Restraint | One primary moving subject per shot; labels settle; background fades away behind dense evidence |

Use **line-level** reveals rather than animating every letter. No typing effects, bouncing words, overshoot, spinning screens, continuous text movement or full-frame sliding panels. A shot's support label enters after its hero settles.

The single signature moment is the Neatlogs diagnosis: a generic failure resolves into a named check and its exact assertion, followed by the verified passing check. The logo reveal remains restrained so it does not compete with this moment.

## Narration draft

Read in a warm, confident female product-launch voice. Conversational and precise, with a short pause at each paragraph. Use ElevenLabs; the previously selected Brielle voice is a tone reference unless that exact voice is available in the connected account.

> Reporting an issue takes seconds. Delivering a fix you can trust takes more.
>
> Meet Torque. It turns GitHub issues into tested, independently verified pull requests, with bounded recovery when an attempt fails.
>
> Torque investigates the issue, prepares a patch, runs acceptance tests, and independently checks the result against the original requirements.
>
> Here is a real example. A website kept autoplaying its demo video, even when a visitor requested reduced motion. Torque reproduced the accessibility bug and implemented a targeted fix.
>
> The run completed on its first attempt. Three independent browser checks passed. The verifier approved the change. And the resulting pull request contains a patch a developer can review.
>
> But a reliable agent also needs failures you can understand.
>
> Neatlogs' critical-incidents feature surfaced an observability gap. Acceptance tests were failing with a generic error, without individual check details or useful stack traces.
>
> We added named test spans, captured output, and bounded failure diagnostics. A controlled failing check then exposed its exact assertion: expected ten, actual eight.
>
> Correcting the fixture made the unchanged check pass. We separately verified the remote browser workflow, merged the instrumentation fix, and documented the evidence in the resolved incident.
>
> Entire captured agent-assisted development in checkpoints linked to commits, preserving the work behind our changes.
>
> With C F O dot A I, we modeled pricing, inference costs, recovery costs, and financial scenarios. These forecasts are planning assumptions, informed by a small sample of measured runs.
>
> Torque. From issue to evidence. From patch to verified pull request.

Pronunciation: TORQUE as “tork”; Neatlogs as “neet logs”; Entire as the ordinary word; cfo.ai as “C F O dot A I.” Do not send performance directions as spoken text.

## Storyboard and provisional timing

These timecodes are planning targets, not locked audio timings. At 30 fps the proposed boundaries are frames **0, 180, 390, 720, 1110, 1440, 1620, 1950, 2430, 2910, 3210, 3930, 4200**.

| Time / frames | Narration cue | Screen and evidence | Motion and transition |
| --- | --- | --- | --- |
| 0:00–0:06 / 0–179 | “Reporting an issue…” | White canvas; **A fix you can trust.** | Headline reveals as one masked line. Hold before the brand appears. |
| 0:06–0:13 / 180–389 | “Meet Torque…” | Actual landing-page recording from `screen-capture (18).webm`; **Meet TORQUE.** followed by **Issue → verified PR** | Cut to the landing page exactly on “Meet.” Reveal the short title with a 0.4 s line mask, then hold. Use one 1.6 s gentle push toward the page hero. Clear the text before transitioning to the workflow. |
| 0:13–0:24 / 390–719 | “Torque investigates…” | **Investigate → Implement → Test → Verify** | One signal moves through four stationary stages. Labels reveal in reading order. Last node settles before the footage cut. |
| 0:24–0:37 / 720–1109 | “Here is a real example…” | Original GitHub issue; **Respect reduced motion.** | Brief title, then nearly full-screen recording. One gentle crop/push toward the requirement. Hold long enough to read it. |
| 0:37–0:48 / 1110–1439 | “The run completed…” | Completed run, three passing checks, verifier approval | Three clean cuts: run status → actual test results → verified result. Short settled overlays: **Completed**, **3 checks passed**, **Approved**. |
| 0:48–0:54 / 1440–1619 | “The resulting pull request…” | Correct kokon PR #1 recording; title/body and patch | Show title briefly, then the actual diff. Overlay **Ready for review**. Cut on a settled view, not during a scroll. |
| 0:54–1:05 / 1620–1949 | “Failures you can understand…” | Neatlogs critical-incidents page; incident title and finding | Let the incident page be the hero. Identify **Missing test diagnostics** with one small annotation. This must show the feature, not just traces. |
| 1:05–1:21 / 1950–2429 | “Acceptance tests were failing…” | Original generic error, then failing child span and assertion | Hard cut from original trace to instrumented trace. Match the output area's location. Reveal **Expected 10. Actual 8.** once, then hold. |
| 1:21–1:37 / 2430–2909 | “Correcting the fixture…” | Passing trace → remote workflow evidence → resolved incident note | Show the unchanged check passing. Return to the incident's resolution note. Label the probe **Controlled instrumentation verification**. |
| 1:37–1:47 / 2910–3209 | “Entire captured…” | Actual checkpoint/commit evidence; **The work behind the change.** | Checkpoint connects to commit with one line-draw. Use a real capture if available; otherwise label the graphic as recorded evidence. |
| 1:47–2:11 / 3210–3929 | “With C F O dot A I…” | Actual cfo.ai summary and assumptions screenshots | Three deliberate focuses: pricing → inference/recovery costs → scenario planning. Keep **Modeled assumptions** visible. Crosscut on narration clauses; no invented revenue chart. |
| 2:11–2:20 / 3930–4199 | “Torque. From issue…” | Actual logo, **From issue to evidence.**, then **Verified pull requests.** | Repeat the same mask language in reverse order: text settles, mark holds. Finish with at least 2 s of complete stillness. |

## Text animation and transition choreography

Text animations are part of the final edit, not static title cards. Each title reveals through a line mask with 24 px of upward travel over 12 frames, using the locked Premium easing. Supporting text follows two frames later where it does not compete with footage. Hold the completed text before its 12-frame masked exit. Keep important application details unobscured.

- **Opening → landing page:** finish the opening headline, then cut to `screen-capture (18).webm` on the spoken “Meet Torque.” The real landing page is the primary subject. Place **Meet TORQUE.** in an unobstructed area, reveal once, and settle. Convert the recording to monochrome for the black-and-white film.
- **Landing page → workflow:** exit the title, settle the footage, then use a clean cut into the four-stage workflow. Use a shape match only if the recorded page contains a suitably positioned logo; do not force a match or distort the page.
- **Workflow → issue:** the verification node settles; its label exits through the same mask, followed by a hard cut to the issue requirement. The next title enters after the cut rather than sliding the entire screen.
- **Run → tests → PR:** preserve the screen position of the relevant evidence with straight cuts. Reveal one short result label per shot; clear it before the next label. Avoid animated scrolls while a reviewer is reading a result.
- **Generic error → named failure → passing check:** match the diagnostic output areas, cut cleanly, and reveal the exact assertion as the visual peak. Hold it for reading. The passing check receives a restrained text reveal rather than a celebratory burst.
- **Neatlogs → Entire → cfo.ai:** use short masked section headings, then let the evidence fill the screen. A single 12-frame dissolve may bridge genuinely different layouts; otherwise retain clean cuts.
- **Closing:** return to the actual public-folder logo. Give it the planned 1.6 s mask reveal, then reveal the closing line once. Both settle into the static final frame.

Align these entrances and transitions to the measured narration. The landing page must appear at “Meet Torque” even if the provisional timestamp changes after ElevenLabs generation. Keep every text animation and transition within the shared easing, timing, motion-budget and hold rules.

## Neatlogs evidence sequence — required priority

Show the actual critical-incidents feature as part of the story:

1. Open incident `d5d9ddaa-09d9-4d5f-b73e-16128ecf6e3d`: **Investigate Independent Acceptance Test Failures**. Show its finding about missing granular diagnostics.
2. Show original trace `e6417b8ff867e18db4fe1093548c91c2`: generic acceptance error without child test details.
3. Show failing controlled trace `3d1061326c1185af4bec2113b7ebe57d`: select the child span and expose test name, stderr and assertion stack.
4. Show passing trace `b08c025e327bcaf698b4b1348e57a2e8`: the same check passes after the fixture correction.
5. Return to the incident and show **Resolved** plus the recorded verification/merge note.

The actual application acceptance defect was not diagnosed by those original traces alone. The established fix is improved test observability. The controlled fixture proves diagnostic visibility; it does not demonstrate an autonomous recovery of the original issue. Browser workflow checks are separate evidence; their logs were not uploaded to Neatlogs.

The earlier export included the full supplied trace recording, but a final edit must explicitly verify that the incident feature and resolution note are visible. If the provided clip lacks those views, capture them before final assembly rather than substituting a graphic for the required feature.

## Asset map and accuracy

| Purpose | Local source / record |
| --- | --- |
| Brand mark | `frontend/ui/public/logo.png` |
| Landing page at “Meet Torque” | `screen-capture (18).webm` in the repository root; file presence confirmed |
| Original issue | `frontend/static/ORIGINal github issue.webm` |
| Completed run | `frontend/static/run-json.webm` |
| Tests | `frontend/static/test 1-json.png`; `evidence/runs/6634790aa28943629348e02914d9b56c/tests-1.json` |
| Verification | `frontend/static/verified-json.webm`; saved `verified.json` in the same run folder |
| Correct PR | `frontend/static/screen-capture (16).webm`; https://github.com/davre001/kokon/pull/1 |
| Neatlogs | `frontend/static/resolution.webm`; controlled diagnostics in `evidence/acceptance-telemetry/c654b3eda3644bcf934215a577de51eb/` |
| Entire | Recorded checkpoint `01M4K5QBAVZ507XR140XFW7586`, linked commit `c081469dacf1…` |
| cfo.ai | `cfo.ai/screenshots/torque-plan-summary.png`, `torque-assumptions.png`, `unit-economics-and-sensitivity.png` |

`Published PR.webm` shows a separate publication-recovery probe. Do not use it as the main reduced-motion PR. The main run succeeded on its first attempt. The captured PR is open and ready for review; do not claim it was merged or is still a draft. TORQUE's instrumentation PR #1 and kokon's demo PR #1 are different pull requests.

Use evidence graphics only when clearly labelled. No fabricated dashboard, test output or incident resolution. Use short IDs on-screen and keep full IDs in this plan. Exclude credentials, environment files and private settings from captures.

## Voiceover, sound and beat timing

**ElevenLabs:** prepare and approve the exact spoken text, then connect the account using an API key stored locally. When audio generation is needed, ask the user to place the key in a dedicated local secret setting; never ask them to paste it into chat or place it in this document. Confirm an available voice with the warm female product-launch delivery they requested.

**Sound direction:** narration first. Optional restrained instrumental bed, with no vocals, only from a supplied or properly licensed track. Music should stay well below narration. Reserve one quiet accent for the diagnosis reveal. No stock whoosh on every cut.

**Beat-sync plan:** until a track is selected, use narration clause boundaries as the timing guide. Do not invent a BPM or claim the edit is synchronized. After selecting audio, record its actual BPM and first-beat offset, compute `frame = round((offset + beatIndex × 60 / BPM) × 30)`, and align structural cuts to 8–16-beat phrases where the evidence remains readable. Round cumulative beat positions to prevent drift. Speech clarity and evidence holds take priority over snapping every cut to music.

**Energy arc:** establish quietly → build through agent/result → tighten around the generic failure → land the named assertion as the single peak → release into the passing check → settle through Entire, cfo.ai and closing. Retain natural-speed evidence footage; skip speed ramps that make diagnostic content unreadable.

## Production gates

1. Review this script and storyboard before generating narration or rendering the new film.
2. Verify all required footage, especially the Neatlogs incident page and resolution note; gather missing views.
3. Check storage and render dependencies before starting a full render. Target true 1080p; do not silently substitute the earlier low-storage export.
4. Generate ElevenLabs narration and measure each paragraph. Revise the provisional timecodes and absolute cut frames to match that audio.
5. Render a logo test and representative title, evidence and diagnosis frames. Inspect start/middle/end states for smoothness, geometry, clipping and contrast.
6. Assemble and review the complete sequence with audio. Hold on text and evidence; remove any animation that competes with reading.
7. Export H.264 MP4, 1920×1080, 30 fps, yuv420p, with narration and a static logo poster. Keep editable source and final frame timing with the deliverable.
8. Decode the final file, inspect beginning/middle/end, check duration and audio levels, and audit all three submission requirements against the actual film.

## Submission reference

The supplied guidelines require one video covering the agent's problem, cfo.ai and Entire's contribution, and Neatlogs-assisted incident identification and resolution.

Reference feature demonstration supplied by the organizers: https://drive.google.com/file/d/1TLu1aTcXnjlHfWAMgTIfuzjV8wRXJ-yJ/view?usp=sharing . Its content still needs to be reviewed before final assembly; this draft uses the written guidelines provided in chat.

The announcement says submissions **start** October 12 at 7 pm IST; it does not specify a closing deadline. Confirm the final upload requirements separately.


Production update: use a WHITE background, BLACK text and subtle monochrome motion. New Neatlogs feature capture: frontend/static/screen-capture (19).webm. The spoken cues are now measured from the supplied Belle B narration in demo/motion/edit-timing.json.

Ending update: reveal a white rounded browser/address field with a thin black outline below the closing lines. Type `torque-pied.vercel.app` from 117.53 to 118.93 seconds, then hold the complete address through the final frame. Keep all other closing text settled; the cursor disappears when typing finishes.
