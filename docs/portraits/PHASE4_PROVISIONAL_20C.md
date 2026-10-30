# DIRECTIVE-20D — Android QA provisional integration

User authorization: 2026-10-30. Status: **PROVISIONAL_ANDROID_QA**, not formal adoption. Historical19A audit and19B normal adoption records remain unchanged. This record supersedes their then-current “other expressions unapproved / blink not implemented” state only for the43 exact revised20C assets listed in [the ledger](PHASE4_PROVISIONAL_20C.json).

Source: private handoff repository, branch `handoff/phase4-20c-claude-20261030`, commit `b8517c2cf74445362ce1a557cf7c4ecd280d94fe`, `reports/PHASE4-20C-20261030/`. Reviewed HANDOFF, SHA256SUMS, boxes/specs, exprgen/blinkgen scripts, expression comparisons and20A/20Cblink comparison sheets. Import copies bytes, never runs generation or modifies adopted PNGs. Revised assets live in each character's `provisional-20c/` subfolder; no old source overwrites.

- Fiona: formally adopted normal +7 provisional expressions.
- Lou: formally adopted normal +5 provisional expressions; **smile/relieved excluded**.
- Emma: formally adopted normal +7 provisional expressions.
- Normal blink only:24 provisional overlays, existing3–6s/260ms shared controller and reduced-motion behavior. All other expressions are still images.
- Existing production conversation metadata/text/progression unchanged; normal blink automatically uses the existing19B integration.

## Android test route

Open the published game, finish/close the current dialogue → DEV → **立ち絵・モーションテスト**. Select Fiona/Lou/Emma, expressions marked **QA候補**, normal → manual/auto/loop/frame0–4. Switch left/right and rotate. Landscape controls can be folded. Normal base remains formally adopted; its blink status is marked QA候補. Other expressions display 未実装・静止画 for blink.

Production routes: Fiona training→cliff summit bench→advance introductory narration once; Emma peaceful Rilde first conversation; Lou win Raider→continue result→advance aftermath six pages. These normal conversations now blink without dialogue changes.

## Residual quality concerns — user Android judgment pending

- Fiona: expression crispness and angry/determined distinction.
- Lou: subtle expression strength, right closed eyelid slightly beige, tiny upper-lid specks.
- Emma: smile/relieved use flat closed lids rather than smiling arcs; eyelid folds and tiny upper-lid specks.

These approved QA concerns are not silently promoted to formal acceptance. Gross rendering misalignment/corruption remains a failure. Physical Android QA: **NOT_RUN**, user pending.
