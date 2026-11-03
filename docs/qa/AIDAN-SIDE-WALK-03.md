# AIDAN-SIDE-WALK-03

Base main `5523023306de776f0ce558e5486f4f4c675083f5`. User explicitly adopts the Android-tested Aidan horizontal cadence180 at1x for production, and authorizes implementation/QA/PR/conditional normal merge.

## Minimal implementation

`moss-forest-runtime.js`: default AIDAN_SIDE_STRIDE72 →180 for left/right only. Up/down and Fiona remain90. Existing DEV URL comparison range20..200 is preserved; absent an override, the existing shared descriptor now supplies180 to both production and DEV. No new animation or timing logic. `index.html` updates only its runtime-script cache tag. DEV40..300/presets72/120/180/240 and speed.5/1/2 stay intact. Production movement speed, frame banks, foot anchor, PNG bytes, SAVE, combat and scenario are unchanged.

Historical reports such as DEV-WALK-MOTION-02 and AIDAN-SIDE-WALK-FIX01 correctly retain their earlier72 policy. This new user decision supersedes only that cadence; it does not promote provisional art or alter any asset approval.

## Production measurement

m58 starts actual NEW GAME, closes opening narration with Enter, then walks the real house aisle using Arrow keys. No DEV jump/teleport, game-state writes, patched speed, flags or SAVE fixtures. Test-owned RAF only observes feet and visible decoded production PNGs. Left/right each show all six frames in sequential loops. Across PC1920×1080, portrait390×844, landscape844×390, median full cycle is180world /0.600s (base300world/s); horizontal foot Y drift0. Stop clears bob and settles feet; ordinary restart/direction changes retain correct behavior. DEV actual image transitions at inherited180/1x agree with field periods. Progress/flags/inventory/party/gold/localStorage unchanged by the walking exercise. Screenshots and raw actual-frame/feet samples are alongside [cadence summary](evidence/aidan-side-walk-03/cadence.json).

First m58 invocation expected unrelated house ID `rilde_in_house_01`, whereas normal NEW GAME enters `rilde_in_aidan`; this fixture failed before movement assertions. The corrected expected ID and ordinary clear-aisle route follow actual map/source. Failure evidence retained; no product behavior or assertions were weakened to bypass a regression.

## QA

Serial browser suite7/7 PASS at c541efa: m58 production/DEV62 assertions; m56 stride UI215 assertions; m57 toe real-screen103 assertions; static toe74 assertions; SAVE/cold CONTINUE25 assertions; heading and asset registry audit PASS. Node17 PASS; formal259SHA PASS. No PNG, geometry, adoption status or asset-reference changes. Current asset registry cadence notes updated to180; historical reports and repair provenance manifest remain unchanged. Final independent exact-head verdict is recorded in the PR before normal merge. Browser emulation is separate from physical Android (NOT_RUN in this task).

[Runner results](evidence/aidan-side-walk-03/results.md); individual raw logs, screenshots, production frame telemetry, Node output and259SHA summary are in the same evidence directory. The initial failed fixture is retained separately.

## Physical Android confirmation

Open the normal Pages URL without an old `aidanSideStride` query override, reload and NEW GAME or CONTINUE. Walk left/right in the house/village; pause, resume, turn up/down. No DEV setting is needed for180. Optional DEV → 歩行モーションテスト → エイダン → left/right should initialize180 /1x;40..300 adjustments remain temporary.
