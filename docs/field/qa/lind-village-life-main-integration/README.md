# Lind Village Life — latest-main integration QA

Local regression result: PASS WITH WARNINGS. Public deployment/smoke will be checked after push; this document does not assert deployment success.

- MAIN BEFORE: `efbe7144a088d41d32fd47d526ea3e5d6dce85f3`
- SOURCE FINAL: `c79fea794fdcb0a519d6d03ebac27b9c293e5c40`
- Merge base: `ac3707698018aa9efe016e04776ba3d1d1be833e`
- Method: audited no-ff merge preserving both histories. File overlap only index.html, with independent field and Battle Idle includes. All source STEP B files match SOURCE FINAL; removing five new field include lines restores current main index exactly.
- User manual commit `efbe714` has the same tree as its parent (no actual file diff). Its history and all current-main assets, including four Aidan Idle and four Forest Bat idle images, are retained.
- No additional production implementation, timing/palette/PNG edits, camera default fix, story wiring, or Battle changes.

## Fresh integration tests

- Fisherman all four viewports and camera scales 1/1.5/1.8/2.1: 30min simulation, 11 catches, 88.9% WAIT, minimum60s catch cooldown, fixed anchor, all states, PASS. Twelve PNGs RGBA/alpha0 and source bytes unchanged.
- Children 30min: 52 swaps/26 reversals/104 pauses, no sustained overlap or static intrusion, PASS.
- Nine villagers plus Emma 30min: bounded movement, no all-NPC synchronized walk, static safety, PASS. Emma origin/height/cane image unchanged.
- All 13 NPC mouse/tap/Enter, child player-yield, humans/animals wind OFF, flowing water: all four viewports PASS.
- Dedicated Wind OFF 30min: fisherman WAIT/BITE/REEL/CATCH/INSPECT/RESET and all children/villagers/Emma continue, PASS. A prior 30s observation had zero Emma travel because initial rest is 24+12×1.7=44.4s; it was not a stopped actor. Rare catches are not required to occur in every short 180s interval.
- Dynamic pig temporary blockage, retained destination, resume without re-click, child/villager/multiple contacts, keyboard cancel/static blocked destination: all four viewports PASS.
- All 14 building fronts/door/corners/contact/input PC1280 1×; representative five on both mobile views at1.8×/2.1×: PASS.
- Camera/mouse/tap/keyboard/bridge/wall-slide/corner assist/blocked destination/Wind Stone/water: all four viewports, four scales PASS. Bridge repetitions shortened from10 to1 per smoke case; route checks unchanged. Camera options1–2.1 and default1 remain unchanged.
- Actual normal/Raider attack, Critical820ms motion + hit-stop, 一閃/Cut-in, damage→Idle: all four viewports PASS. The first concurrent single-point WAAPI test failed; an isolated unchanged test passed. Final QA measures WAAPI before screenshot capture, avoiding real-time capture delay during fake-clock sampling. Product code untouched.
- COMMAND/DEV kill during motion/KO/Victory/race/independent Raider HUD: three principal viewports PASS; HP1250 and phase formula unchanged.
- Aidan Idle native60s: all four frames and private-RNG/no gameplay Math.random consumption PASS. JS/CSS/PNG/timing match MAIN BEFORE exactly.

PC1280×720 /1920×1080, mobile844×390 /390×844: PASS. Image404, JS exception, console error, legacy asset references:0 in executed local suites. Syntax/diff checks pass.

Warnings inherited: children/most villagers use static artwork for movement; physical mobile visual QA pending; camera initial1× vs provisional1.8× is a separate task. No A1.5/Fiona/Lou/Party Follow/interiors/cinematic camera/Battle cleanup implemented.

After successful public deployment, PLAYER QA should inspect rare catches, child route/yield, work pauses/Emma, pig retry, Wind OFF with continuing people/water, and camera scales. Public results are reported separately to avoid falsely treating local tests as deployment evidence.
