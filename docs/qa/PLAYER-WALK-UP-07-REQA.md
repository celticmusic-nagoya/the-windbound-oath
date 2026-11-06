# PLAYER-WALK-UP-07-REQA

Status: **BLOCKED — first real failure preserved; no retry, merge or deployment.**

## Fixed inputs

- Implementation: PR #155, `0494f6452548ea476b4cebbc69d9f41d878d540d`.
- Measurement: PR #156, `442ab3b75141376fd83e37541504d896ba02638e`.
- Five frames: new → 03 → 04 → 01 → 06; 90 world; bob 25%.
- Initial PC/UR failure remains CASE D (cause undetermined). Original failure and diagnostic 24-run history remain unchanged under their existing evidence directories.
- No production, asset, original test predicate, or tolerance changes are authorized. No merge or deployment is authorized.

## Execution contract

`tools/qa/up07_reqa.py` runs the 17 original Node files and seven original browser/static regressions serially. The first real failure stops the suite; remaining tests are NOT_RUN. A logging-only AST shim saves original predicate values and selected caller context before assertions. Legacy collecting checks stop at the first false result. The shim verifies that removing its inserted logging/stop guards reproduces the original AST exactly. Passing timed checks perform no extra browser evaluation. Read-only live capture is attempted on failure before the Playwright context exits; capture errors remain explicit.

Every test has start/end clocks, elapsed time, source SHA, expected/actual result and a log. Sampled movement checks include retained coordinates and RAF intervals; nonmovement checks explicitly mark those fields as not applicable. Existing PR #156 per-route metrics remain the primary cadence measurement.

Synthetic preflight: seven logging contract tests PASS; all seven original script ASTs instrument successfully. These negative controls are not product failures or substitutes for actual execution.

Actual results are below. Android physical QA is NOT_RUN.

Pre-execution independent review found a failure-snapshot iterator error and first-failure overwrite risk in the new logging shim. Both were corrected before any real REQA execution; the added live-page negative control verifies snapshot persistence and retention of the first failure. Production code and test predicates were unaffected.

The preflight review also added same-line callsite disambiguation (all original candidates retained) and detection of both TAP and Node v24 summary skip/fail formats. Retained caller traces are labelled as reference context, not asserted to describe each current static predicate.

## Independent run result

Runtime head: `c6f4d138cfe5edd93cff341027ca73e25eff5c97`. Original sources and production assets were fixed before execution. A different reviewer executed the suite and independently inspected the persisted failure; the implementation author did not operate a second browser. Preflight logging fixes above occurred before this one real run.

| Scope | Result |
|---|---|
| Original Node files | 17/17 PASS, no skip |
| m67 production checks | 31 PASS / 1 FAIL, process exit 1 |
| PC straight, left-up, right-up | Five decoded frames/order/wrap, original cadence, quarter bob and stop/protection predicates PASS |
| Stock DEV production up bank | Five real sources, cleanup and state-protection checks PASS |
| Ordinary UI SAVE / title CONTINUE | SAVE creation and enabled CONTINUE PASS; exact feet/progress/SAVE conjunction FAIL |
| Remaining PC continued movement | NOT_RUN |
| Smartphone portrait / landscape | NOT_RUN (stopped before either viewport) |
| m62 down ARM-02 / m58 side | NOT_RUN |
| m55 ally/enemy/NPC / separate SAVE lifecycle | NOT_RUN |
| Asset-registry and m49 full regression | NOT_RUN; independent byte/SHA protection pre/post PASS |
| Visual integration acceptance | NOT_COMPLETE; partial PC recording retained, no mobile evidence |
| Android device | NOT_RUN |

### Actual cadence values

| PC direction | Samples | Overlapping cycle windows | Median world/cycle | Median seconds/cycle | Max RAF interval ms |
|---|---:|---:|---:|---:|---:|
| Straight | 70 | 16 | 90.0000 | 0.3000 | 33.4 |
| Left-up | 85 | 19 | 90.0000 | 0.3000 | 16.8 |
| Right-up | 83 | 19 | 90.0000 | 0.3000 | 16.8 |

