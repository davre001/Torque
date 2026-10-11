# Controlled live recovery evidence

This is a controlled local drill, not the kokon production demo. The first patch was deliberately incorrect. The independent subprocess failed, Neatlogs finalized and returned that exact failed attempt, and live Claude recovery/implementation repaired it. The unchanged assertion then passed and live Gemini reviewed it. No GitHub calls, PR writes, or Docker execution occurred.

Run: `ce1d5d570a144e608d98d49031579dd2`. Main trace: `2b869453d595b5951eb2fd0fbb898021`.
Estimated model cost: $0.008778. See the manifest and readback records.

Failed trace: `e6417b8ff867e18db4fe1093548c91c2`, finalized ERROR. Main trace finalized OK with 16 spans and four LLM calls.

Provider accounting includes 3,484 tokens; hosted telemetry reports 2,639 because its Gemini counts omit 845 thinking tokens. Requested Gemini alias was `gemini-3.5-flash`; hosted spans report `gemini-3.6-flash`. See both records rather than assuming identical totals or model identifiers.

Passing attempt trace: `ff5d1966ea773563a23d1743ec4b3851`, finalized OK; saved in `passing-trace-2.json`.
