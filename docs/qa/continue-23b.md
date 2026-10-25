# Issue #21 SAVE-LOAD-CONTINUE — DIRECTIVE-23A/23B

Base/main before integration: `147e952b3b0233a2fdb104172c3c426908d586a6`.
Branch reused: `investigate/issue21-continue-22d`.
Design recorded before implementation: `docs/design/CONTINUE_IMPLEMENTATION_23A.md`.
References reused: existing CONTINUE design `d02045be37ad396baf9cfbb4e97f081e2f296eb6`, TITLE-01 menu/NEW GAME confirmation pattern `7b724c10408ca70b6d144c2e0c443d8c41c5e6e7`. Unmerged title artwork/whole historical branch is not imported. The integrated title is text/CSS-capable with NEW GAME and CONTINUE; no new lore/art assumptions.

## Restore and ownership

Title selection is the cold-start boundary; no initial NEW GAME map/narration is launched when CONTINUE is chosen. Read-only inspection checks supported root/progress versions, party/formation, item counts, event arrays, map identities and optional facing. Malformed/incomplete/unsupported data return a title error with original bytes untouched. Duplicate/pending/late CONTINUE starts are refused.

CONTINUE reuses the actual LOAD application function, TrainingCheckpoint and PrologueProgress routes, not a second map/save engine. Common Loading/Input blocks background interaction. Coordinator invalidation rolls back the provisional cold-restore model synchronously before a newer NEW GAME/DEV/unload owner proceeds. Failures restore the pre-CONTINUE model and return to title; a failed normal LOAD also restores legacy acquisition flags and their provenance. No automatic save/delete occurs on read or migration.

Current stage0/1/3 village records keep map and coordinates; stage2 uses the existing validated retry-to-stage1 policy; real v1 stage2 stays refused. Legacy early records without new-map coordinates use documented bed/training/sunset checkpoints rather than guessed coordinate conversion. Stage4/8 resume the existing atomic return/escape scene from its beginning; stage5–7 reconstruct existing attack visuals without invoking the entry function that resets saved flags or grants rewards. Forest/free-roam routes reuse existing restoration. Known saved coordinates are verified after restore. Optional new `moss.facing` saves direction/flip; absence retains existing default/spawn behavior and is not claimed to recover an unknown historical facing. Transient dialogue page position was never saved; restored history/cycles/fired/opened prevent automatic replay of committed events.

## Acquisition profile and old SAVE policy

Root version remains 30, progress version remains 2. Added optional field:

```json
"legacyEvents": {
  "v": 1,
  "drawer": false,
  "pot": false,
  "balloon": false,
  "balloonDone": false,
  "cat": false,
  "catFound": false,
  "catDone": false,
  "unknown": []
}
```

- New explicit false/true is restored exactly before events become operable.
- Entire profile absent: only drawer/pot are unavailable under the user-approved old-save compatibility restriction. This is **not proof of prior collection**. Unknown provenance is retained in `unknown` if the player explicitly saves later.
- A player who had not collected an old drawer/pot may lose access to it. No item, money or historical collection record is fabricated; old raw SAVE bytes are never auto-rewritten.
- A present but partial/invalid profile is safely refused. New game clears the flags/provenance to genuinely unclaimed state.
- Other event mechanisms were audited: forest/map treasure uses existing Inventory.claimed plus opened/fired; quest rewards use Quest serialization. Legacy balloon/cat state is now exact in new profiles; old subquest completion and the recorded cat-report objective are the only positive evidence used for their recovery. Ordinary conversation and required story events are not disabled by the unknown-item rule.
- Current drawer/pot hooks set a flag and display the acquisition text. Tests prove event replay prevention; this change does not invent or rebalance their physical reward implementation.

## Failure diagnosis kept separate

23A's additional actual-SAVE/cold-CONTINUE test FAILED: consumed drawer emitted the unconsumed-event text. The cause was missing serialization of the separate global legacy flags, not a fixture stub. Original FAIL, stop report and pre-change backups are retained under independent `/tmp/directive23-qa` and `/tmp/directive23b-qa` evidence directories. The unchanged failing expectation passes after the additive profile fix.

## Executed final alternative QA (2026-10-25)

| Command | Result |
|---|---|
| Original real SAVE acquisition regression, isolated | PASS 1/1 |
| `node tests/continue_restore.test.cjs` | PASS 37 cases |
| `node tests/title_continue.test.cjs` | PASS 7 cases |
| `node tests/startup_race.test.cjs` | PASS 20 cases |
| `node tests/s2_transition_recovery.test.cjs` | PASS 19 cases |
| `node tests/common_loading.test.cjs` | PASS 17 cases |
| `node tests/loading_input.test.cjs` | PASS 37 cases |
| `node tests/loading_map_readiness.test.cjs` | PASS 3 cases |
| `node tests/issue51_command_lock.test.cjs` | PASS 14 cases |
| `node tests/issue54_coordinator.test.cjs` | PASS |
| `python tests/battle/battle_opening.py --self-test` | PASS assets/classifier only |
| Changed/new JS, all inline syntax; git diff --check | PASS |

Actual Party/Inventory/Equipment/Quest/FieldTalk/PrologueProgress/TrainingCheckpoint/LOAD/CONTINUE/title code is exercised with DOM/network/renderer adapters. Actual syncStoryEquipment is used in CONTINUE tests. Assertions are unchanged for the original 19 cases and the original failed one-time-event case. Cases cover explicit true/false for both acquisitions, actual event→SAVE→cold restore, old unknown suppression, unchanged bytes and legitimate inventory/progression, malformed profiles, new-game reset, failure rollback, provenance preservation, known quests, stages0–8, legacy/new village/forest, facing, reordered replies, duplicate/late clicks, NEW GAME supersession, invalid inputs, visible title error/retry and keyboard focus/Tab.

## NOT_RUN and residual limits

- Real browser regression/desktop/portrait/landscape: **NOT_RUN / ENV_BLOCKED**, current localhost socket preflight PermissionError (Operation not permitted).
- Android physical device: **NOT_RUN / ENV_BLOCKED**, no attached device.
- Native touch/key synthesis, visual layout, real goto/reload/bfcache, performance, memory/LRU and long animation soak remain unverified. Simulated navigation/DOM evidence is not browser PASS.
- Historical TITLE-01 art/OPTIONS/GALLERY and its full old browser QA are not certified or merged by this implementation. Existing in-game settings remain available after game entry.
- Old unknown acquisition restrictions and checkpoint/page/facing limitations above are explicit compatibility limits, not silently inferred history.

All executable mandatory alternative QA passed; target acquisition replay is resolved, no new P0/P1 or unintended conflict found in this scope. Automatic integration is authorized by DIRECTIVE-23B after latest main/head/merge checks.
