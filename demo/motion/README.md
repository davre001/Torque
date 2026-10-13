# TORQUE narrated demo — current delivery

The active edit uses a white background, black text, subtle monochrome motion elements and the actual logo from frontend/ui/public/logo.png.

Narration source: the supplied Belle B MP3 in the repository root. Audio is processed locally. edit-timing.json maps measured speech cues to 30 fps cuts; narration-alignment.json preserves the local ASR word estimates. Those estimates are approximate and are used for edit timing, not authoritative captions.

Key cues: Meet Torque 0:06.17; workflow 0:15.87; actual issue 0:25.40; completed run 0:38.33; named test diagnostics 1:06.97; exact assertion 1:16.77; passing check 1:19.57; resolved incident 1:23.13; Entire 1:31.60; cfo.ai 1:39.77; closing 1:53.83.

The new screen-capture (19).webm opens a different incident first. This edit uses its later portion containing the correct d5d9ddaa incident, diagnosis, recommendation and Resolved status. The recording does not show the written resolution note itself. The earlier trace recording supplies the original generic error, named failing child span and passing check.

Final delivery: final-v2/TORQUE-demo-final.mp4 — 1920x1080, 30 fps, approximately 2:01 including the ending hold. This supersedes the previous silent 720p video.

Editable canvas composition: launch-v2.html. Local renderer: render_browser.py. Timing compiler: build_timing.py. Applied project skills are in skills/; all four user-supplied skills passed validation after moving version into supported metadata.

Render commands:

```powershell
.venv/Scripts/python.exe demo/motion/build_timing.py
.venv/Scripts/python.exe demo/motion/render_browser.py --preview
.venv/Scripts/python.exe demo/motion/render_browser.py
```

Speech alignment can be regenerated with align_narration.py once the local model is available. The downloaded model and intermediate picture export are ignored by Git.

The closing card includes the demo address `torque-pied.vercel.app` in a rounded monochrome browser field. The address types in from 117.53?118.93 seconds and remains visible through the ending hold. `assemble_final.py` replaces the outro while preserving the narration; export-verification.json records the final stream metadata.

Export verified: 1920x1080 H.264, 30 fps, 3,642 frames, 121.4 seconds; AAC narration matches video duration. Full video/audio decode passed.
