# UP07 — independent read-only STOP review

**Disposition: BLOCKED / HOLD production QA and merge.** User's problem-stop instruction applies. No browser rerun, retry, source/test change, expectation relaxation or implementation fix by reviewer. Static protection PASS is not production-playtest PASS.

Fixed attempted source `7c7ea60232c993eff98d52593de4d94d392bdbaf`; baseline main `6e28466751f124fc5a483be3d89c65f35a320b5c`.

## Observed failure and evidence limits

Root's first production m67 run passed exact adopted bytes/fullcanvas, real registered five-key bank, no QA fixture/02alias, PC straight and UL checks, and PC UR real decoded five-source order/wrap. It then printed `FAIL pc/ur 90world/.300second measured` and stopped. This is an actual unresolved test FAIL; do not replace with prior PR154 QA-fixture PASS or static metadata PASS.

The failed assertion combines3 conditions: cycle count>=4, median Euclidean cycle displacement within12world of90, median elapsed cycle seconds within.08 of.300. The log does not identify which conjunct failed or supply its numeric value. field_check raises before the caller appends URrows/cycles to global runs; ck serializes only previously appended runs. Therefore retained screens/runs.json has PC straight+UL only; **UR numeric cadence/distance/RAF evidence is absent**. No reviewer fabricated or reconstructed UR values from successful routes.

Own recomputation of retained successes: straight61rows/16cycles, median90world and.333350s; UL74rows/19cycles, median90world and.300000s. See retained-success-metrics.json. These establish only those successful conditions; straight's timing headroom does not prove UR scheduling behavior.

## Static hypotheses — not identified causes

1. Recording/RAF scheduling or movement frameScale/clamping may change measured wall-clock cadence under load. Prior UP06 reference recording failures and straight.33335s make measurement-load investigation reasonable, not proof of UR cause.
2. Field cycle metric uses straight-line endpoint distance; any collision sliding/path bend during a cycle makes chord shorter than travelled arc. Heading changes can reset sprite distance phase. Actual UR route state/heading/collision samples are missing, so neither occurred nor is ruled out.
3. Finite route/sample alignment and first/last partial cycles can affect sample count/medians. Strict source order passing does not independently guarantee enough complete cycles or expected wall-clock duration.
4. A product-specific production integration regression remains possible. No direct physics/timing engine edit appears in the static diff, but actual production FAIL cannot be dismissed solely for that reason.

No hypothesis is selected as root cause. Do not broaden tolerance or force victory/position/stage to obtain PASS.

## Independent static protection and registration

Own readonly hashes at fixed head: all1833 baseline PNG blobs unchanged, canonical259 formal SHA match, new production PNG byte-identical to fixed PR153c15a715 candidate, SHA1bde96684c85739e821e8c7e5e8f07831b8819414569d07d6a3bbb3613e80dfd. Production frame metadata's pre-existing entries are all unchanged; exactly one new distinct aidan_walk_up_pushoff entry added. Real up bank is[new,03,04,01,06], stride90, bobup.25; down bank unchanged. Old up02 path remains original. No QA02 DOMalias, init_script, DEV controls, source-candidate import or shared physics/SAVE/scenario/CSS change. Index diff is only Aidan metadata cache key. Clean fixed worktree at inspection. See stop-protection.json and stop-metadata.json.

Node17 PASS before browser is root evidence; reviewer did not rerun regression tests after STOP. Reviewer used readonly Node VM evaluation only to compare metadata objects; it is not a browser/test retry or independent full-regression PASS.

## Recommended next evidence, only after director authorizes resumption

Preserve this failed source/log/video/results first. For a future approved diagnostic, record raw rows/cycles and separate count/distance/time metrics **before** any assertion, with fail-safe flushing. Include retained currentSrc/loading, heading, coordinates, RAF gaps, instantaneous displacement and cumulative arc distance; compare identical ordinary route/capture conditions against baseline main. Keep original acceptance criteria until evidence justifies any specification decision. Do not execute this plan under current STOP.

Current PC UR post-failure bob/cleanup, normal DEV/reload/SAVE/CONTINUE portions, portrait/landscape and remaining intended regressions are NOT_RUN in this aborted production attempt unless separately evidenced. Prior candidate-art adoption and source protection remain valid; end-to-end production QA is not complete. A clearly BLOCKED Draft checkpoint may preserve the artifact, but main/Pages must remain unchanged pending director response and successful independent QA.
