# Independent QA — DEV-WALK-MOTION-02

Verdict: PASS
Reviewed head: `9fa6b89ead967f2ec860a0c3e04e46ee259accc7`
Baseline: `3d1794340feb7210f209ae4beea2dc879034e92f`
Reviewer: independent Codex agent; no product/repository edits or integration operations.

Read AGENTS.md, docs/handoff/AI_HANDOFF_PROTOCOL.md and codex-standing-orders.md. Inspected all eight committed changed paths and current DEV rendering/timer path. Stride descriptors are cloned, settings remain page-local, only Aidan side-walk receives override, live changes preserve fractional phase and existing RAF. Input covers 40–300 on ten-grid plus off-grid adopted72 preset. Independent playback rate is retained. Index changes only the two DEV cache tags. No runtime movement, save, assets, map, production stride or registry change exists in committed diff.

Own checks:
- Final strictly serial m56 real UI/PNG cadence: exit0, 215 assertions PASS across desktop1920x1080, emulated portrait390x844, landscape844x390; URL seed/reload/isolation checks PASS. Evidence m56-browser.log and screens/*.json/png; final serial start 2026-11-03T05:13:00Z, end 2026-11-03T05:13:58Z. Portrait screenshot visually reviewed: slider/presets/text usable within scrollable panel.
- Classifier negative controls: positive reference plus all eight rejected deviations PASS; negative-controls.log.
- Real positive classifier probe at reviewed head: original HTTP still delayed3s, browser naturally aborts its pre-DEV image request, actual decoded currentSrc differs and belongs to BattleMotion.frames idle registry. expected_retarget accepts this actual event; no route.abort or game-state writes, no unexpected errors. positive.py/json/log. Probe was rerun serially after initial m56 for final classifier evidence. Initial exploratory probe overlapped initial m56; exploratory-m56-browser.log and exploratory-screens preserve that run, which is excluded as final cadence timing evidence. Final strictly serial m56 rerun completed after all probes closed; all215 assertions PASS with FAILS0 and exit0. Final cadence evidence is screens/stride-cadences.json; timestamps are serial-m56-start.txt/end.txt.
- Fresh all259 protected portrait hashes match adoption ledgers, no protected changed paths. static.json.
- Verified original exact-head QA provenance: three test-file before/after hashes match reviewed checkout; verified-qa/results.json source_head matches reviewed head. Raw m55 4423 assertions PASS, 399 slots per view (1197 total), final FAILS0; m56 215 PASS; helper controls PASS. Prior failed logs retained separately. No fourth complete m55 execution performed (retry cap).
- Reviewed prior node-final results:17 entries exit0/no failure lines; regressions save/continue, m31, asset audit, goblin assets PASS. Earlier regression m55 startup cancellation failure is retained and superseded only by exact-head verified results and focused actual classifier proof.

The network exception is narrow: exact original URL, image, ERR_ABORTED, before DEV, loaded different replacement registered in current idle definitions. Other failed requests immediately remain fatal; pageerror/console/HTTP errors remain fatal. Replacement wait failure fails execution. This is not an unconditional skip.

Physical Android: NOT_RUN. Emulated layouts are not physical QA. Untracked docs/qa/DEV-WALK-MOTION-02.md was present and is excluded from this SHA-specific verdict; any later commit requires exact-head delta review. No unresolved blocker found within authorized DEV scope. This verdict alone is not a merge operation or asset adoption.
