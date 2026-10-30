# DIRECTIVE-20D — provisional Android QA integration

Baseline main: `642e70184dfad8f1aa2bcd8dd4a4ce46b85c6440`. Runtime implementation: `cab3827`; final test optimization: `787267ca812f7921c5757607e623cb15120923b2`. Later evidence-only commits do not change the runtime/tested assets. PR: [#90](https://github.com/celticmusic-nagoya/the-windbound-oath/pull/90).

## Automated/browser result: PASS

-11 browser regression files PASS,0 printed failures;6 Node controller/registry tests PASS. [Exact test heads/results](evidence/directive-20d/results.json). Baseline main m46 also PASS before changes.
- m47: all19 provisional expressions visibly distinct; same dimensions/alpha and exact same screen geometry as normal. Fiona8/Lou6/Emma8 selectable faces; Lou smile/relieved excluded. Non-normal blink disabled/still. Manual/auto/continuous/individual frames0–4 change BOTH eye canvas pixels. Left/right and6 viewports tested; reduced-motion respected. DEV exit clears timers and preserves scenario/save state.
- m46: real Emma NPC, Fiona bench and Lou post-Raider dialogue routes. Each normal completed THREE natural3–6s blink cycles. Every sampled full canvas exactly matched independent source-image/overlay compositing; both eye ROIs changed. Dialogue end/cancel/LOAD/scene hide/CG takeover clear portraits/timers. Existing story outcomes/text/order unchanged.
- m40–m45: shared renderer/lifecycle/blink/preview/DEV and Aidan production regressions. m7cliff/m6talk/save_continue_lifecycle: existing story/save checks.
-43 revised20C PNG hashes exact; adopted normal3/Aidan54/eventCG10 unchanged. Asset-registry build/check/audit:0errors. Historical19A/19B adoption records retained.

The first DEV run exposed a test selector ambiguity and was corrected; no runtime rendering defect was hidden. An initial suite command named a nonexistent m43 test; the correct test and remaining cases completed successfully. Neither interruption is counted as a passing run.

## Actual canvas eye evidence

Each strip shows states0,1,2,3,4 from the displayed production canvas, enlarged3× for inspection (original asset PNGs were not modified):

| Character | Left eye | Right eye |
|---|---|---|
| Fiona | [actual frames](evidence/directive-20d/20d_fiona_L_actual_strip.png) | [actual frames](evidence/directive-20d/20d_fiona_R_actual_strip.png) |
| Lou | [actual frames](evidence/directive-20d/20d_lou_L_actual_strip.png) | [actual frames](evidence/directive-20d/20d_lou_R_actual_strip.png) |
| Emma | [actual frames](evidence/directive-20d/20d_emma_L_actual_strip.png) | [actual frames](evidence/directive-20d/20d_emma_R_actual_strip.png) |

## Adoption and Android

All43 imported runtime PNGs remain **PROVISIONAL_ANDROID_QA**, never formally adopted. See [ledger](../portraits/PHASE4_PROVISIONAL_20C.json) and [routes/known quality concerns](../portraits/PHASE4_PROVISIONAL_20C.md). Fiona crispness/angry-determined distinction, Lou subtle expressions/right-lid tint/specks, Emma flat closed smile/relieved/lid folds/specks remain user Android art judgments.

Physical Android QA: **NOT_RUN / user pending**. Browser viewports390×844,360×800,412×915,844×390,915×412,1920×1080 are emulation, not a physical device verdict. Open DEV→立ち絵・モーションテスト→select character→QA候補 expression, or normal→manual/auto/loop/frames. Existing production routes remain available.
