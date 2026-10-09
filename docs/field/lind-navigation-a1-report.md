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
