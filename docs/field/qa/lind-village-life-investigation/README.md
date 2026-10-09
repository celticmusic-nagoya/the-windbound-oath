# STEP B — investigation checkpoint, implementation stopped

Date: 2026-10-09. Start/main: `ac3707698018aa9efe016e04776ba3d1d1be833e`.
Branch: `work/lind-visual-polish-village-life`.

**STEP B is NOT PLAYER QA READY.** No application code or PNG was changed.
This is an investigation/evidence checkpoint, not a completed village-life feature.
Main and GitHub Pages remain the approved Terrain STEP A version.

## Stop condition

The user's section 28 requires stopping if the current NPC asset cannot naturally
fix the fisherman. The sole fisherman character export is
`img/field/lind/npc/villagers/fisherman_idle.png`. Visual inspection of both the
PNG and actual field confirmed an upright rod, with a caught fish hanging from
it, integrated into the character art. It is already right-facing in the PNG.
Mirroring or relocating the whole image cannot turn that pose into quiet fishing
with the rod extended over the water. Tilting the entire actor would tilt his
feet/body too; overlaying the separate prop would leave the existing upright rod
and fish and create an incoherent duplicate rod. No such workaround was applied.

The separate `img/field/lind/river/lind_fishing_rod.png` is a placement prop,
not an alternate character pose. No other fisherman pose exists in the checked-out
latest main. A standalone transparent, right-facing **idle-fishing** character PNG
is needed, retaining the existing fisherman design, with one rod extended toward
the right/water and line descending to the water, without a permanently caught
fish. Use a stable ground anchor. Extra frames and a new character design are not
required. No PNG editing or generation was undertaken.

## Source audit

- `lind-npcs.js`: 12 villagers, plus Emma registered by `lind-emma.js`; one
  centralized NPC RAF. Only the male farmer has an additional walk PNG and a
  24px horizontal patrol. Other villagers/children/Emma currently remain idle.
- Positions use `x` and `footY`; rendering uses alpha content bounds. Existing
  actor foot is 18×8. Moving only x currently updates neither foot y, hit-target y,
  nor depth, so a future two-dimensional ambient update must update those together.
- `lind-review.js` compiles static geometry and mixes animal/NPC predicates into
  `blockedWorld`. Story review coordinates are deliberately not saved. Interaction
  cancels destination; close restores the prior scene position.
- `field-navigation.js` already has a bounded grid planner. Destination validation,
  planning, movement, and blocked handling use the same mixed predicate. Its early
  `blocked(x,y)` / `blocked(target.x,target.y)` branch calls `finish`, clearing the
  destination immediately, before retry/replan logic can run.
- `lind-animals.js`: existing slow pen motion on a separate RAF; no NPC pushing or
  player-position writes. Its live foot can move over the player's foot.
- Keyboard input already cancels target and navigation immediately. The native
  footprint/speed/river/static geometry/camera/Terrain require no change to address
  the dynamic obstacle root cause.
- Fisherman: x1447, footY1367, height46, direction1. River x1450–1630;
  fishing-deck walkable polygon is the existing four points recorded in the JSON.
  Current actor is near the west/base of the dock, not its east tip. Dock image,
  decorative rod, river clearance and depth must be reviewed together after the
  fishing pose is available; static river/deck geometry must remain locked.
- Boy/girl standalone idle PNGs exist; no walk/run exports exist. Only two children
  would be reused, without adding a third NPC or generating new sprites. Grounded
  movement quality must be reviewed before claiming a chase PASS.
- Environment wind controls affect foliage/birds independently of water and
  livestock. Ambient human behavior must likewise remain independent of wind.
- Actual camera default is **1.00x**, with session review choices through 2.10x;
  instruction section 18 calls 1.80x provisional. This discrepancy is recorded,
  and no camera setting was changed.

## Dynamic livestock reproduction

`pig-before.json` records 9 controlled fixtures: mouse, tap and keyboard, three
attempts each, at mobile-landscape 844×390 and camera2.10x. Mouse/tap select a
destination; the existing moving pig is then advanced into the native player foot.
The next normal RAF navigation step reports `outcome: blocked`, `target: null`,
`staticBlocked: false`, `animalBlocked: true`. This reproduces the reported root
cause. Moving the pig away and issuing the destination again reaches it. Keyboard
cases are manual-input observations, not automatic-resumption tests. This fixture
is controlled QA and does not describe the frequency during normal play.

The reproduction and visual audit observed image404=0, JS exceptions=0,
console errors=0. These counts apply **only to the investigation runs**, not the
unexecuted full STEP B regression suite.

## Safe implementation direction, not executed

Separate static routing/destination validity from live dynamic contacts only in
the active Lind DEV review. Retain the existing planner and movement sweep; keep
the destination during temporary actor blockage and retry when clear. Preserve
keyboard cancel and static blocked-destination behavior. Do not change geometry,
speed or implement a second pathfinding engine.

After that foundation is tested, use a single centralized NPC update with authored
plaza waypoints derived from actual Wind Stone/static geometry, staggered child
chase/pause/role-swap states, player-yield behavior, small per-profession routines,
and minimal Emma movement. Do not add timers per NPC or couple them to wind.

## Outcome

- Investigation: completed; evidence saved.
- Dynamic navigation / children / fisherman / villager-life / Emma implementation:
  **not performed**, following section 28 stop condition.
- Full 30-minute simulation, four-viewport/four-camera feature QA, dynamic
  resumption tests and Battle regression: **not run for STEP B**.
- Runtime sources, existing PNGs, Terrain, static collision, Aidan, camera and
  Battle: unchanged. No claim of feature PASS or public STEP B availability.
- Resume prerequisite: appropriate idle-fishing pose or explicit revised direction
  allowing preparation of that asset. Do not merge this investigation-only branch
  as a completed STEP B implementation.

## Reproduction

Playwright/Chromium are provided by the cloud environment. Start a static server
on 127.0.0.1:8015 at the repository root. The scripts write QA output outside the
repository under `/workspace/onboarding/lind-village-life-investigation/`.

```sh
mkdir -p /workspace/onboarding/lind-village-life-investigation
NODE_PATH=/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules \
LIND_QA_URL=http://127.0.0.1:8015 \
node docs/field/qa/lind-village-life-investigation/pig-before.cjs
NODE_PATH=/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules \
node docs/field/qa/lind-village-life-investigation/visual-audit.cjs
```
