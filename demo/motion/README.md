# TORQUE submission demo

Final video: `final/TORQUE-demo.mp4` — 2:08, 1280×720, 24 fps, H.264/yuv420p.
Silent, with on-screen narrative; voiceover omitted at the user's request after the Brielle generation was blocked by an empty provider credit balance.

The film follows the user-selected iart-ai motion-design skills: restrained charcoal/lime art direction, grid composition, short eased entrances, one primary subject per shot, a circular reveal, hard cuts and readable evidence holds.

It includes the actual issue, completed run, verification, correct kokon PR #1 recording, the complete Neatlogs recording, diagnostic/resolution evidence graphics, Entire checkpoint graphic and actual cfo.ai screenshot. The controlled diagnostic probe is labelled separately from the first-attempt issue-to-PR run. Financial forecasts are explicitly planning assumptions.

## Timeline

- 0:00–0:17 — problem and agent workflow
- 0:17–1:00 — issue, completed run, verification and PR
- 1:00–1:22 — complete supplied Neatlogs recording
- 1:22–1:43 — named assertion, unchanged passing check and shipped resolution
- 1:43–1:51 — Entire checkpoint and commit
- 1:51–2:02 — cfo.ai planning model
- 2:02–2:08 — closing

## Sources and rendering

`remotion/src/index.tsx` is the editable 1080p Remotion composition. Dependency installation could not complete because the drive ran out of space, so it was not used for this export and has not been render-validated.

The delivered MP4 was rendered locally by `render_local.py` using Pillow and FFmpeg, following the same storyboard and motion direction. This renderer uses a quartic ease-out approximation for entrances. Run:

```powershell
python demo/motion/remotion/prepare_assets.py
.venv/Scripts/python.exe demo/motion/render_local.py
```

To render the Remotion version after freeing sufficient disk space:

```powershell
cd demo/motion/remotion
npm install
npm run render
```

Original recordings remain untouched. The earlier `torque-motion-graphics.mp4` is the superseded basic graphics-only version. The new film is `final/TORQUE-demo.mp4`.

Validation: selected shot previews inspected; complete final video decoded without errors; format checked with ffprobe.
