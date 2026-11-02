# DEV-WALK-MOTION-01 / WALK-QA-02

## Scope

Codex implements the common walk inspector; Claude owns integration of #107 and
#112. The inspector changes no PNG, adoption status, dialogue, battle parameters,
or save schema. Physical Android verification is NOT_RUN.

Base: `b85c3db4dbf1324cc248b1c4344e26efa1c1c783` (includes GOBLIN-20F-FIX01).
Implementation/QA head: `5ca4818914a692f392f8832076698e62d5360ac9`.

## Production source and supported states

- Allies: Aidan/Fiona, exact field registries. Six/front and current side banks
  follow the actual registry count; no private DEV frame list. Other allies are
  not advertised as having a walking bank without an implemented registry.
- Enemies: goblin, moss slime, leafy boar, forest bat, exact MONSTER_TYPES art.
  Goblin has idle + four directions; legacy ground enemies expose horizontal
  common/mirrored banks and explicitly identify dedicated direction art as absent.
  Forest bat is an idle/flight loop, not a claimed walking bank.
- NPCs: 25 manifest rules, including royal soldier and village residents, from
  FieldWalkers.describe(). Idle and shared left/right patrol are available;
  dedicated up/down are unavailable, show 未実装 and clear the previous preview.
- Frame selection, cadence, bob/air lift and walker FPS are shared with production.
  Aidan stride is read from MossForest.walkStride: Claude's #112 integration must
  expose the actual runtime side stride via this adapter, preserving query override.
  No preview-only stride is maintained. Current base uses 90; prior #112 comparison
  of 50/72/90 recommended 72, and that PR's production code already uses 72.

## Operation

Start/CONTINUE the game, finish current dialogue, open DEV → 歩行モーションテスト.
Select 味方 / 敵 / NPC, character, 待機 or direction. Loop, pause, previous/next frame,
0.5/1/2 speed, frame counter, background checker/dark/white/green and foot/center
lines are available. 操作パネル folds controls for mobile landscape inspection.
Read the source-path/status text: common mirrored images are not dedicated art.
One-frame static poses cannot start a useless playback timer.

The modal freezes field and NPC updates, cancels held movement, and blocks game
keyboard propagation. Close, LOAD invalidation, battle, portrait/cinematic takeover
and page exit cancel playback and pending image completions. Hidden/reduced-motion
pause loops; manual stepping remains available. No game state or localStorage write.

## QA (final results appended after collection)

- Node direct original suite: 17/17 PASS, including 8 walk policy tests.
- Formal portrait hashes: 259/259 unchanged. No img/assets diff vs base.
- Registry generator: `python tools/assets/build_registry.py --check` PASS.
- Expanded actual-UI matrix: PASS, 395 frame slots per viewport / 1,185 total; all three viewports. Console, pageerror, HTTP errors and failed requests: zero.
- Required regression rerun: 11/11 PASS (SAVE/CONTINUE, m31, m9, goblin actual pixels/contact battle, town maps, Rilde, DEV arena, portrait DEV, battle motion, asset registry, goblin assets). Independent exact-head browser QA: pending.

The final regression batch recorded 10 PASS and an asset-freshness failure because
the archive omitted `--git-history`. The unchanged original asset test passed
when rerun with committed history. Both raw results are retained; the first batch
is not represented as an unconditional 11/11 PASS. No fixture/assertion was relaxed.

Historical failed attempts are retained in evidence: initial reduced-motion async
fixture wait, then stale queued native-dialog close closing a newly reopened dialog.
The latter was fixed with an `open` guard. Tester1's asset freshness failure concerned
old squash delivery dates; subsequent upstream FIX01 ledger regeneration superseded
that temporary date pin. Current ledger is byte-identical to the latest base.

## PR integration boundaries

Historical independent #107/#112 reviews are scoped to their recorded old SHAs.
Newer heads require fresh review; neither an old PASS nor this tester's QA proves
those PRs merged. See [coordination handoff](../handoff/WALK_QA_02_CODEX.md).
Do not merge #109 or #111 separately. Exact tested head, CI, conflicts and remote
rollback-ref readback must be checked before any normal authorized main merge.

## Director Android checklist (NOT_RUN)

1. Open tester after NEW GAME and after CONTINUE; verify labels/buttons in portrait
   and landscape, folding controls while keeping the sprite visible.
2. Select Aidan/Fiona, goblin/boar and soldier/village resident. Check idle and every
   available direction, missing up/down warnings, left/right mirroring and no stale image.
3. Pause, step forward/back through wrap, compare 0.5/1/2 loops and feet/contact lines.
   Inspect all PNG edges on checker/white/dark/green for transparency fragments.
4. Specifically inspect the latest FIX01 goblin up/down silhouettes and direction.
   This is browser evidence only until the director performs physical-device QA.
5. Close while looping, rotate, reopen, SAVE/CONTINUE and confirm normal field input.
   With reduced-motion enabled, automatic loops must stay disabled; stepping must work.
6. After Claude integrates #107/#112, confirm soldier six-frame cycle and Aidan side
   cycle at the actual production cadence. Formal visual adoption remains the director's.
