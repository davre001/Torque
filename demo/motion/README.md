# TORQUE motion graphics

60-second silent graphics sequence, 1280x720, 24 fps. Native Higgsedit source is in `torque-motion.jsx`. Import this MP4 as an opening/interlude sequence, or cut its scenes around actual screen recordings.

| Time | Scene |
| --- | --- |
| 0-7 | TORQUE introduction |
| 7-14 | Problem |
| 14-24 | Agent workflow |
| 24-36 | Controlled trace-informed recovery |
| 36-44 | Entire development checkpoints |
| 44-53 | cfo.ai financial planning |
| 53-60 | Closing |

## Recordings required for submission assembly

- TORQUE issue, completed run, browser test results, and verified draft PR.
- Neatlogs critical-incidents feature: actual incident, diagnosis, and resolution, with failure and passing traces.
- Entire checkpoint and associated commit.
- cfo.ai model; screenshots already exist in `cfo.ai/screenshots/`.

The graphics illustrate the workflow. They do not substitute for a recording of the critical-incidents feature. The GitHub example passed on attempt one; the recovery drill used a deliberately incorrect first patch and is a separate demonstration.

## Optional voiceover aligned to this graphics sequence

0-7: TORQUE turns a GitHub issue into a verified pull request, with recovery when an attempt fails.

7-14: Fixing an issue means understanding the code, proving the patch works, and handling failures along the way.

14-24: TORQUE coordinates investigation, implementation, and verification. It tests a patch in an isolated workflow and reviews the result against the issue.

24-36: In a controlled recovery drill, we deliberately seeded an incorrect patch. Neatlogs returned the finalized failure trace. Recovery revised the implementation, and the unchanged assertion passed.

36-44: During development, Entire captured agent-assisted work in checkpoints linked to commits, preserving a record of the changes.

44-53: With cfo.ai, we modeled pricing, inference and recovery costs, and how usage and success rates affect margins. These forecasts remain planning assumptions.

53-60: TORQUE: fix, verify, recover. A real issue-to-PR result, alongside a separate controlled recovery demonstration.

## Build

Run in a Higgsedit environment. Set the source project directory to the desired location before building.

```bash
higgsedit build torque-motion.jsx
higgsedit fonts add /home/user/torque-motion Inter:400 Inter:700
higgsedit build torque-motion.jsx
higgsedit render /home/user/torque-motion --out renders/torque-motion-graphics.mp4
```