Original requirements remain: at least four windows, strict absolute world error <12, strict absolute seconds error <0.08. No alternative clock or relaxed limit was used. Full start/end coordinates, UTC/RAF clocks, sample count, key events and expected/actual conjuncts are in the archived route measurements.

### First failure and reproduced procedure

1. At 960×540, NEW GAME, dismiss opening through ordinary keys, perform straight/diagonal movement and stock DEV inspection.
2. Use MENU → SAVE, reload document, select enabled CONTINUE and wait for the original READY conditions.
3. Evaluate the unmodified `pc CONTINUE exact feet/progress/SAVE` predicate at m67 line 84.

Expected: exact pre-SAVE feet, STABLE string and SAVE string equality. Actual feet changed from `(421.3873950262489, 259.6053351839163)` to `(421,260)`; the exact feet check is false. The original `and` short-circuited there. A separate read-only failure snapshot then verified STABLE and the stored SAVE string were both byte-for-byte equal. This separate observation does not convert the original FAIL to PASS.

The saved internal coordinates are `(404,218)`; the existing foot offset `(17,42)` produces exactly the observed restored `(421,260)`. `js/field/moss-forest-runtime.js:719` already rounds internal coordinates, and `js/save-continue.js:72` already accepts up to one world unit per axis when validating the saved position. Both sources are unchanged from main. The persisted evidence therefore identifies an exact-floating-feet expectation incompatible with existing save quantization; it does not establish corruption or an up-walk production regression.

No test predicate, production code or save format was changed; no rerun was attempted. Recommended next action: director decision on a separately scoped QA-contract correction that compares against the existing saved-coordinate representation while still requiring exact STABLE/SAVE preservation. This is a proposal only, not an authorized change or passing result.

### Initial FAIL versus this run

The initial PR #155 right-up cadence failure remains **CASE D**, since its failed UR numbers were not saved. PR #156's 24 diagnostic measurements remain unchanged. This run's right-up cadence passed with complete numerical evidence, but that success cannot establish the initial failure's cause. This new stop is a distinct CONTINUE assertion encountered later than the original stop.

### Evidence and protection

- [Full test plan/result](evidence/player-walk-up-07-reqa/results.json), [serial execution log](evidence/player-walk-up-07-reqa/run.log).
- [Saved/continued values](evidence/player-walk-up-07-reqa/save-continue-comparison.json), [cadence comparison](evidence/player-walk-up-07-reqa/movement-comparison.csv).
- [Lossless execution archive](evidence/player-walk-up-07-reqa/execution.tar.gz), [per-file SHA index](evidence/player-walk-up-07-reqa/run-index.json): all 71 files, including original per-assert outputs, raw measurement arrays, first failure and pre-close browser snapshots, console/request observations, partial native PC video and four PC screenshots. The raw video is unfinalized (486 readable VP8 packets, ffprobe “File ended prematurely”, no duration); its bytes are preserved and it is not complete SAVE/CONTINUE evidence.
- [Independent report](evidence/player-walk-up-07-reqa/independent/REVIEW.md) and preflight/negative-control logs are retained separately from the root report.
- All 259 formal SHA locks PASS before and after. All 1,857 fixed PNG/old-failure evidence files match; old diagnostic history is unchanged; production and pinned PR #156 measurement inputs have zero difference.
- No observed console/Promise/HTTP errors were captured up to the stop; this is not an all-viewports error-free claim.
- A secondary exception checkpoint records propagation of the same assertion, not a second test failure; the first failure remains independently preserved.

**Final recommendation: BLOCKED. Do not merge PR #155 or publish Pages.** Remaining regressions, mobile rendering and overall integration acceptance are unverified. No main/Pages changes were made.
