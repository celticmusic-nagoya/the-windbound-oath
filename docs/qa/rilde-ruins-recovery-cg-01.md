# RILDE-RUINS-RECOVERY-CG-01 — implementation gate

Base: main after PR #167 (squash c51197e263ad85a2cca39735b845362b326d55c9).

## Verified source routes
- `RildeVillage.resolve('rilde_village')` selects `rilde_village_01_ruin` when `storyStage >= 5` or `rilde_ruined`.
- `RildeVillage.onEnter(map)` is called by the `MossForestStory` map hook. This can occur during load/restore and free-roam, not just the initial destruction.
- The prologue's stage 5–8 attack uses the legacy DOM village and its own click/battle overlays.
- The escape is `startEscapeScene()` then `enterMossForest()`; the approved recovery composite is explicitly reference-only in `RildeCG`.

## Next implementation contract
1. Preserve the existing map and battle overlays; do not replace playable map with a full-screen CG.
2. Only show the approved `aftermath/ruins_background_only.png` at a director-approved narrative beat, **not** every time the ruined map is entered or a save is restored.
3. The recovery composite remains reference-only; do not render it as an independent game background or silently promote it.
4. A cue must be idempotent, cancellable on load/reset, non-blocking after dismissal, and must not modify `storyStage`, flags, or SAVE.
5. Add automated trigger, cleanup, old-save, and responsive layering checks before a merge.
6. Android physical-device QA is deferred by director until a cohesive batch of main merges is complete. Record as NOT_RUN, never PASS.

## Current gate
Ruins CG trigger: NOT YET APPROVED/IMPLEMENTED. The map-state change is not a unique narrative beat. The next code step is a separate presentation cue at a verified story beat, not a map-load side effect.
