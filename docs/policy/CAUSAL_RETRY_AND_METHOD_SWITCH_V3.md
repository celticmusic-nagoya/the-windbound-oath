# Adaptive Causal Retry & Continuation Policy v3 — 2026-11-20

Director-approved. Applies to all AI agents and automation, all game development and asset production. Supersedes v2 and older numeric stop rules for retry semantics only.

- Two failures of the same method/root cause trigger evidence-based reassessment, not mandatory termination. No fixed lifetime attempt cap.
- Continue the same method when measured improvement, newly diagnosed cause, credible corrective hypothesis or useful new evidence justifies the next bounded attempt. Record baseline, cumulative failures, evidence, changed condition, expected measurable result, time/cost budget and stop condition before retrying. Do not rename methods or reset counters.
- Switch or stop only when further work is reasonably judged wasteful: repeated no-progress without credible correction, demonstrated technical limits, or disproportionate cost/time relative to expected quality gain. Continue independent tasks; mark unavailable inputs BLOCKED.
- Preserve all historical failure ledgers, sources, hashes and artifacts. Reassess previously stopped methods only with evidence; never blindly rerun.
- G1–G4, independent QA, source/license protection, approval and cost gates remain binding. No asset adoption, release or canon change implied.
- Existing hard-cap validators remain technical blockers until explicitly aligned and regression-tested. Never bypass them, falsify counts or relabel families to evade them. Report the blocker and use owning PR to update validation compatibly with historical records.
- Reports distinguish executed work, PASS/FAIL/BLOCKED/NOT_RUN, next hypothesis and expected quality gain.
