# Lind Navigation Fix + Aidan A1

START COMMIT: `e9b5c952a1ad11b07f4fd26d7bb63b3ec19c4a62`
START BRANCH: `work/lind-step9-11-prep`
START WORKTREE: CLEAN. Remote branch matched HEAD; main stayed `51cf092...`. No reset/rebase/force push.

## Navigation source audit

Old field movement stopped both axes on the first blocked sample and immediately discarded the destination. The pointer destination subtracted22px while the established foot anchor is42px, placing feet20px beyond the tapped point. DEV bridge collision used a26px deck strip for a10px foot collider, requiring precise entry alignment. Current sprite alpha bounds and bridge visual were inspected before changing the finite strip.

## Implementation

- Preserve pointer5px/frame and keyboard22.5px/input (125%).
- 2px swept microsteps, independent X/Y wall sliding; no collision bypass. Keyboard pure-axis corner assist probes up to12px, shifts at most0.5px/microstep and3px/input. It checks the lateral sweep and forward clearance; no teleport/snap.
- Held arrows/WASD combine into normalized diagonals, retaining native key-repeat behavior. Manual directional input cancels destination/route immediately. Pointer input creates a new destination; targets never resurrect.
- Pointer destination uses the established foot anchor(17,42). Arrival radius3px, finite world bounds, blocked clicked points cancel rather than push an actor/wall. NPC/object buttons and existing Enter/ranges remain separate.
- New generic `FieldNavigation` owns transient routes only. It accepts the caller's live collision predicate; contains no bridge/map-object IDs or stored progression. Direct swept segment first, lazy bounded A* only when needed:16px grid,8px retry for narrow passages; max12000 expanded nodes per attempt. Every route edge and movement microstep is checked against the same collider. Exact positions connect to grid vertices by walking, never snapping.
- Moving obstacles: actual collision checked during every step;12 stalled frames trigger replan, max3 replans per destination, finite3600-frame guard. No stale static actor cache across plans. All timers remain the existing field RAF; no new battle timers.
- DEV river's finite bridge deck strip remains x1425..1665/y580..610 (height30, formerly26). Outer water/rails/supports remain blocked; no entire-image/transparent-canvas walkability. Existing map layout and bridge image unchanged.
- DEV static collision iteration avoids per-sample nested array allocations; rectangle comparisons unchanged. Villagers, Emma, livestock, wind/water and bird sources/assets unchanged.

## Navigation QA

Unit cases: thin wall sweep, split-axis wall sliding, gradual corner assist, blocked-wall detour,16→8px narrow-gap retry, sealed no-route cancellation, radius arrival and replacement/cancel.

Browser QA (all3viewports): actual mouse or touchscreen input, foot-aligned target, bridge center/exit/off-center both directions; arrival; replacement while moving; key override followed by new pointer target; arrows/WASD, normalized diagonal and native repeated key events; pure-axis slightly misaligned bridge entry in both directions; actual river-edge wall sliding;20 crossings(10 round trips) with every<=5px step collision-checked; long route from(1380,800) to(1790,1030) through the bridge; moving blocker replan; rejected river destination; sealed route failure; Emma/merchant/fisherman tap/click/Enter and no NPC auto-pushing; save/story/preview restoration.

Long ambient/bridge-loop tests use the same actual update APIs for deterministic bounded steps. Real click/tap destination tests use existing field RAF clock playback. Exploration timings use a captured native performance clock, not the mocked animation clock.

| Viewport | Bridge plan max ms | Long detour max ms | CPU condition | Result |
|---|---:|---:|---|---|
| 1280×720 | 19.7 | 110.9 | normal CPU | PASS |
| 844×390 | 47.8 | 278.0 | 4× CPU throttling | PASS |
| 390×844 | 54.4 | 251.1 | 4× CPU throttling | PASS |

Performance warning: a long obstacle detour can produce a one-time planning pause (~278ms in this4×CPU run). Planning does not run each frame; physical phone QA remains necessary.

Navigation checkpoint browser errors: IMAGE404=0, JS EXCEPTIONS=0, CONSOLE ERRORS=0. No old embedded/numbered/old Lou paths; all protected source PNGs/CSS/Battle and STEP9–11 actor modules unchanged. Normal/Raider checkpoint regression passed all3viewports COMMAND/enemy motion/DEV kill/KO/Victory/race protection.

## Aidan source prerequisite

The supplied file for this request is the instruction `.txt` only. The explicitly designated Aidan/Fiona/Lou Field Sprite Reference Sheet is not present in attachments or current repository reference files. An asynchronous request for its file/path was issued while Navigation continued. Aidan A1 remains pending that exact source of truth:0/20 generated, no asset or implementation checkpoint. No substitute battle source, guessed design, sheet crop, Fiona/Lou generation or A2 work.

Navigation success is not an Aidan20/20 claim. Full requested completion/PLAYER QA READY must distinguish this missing prerequisite.

NAVIGATION FIX COMMIT: `c7416314b32318a433a6d789d8777c43ef896d2e` (normal push succeeded).

