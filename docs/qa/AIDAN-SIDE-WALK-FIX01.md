# AIDAN-SIDE-WALK-FIX01

Base main: `12b1dca9433f6c2f2b69c2a63c097ad95fdc5e2b`. User authorizes targeted toe repair, QA, PR and conditional normal merge. Physical Android final review remains pending.

## Cause and narrow repair

Four baked alpha cuts: left02/04/05, right01. The other eight frames show no corresponding cut. The adopted six-frame conversion preserved the four-frame predecessor alpha; complete toe pixels exist in the delivered sideL/sideR sheets. Internal cut planes are well inside the 2048×1280 canvas, so stage clipping and the foot anchor are not the cause. The exact historical extraction command is not available; source registration was fitted to intact pixels rather than claimed as recovered history.

`tools/art/restore_aidan_side_toes.py` deterministically extracts only the missing toe regions from those source sheets. Left04/05 recovered pixels retain the adopted far-leg shading rule. It adds 10,165 formerly transparent pixels across four separate versioned PNGs. Every formerly visible RGBA pixel, all pixels outside the four boot regions, original canvas, anchor `[1024,1230]`, scale `.0625` and sole baseline remain unchanged. No new artwork or body redraw; all twelve original side6 PNGs remain byte-identical. The asset registry explicitly records these sparse replacements rather than a new three-frame animation.

Only four asset paths/bounds and the asset-script cache key change. Rendering, movement, SAVE format, story and combat code are unchanged. The new files remain `PROVISIONAL_ANDROID_QA`; approval of formal stride180 is NOT implied. Runtime default72 remains unchanged; DEV comparison180 at1x only.

[Before/after boots](evidence/aidan-side-walk-fix01/toe-comparison.png). Exact source/final SHA, registration, recovery regions and twelve original SHA are in [manifest](../../img/field/characters/aidan/side6/fix01/manifest.json).

## Verification

Static/pixel checks: 74 PASS, including all twelve geometry/alpha inspections, original SHA protection, source/final SHA, no changes to existing visible pixels, no remaining internal vertical toe cut, no new disconnected fragments and unchanged baseline. Formal259 SHA PASS. Node17 PASS. Independent static/pixel review PASS at `85e6e1be7e1adcd02525a549ed90d7987bfca572`.

Browser suite: 7/7 PASS at source head85e6e1b (serial isolated committed snapshot with history). m57:103 real-image/screen-pixel/loop/cleanup assertions; m55:1,197 frame slots; m56:215 stride/rate/UI assertions; SAVE/CONTINUE:25 core assertions; m31 and asset registry audit PASS. No console, unhandled Promise or unexpected HTTP failure in the focused test. Final exact-head independent gate is recorded in the PR review before merge. No uncollected result is counted as PASS. Initial runner attempt could not bind its owned local server in the restricted sandbox (all seven exit125); preserved outside the repository as `qa/`. Retried with authorized loopback network capability as `qa-retry1/`; no test assertions were relaxed.

## Android final checks

Open `?dev=1`, NEW GAME or CONTINUE, DEV → 歩行モーションテスト → エイダン. Choose 横歩き周期180 and speed1x; inspect left/right frames1–6, looping, pause/restart and direction changes in portrait/landscape. Confirm no toe cuts and natural contact. Default formal72 is deliberately unchanged.

Evidence: [runner results](evidence/aidan-side-walk-fix01/results.md), individual logs alongside it; [actual loop transitions](evidence/aidan-side-walk-fix01/toe-loops.json), [screen-pixel assertions](evidence/aidan-side-walk-fix01/toe-results.json), Node17 and protection summaries. The static-test server readiness probe closes its HTTP body early and can cause a server-side BrokenPipe; it is not a game request. No failed test expectation was hidden.
