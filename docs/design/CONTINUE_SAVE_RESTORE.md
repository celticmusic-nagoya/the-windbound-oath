# SAVE-LOAD-CONTINUE design (Issue #21) — investigation + design, no implementation yet

Base: fix/startup-opening-no-clobber (a2217208…, on Scene lifecycle cc3aad4c…). Date 2026-10-19.

## Findings (reproduced: tests/pending/m36_continue_cold_restore.py, 10 FAIL on this base)
1. Save (`saveGrowthData`, version 30; `prologue` version 2) already records the new-village state: `prologue.moss = {map:'rilde_village_01_peace'|'rilde_in_aidan', x, y, opened, fired}` plus `storyStage`, and `position.px/py` of the *legacy* DOM village.
2. Load (`PrologueProgress.load`, js/prologue-progress.js) routes by stage: stage 9–12 -> `MossForestStory.fromSave`; stage <=8 -> legacy DOM village branch (`px/py`, `room='home'`, `#inside`); 13/14/15 -> aftermath/fort/end. The Rilde maps are not in `MossForestStory.MAP_IDS` (forest maps only), so `fromSave` treats them as invalid.
3. Result of a cold start + `loadGrowthData()` for a save made in the new village (stages 0, 1, 3): MossForest inactive (map=null), the legacy DOM village/house shown, saved map/position ignored. Stage 0 saves show the legacy house.
4. `?title=0`/DEV: `devJump` puts the game in "sandbox" where normal save is blocked (protection), so natural play is needed to create saves for tests.
5. TITLE-01 `canContinue()` is hard false; `begin(cb)` cb = `RildeVillage.startOpening` (NEW GAME path).
6. The save write path itself is fine (no data loss). `loadGrowthData` leaves the save byte-identical on load (asserted in m36).

## Design (non-destructive; no SAVE format change)
- Add a Rilde-aware branch for stage <=8: when `RildeVillage.enabled()` (not `?legacyVillage=1`) and `data.moss.map` is one of the Rilde map ids with finite x/y, restore through the same restoration-token path used for forest saves (kind 'forest'): `MossForest.enter({map, x, y})` with request-generation checks (cc3aad4), and `verify` = map id + feet within 2 px + `!busy`. Whitelist the Rilde ids from the village module, not from user data.
- Saves without `moss` (version-1 era, legacy village) or an invalid/unknown map: fall back to a stage-based new-village spawn (stage 0 -> `rilde_in_aidan/from_bed`, 1 -> `from_training`, 3 -> `from_sunset`, 5..8 stay legacy attack scenes) — read-only, never rewriting the save.
- Never mutate `localStorage` during load; on any failure keep the existing safe-stop behaviour (`failRestore`).
- CONTINUE (TITLE-01): enable only when `localStorage[SAVE_KEY]` parses AND a dry-run validator (`PrologueProgress.canRestore(data)`) says the route is supported; then `begin` is skipped and `loadGrowthData()` runs after boot; startup opening must not run (use the #20 no-clobber guard and cancel `startOpening` by request generation). If unsupported -> button stays disabled.
- Ordering vs the opening: CONTINUE must call load as the first scene request; the opening is never started on that path.

## Tests to add before implementation
- m36 (this branch, pending): cold-start restore for stages 0/1/3 + house; byte-identical save; no page errors.
- To add: forest stage 9–12 cold restore regression, stage 13–15 (cc3aad4), pv1 migration fixtures, corrupted/unknown map fallback, TITLE-01 CONTINUE enabled/disabled matrix, battle-time save refusal.

## Risks / open
- Interaction with Issue #12 (Scene lifecycle integration gate) and cc3aad4 not yet merged to main: this must follow it. P2 portraits not in this base.
- Stage 5–8 (village attack) saves still restore into the legacy DOM scenes; out of scope until the new village hosts them.
- Android/real-device untested.
