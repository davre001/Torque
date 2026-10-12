# TORQUE launch film direction

Skill source: https://github.com/iart-ai/motion-design-skills/tree/main/skills
Applied: motion-art-direction, animation-principles, shot-composition,
remotion-video, logo-animation, color-motion and beat-sync-editing.

Intent: make a hackathon reviewer trust the demonstrated issue-to-PR result and
understand the specific observability incident that Neatlogs helped resolve.
Mood: precise, confident, deliberate. Corporate motion personality, calm/sharp.

| Rule | Locked choice |
| --- | --- |
| Canvas | 1920×1080, 30 fps, 16:9 |
| Grid | 12 columns, 104 px outer margins, 24 px gutters, 8 px baseline |
| Signature easing | cubic-bezier(0.2,0,0,1); ease-in-out only for camera moves |
| Timing | 0.4 s unit; entrances 0.4 s, hero 0.8 s, camera 1.6 s |
| Stagger | 2 frames, left-to-right or top-to-bottom |
| Transitions | hard cuts; motivated circular match cut for logo → pipeline |
| Intensity | text travel ≤32 px; camera scale 1→1.035; no overshoot |
| Hierarchy | one hero per shot; supporting label static after entrance |
| Ambient | low-contrast engineering grid, 20 s subtle periodic drift |
| Holds | ≥0.4 s after a reveal; longer holds for evidence reading |
| Palette | charcoal #101410, lime #CAEF72; ivory #F4F5EC and muted #9AA292 |

One signature moment: the incomplete diagnostic path resolves into a named
assertion, then the verified outcome. No uncontrolled text loops or decorative
camera rotation. Evidence remains readable and receives one camera move per shot.

Narration: Brielle preset. Final timings follow measured narration duration.
The timeline is provisional until voiceover transfer is approved and audio is
generated. A silent preview is not the final submission.

Accuracy: original issue-to-PR run and controlled instrumentation verification
are explicitly separate. Supplied PR #6 is a publication-recovery probe, so it
must not illustrate the original reduced-motion patch (#1). Entire uses the
recorded checkpoint c081469, not the later stalled checkpoint attempt. Financial
forecasts are labelled modeled assumptions. Any evidence graphic is labelled
as a graphic rather than represented as a captured application screen.

## Confirmed main PR recording
- Source: frontend/static/screen-capture (16).webm
- Inspected opening frame: davre001/kokon PR #1, Torque: verified fix for issue 4, matching saved run 6634790aa28943629348e02914d9b56c.
- Use this recording for the main reduced-motion PR segment. PR is open and ready for review in the recording; label it as a reviewable PR.

# Final delivery note

The user requested completion without generated voiceover on 2026-10-12. Final delivery is a silent video with on-screen narration. Remotion source is retained for future rendering; the actual export used the low-storage local renderer because dependency installation exhausted available disk space. See README.md for the final timeline and commands.