## Final required report

FINAL RESULT: **FAIL for full requested scope (Aidan A1 incomplete due to missing reference)**. Navigation alone PASS WITH WARNINGS for planning latency under CPU throttling. No gameplay/battle regression detected.

START COMMIT: `e9b5c952a1ad11b07f4fd26d7bb63b3ec19c4a62`
START BRANCH: `work/lind-step9-11-prep`
NAVIGATION FIX COMMIT: `c7416314b32318a433a6d789d8777c43ef896d2e`
AIDAN ASSET COMMIT: NOT CREATED
AIDAN IMPLEMENTATION/QA COMMIT: NOT CREATED
FINAL COMMIT: final QA/report checkpoint at branch tip (completion response records its hash).
PUSH: normal pushes to staging branch only. Main protected; no merge/reset/rebase/force push.

| Navigation requirement | Result |
|---|---|
| Click destination | PASS |
| Tap destination | PASS (real touchscreen events) |
| Auto arrival | PASS, <=3px radius |
| Destination replacement | PASS |
| Manual input cancellation | PASS |
| Blocked destination handling | PASS |
| Wall sliding | PASS, unit + actual river edge |
| Keyboard narrow passage | PASS |
| Corner assist | PASS, <=3px/input, swept |
| Bridge west→east | PASS |
| Bridge east→west | PASS |
| 10 round trips | PASS in each viewport |

| Aidan requirement | Result |
|---|---|
| GENERATED PNG | **0/20** |
| IDLE | 0/4 |
| WALK | 0/16 |
| RGBA/REAL ALPHA | NOT RUN |
| ANATOMY | NOT RUN |
| SWORD COUNT=1 | NOT RUN; no20/20 claim |
| VISUAL CONSISTENCY | NOT RUN |
| GROUND ANCHOR | NOT RUN |
| WALK ANIMATION | NOT RUN |
| FIELD SCALE | NOT RUN |
| NAVIGATION ANCHOR | Aidan NOT RUN; existing placeholder foot-aligned click tested |

| Environment/regression requirement | Result |
|---|---|
| PC1280×720 | Navigation/field/battle PASS; Aidan A1 NOT RUN |
| Landscape844×390 | Navigation/field/battle PASS; Aidan A1 NOT RUN |
| Portrait390×844 | Navigation/field/battle PASS; Aidan A1 NOT RUN |
| STEP9 villagers | PASS, all12 NPC click/tap/Enter, bounded farmer walk, collisions/anchors |
| STEP10 Emma | PASS, peaceful NPC interaction, source PNG unchanged |
| STEP11 birds | PASS, real approach/takeoff, flock, bounded lifecycle |
| WIND ON/OFF | PASS, birds/wind props stop and resume |
| WATER | PASS, river continues while windOFF |
| WIND STONE | PASS, NORMAL/GLOW/OFF, controls/interaction/collision |
| BATTLE REGRESSION | PASS on exercised flows |
| RAIDER HP | 1250 |
| RAIDER SCALE/HUD | PASS, exact geometry match to STEP9–11 baseline in all3viewports |
| COMMAND | PASS, mouse/touch open/close |
| DEV INSTANT KILL | PASS, during enemy motion |
| KO/VICTORY | PASS, fixed after stale motion timers |

Actual player battle input rerun with console monitoring: Aidan/Fiona normal attacks, target selection, 一閃 TP30 consumption, Fiona Guard; enemy attack/turn progression and DEV kill/KO/Victory in normal/Raider. Existing four building entry/exits, fisherman and training tutorial also passed all3viewports. All registered battle asset/cut-in paths loaded successfully; no battle sources/assets/CSS changed. This is not an exhaustive replay of every battle skill/critical/back-attack variant.

TECHNICAL QA: IMAGE404=0; JS EXCEPTIONS=0; CONSOLE ERRORS=0; OLD/INVALID ASSET REFERENCES=0. Protected176 source files unchanged; inline room/story/battle portion unchanged. Final worktree clean after final commit.

Warnings:
1. **Required Aidan/Fiona/Lou field reference image is missing.** Checked message attachments, repository reference files, existing ZIP inventories and remote branches (only main + this work branch). Provide that exact image or a readable path. No production Aidan image is generated from a guessed/substitute reference.
2. Long detour planning reached ~278ms under4×CPU throttling; physical phone responsiveness requires PLAYER QA. Routes are reused during movement; cap/replan limits prevent perpetual wall-pushing.
3. All mobile QA here is Chromium viewport/touch emulation, not physical-device testing.

Only Navigation is PLAYER QA READY. Full Navigation+Aidan completion remains blocked by the reference. STEP12/A2/Fiona/Lou/story/battle expansion is not executed. Current placeholder is retained.

Changed implementation files: `index.html` outdoor field portion + new script load; `js/field/field-movement.js`; new `js/field/field-navigation.js`; `js/field/lind-river.js` finite bridge strip; `js/field/lind-review.js` allocation-free equivalent static collision loop. Report/QA artifacts only otherwise. No production PNG changes.
