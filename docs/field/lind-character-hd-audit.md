# Lind Character Visual Quality Audit & HD Prototype

RESULT: **PASS WITH WARNINGS** — HD PROTOTYPE PLAYER QA READY.

START MAIN: `d3e299ac7ca90eb49629570a57a90ff678ad7591` (remote main confirmed at start).
BRANCH: `work/lind-character-hd-audit`
IMPLEMENTATION COMMIT: `64fbb44084fdebb18e34f3551785d72b6b1aee6a`
FINAL COMMIT: this report's QA checkpoint; see branch history and completion message.
Publication: source branch only. No main merge or GitHub Pages deployment.

## Root cause audit

46 character PNGs exist: Aidan A1 ×20, generic villagers ×13, Emma ×1, fisherman production poses ×12. The older generic fisherman idle is superseded at mount, so 45 frames are actually used. All 46 are RGBA and have real fully transparent pixels. No production field Fiona PNG exists: the legacy field Fiona is a CSS/text placeholder, hidden in Lind material review. No Fiona asset was generated. Other legacy CSS NPC placeholders are also hidden during material review; this audit covers the actual standalone production actors.

Five viewport/DPR conditions × all 17 camera scales = 85 cases / 3,825 frame observations. PC 1280×720 and 1920×1080 at DPR1, PC 1920×1080 at DPR2; mobile 844×390 and 390×844 at DPR3. These are Chromium emulations, not measurements of the user's physical devices. Every production frame was additionally exposed for actual computed CSS / screen-size measurement at PC 1920×1080, camera1.80, DPR1.

| Cause | Finding |
|---|---|
| Source resolution shortage / native upscale | No PC shortage. Worst tested PC source-to-physical ratio is 2.38×; every frame is downsampled. At PC1.80, Aidan idle_down is 1536×1024 → ~160.26×106.85 full-image CSS px, source ratio9.58×; visible body height79.2px. Emma is1182×1330 → ~70.59×79.43, ratio16.74×; visible height68.4px. |
| CSS dimensions | Source padding is intentionally scaled out through existing per-frame bounds/anchors. Fractional widths/heights are present, not accidental enlargement. They remain unchanged. |
| Camera / double scale | One intended world transform, 1.00–2.10. No additional persistent positive actor scale. Mirroring and existing child/worker animation transforms are intentional. Camera logic is untouched. |
| Image rendering / interpolation | 25 NPC frames force `pixelated`; Aidan20 use `auto`. Nearest-style NPC sampling produces harder/jagged edges at small sizes. Normal browser interpolation is a candidate for painterly NPC art; it can also look softer. |
| Aidan compositor sampling | Aidan already uses auto. With the same PNG and geometry, isolating the visible frame's compositing layer changes and sharpens the PC comparison. Prototype uses `will-change:transform` only; no transform or coordinate is added. This is a browser rendering candidate, not a new artwork resolution. |
| DPR | At the same CSS size, DPR3 gives three times the physical samples per axis versus DPR1. This explains why a high-DPR phone can preserve more detail; actual player-device DPR is not known. |
| Fractional placement / animation | Measured fractional coordinates and existing transient CSS animation transforms. Snapping world coordinates would risk foot/collision/movement jitter, so it was not done. Before/After capture freezes animations in the QA fixture only; normal gameplay is unchanged. |
| Source artwork | Existing A1/painterly designs preserved byte-for-byte. No AI upscale, repaint, re-export or PNG editing. |
| Fisherman extreme mobile zoom | At DPR3 / camera2.10, physical output is up to1.26× source dimensions (source ratio0.794). This modest limit is not the cause of PC-wide roughness. His12 poses/rod/fish/anchors remain unchanged. |

Complete paths, native dimensions, alpha, bytes, bounds, hashes: [asset inventory](qa/lind-character-hd-audit/asset-inventory.json). All viewport/scale ratios, live rectangles, transforms and fractional positions: [CSV](qa/lind-character-hd-audit/render-audit.csv). Hidden frames' CSV dimensions are their metadata-derived potential layout; [individual visible-frame audit](qa/lind-character-hd-audit/frame-css-audit.json) records real computed CSS for all45.

## Three-actor HD prototype

Only Aidan / Emma / male farmer participate. DEV review now has **キャラクター画質（試験）** → **原表示** / **HD prototype · Aidan／Emma／農夫**. Default is original; choice is session-only, not saved. Emma and male farmer idle/walk change to `image-rendering:auto`; Aidan stays auto and only his currently visible frame receives `will-change:transform`. Hidden Aidan frames do not reserve layers. All other NPCs, including children and fisherman, keep their original rendering.

Modified runtime files: `index.html` (two include lines), new `css/lind-character-rendering.css`, new `js/field/lind-character-rendering.js`. No existing field logic, animation timing, collision, camera, terrain, Battle JS/CSS/assets or PNG was edited. No new image/timer/RAF/observer is created. [Protection evidence](qa/lind-character-hd-audit/source-protection.json).

| Representative | Native before → after | File bytes before → after | Display / anchor |
|---|---|---|---|
| Aidan A1,20 PNG | unchanged; each1536×1024 |30,078,849 →30,078,849 total | body44 world px; all20 original per-frame anchors/scales |
| Emma,1 PNG |1182×1330 →1182×1330 |1,303,820 →1,303,820 | body38 world px; same cane/body foot anchor |
| Male farmer,2 PNG | exact originals in inventory |1,832,488 →1,832,488 total | body46 world px; same idle/walk registration |

Generated/updated production image files: **0**. No bulk replacement. Fiona is absent and was not produced. Fisherman received audit/regression only.

## Before / After and QA

24 same-position pairs across four viewports, camera1.00 /1.80 /2.10, focused on Emma and farmer with Aidan beside them. Quality-mode switch preserved exact player/NPC positions, footprints, source URLs, inline dimensions and DOM rectangles. One hundred mode round trips produced no DOM growth / duplicate control. Full PC1920×1080 camera1.80 [Before](qa/lind-character-hd-audit/before-1920-1.8-emma.png) / [After](qa/lind-character-hd-audit/after-1920-1.8-emma.png). Native screenshot crops, without enlarged artwork: [three representatives](qa/lind-character-hd-audit/representatives-before-after.png).

| QA | Result |
|---|---|
| Camera1.00–2.10, all17 configured scales | PASS — audit85 cases; movement sweeps at1/1.5/1.8/2.1 |
| PC1280×720 /1920×1080 | PASS — comparisons, input, actors, collisions, Battle |
| Mobile844×390 /390×844 | PASS — comparisons atDPR3; touch/navigation/lifecycle at standard emulation; no severe toolbar/actor obstruction |
| Aidan walk20 frames /4 IDLE /4-direction WALK | PASS — actual movement, ground-anchor error<0.04px, body44, click/tap/key/toggle and review exit restore |
| Static collision, bridge, wall slide /corner assist | PASS — existing route sweeps; player footprint22×10 unchanged |
| Dynamic actor navigation /Pig retry | PASS — mouse/tap contact wait and automatic resume without new input; child/villager/multiple actors; cancel preserved |
| Village life | PASS — all13 NPC click/tap+Enter, child yield, worker routines, humans/livestock continue during windOFF |
| WindOFF /water | PASS — wind-driven objects/birds stop; water continues |
| Fisherman | PASS — four scales/four viewports,30-minute simulation, rare catch cooldown≥60s, fixed dock/body anchor, full existing wait/bite/reel/catch/inspect/reset states |
| Battle | PASS — normal/Raider COMMAND, real attack/Critical/820ms motion/hit-stop, skill/一閃/TP30/cut-in/damage, DEV kill during enemy action, KO/Victory/race protection; RaiderHP1250, giant scale/HUD independence |
| 404 /JS exceptions /console errors |0 /0 /0 observed in passing runs |
| Legacy asset references |0 old embedded /numbered asset /old Lou runtime paths |

QA result JSON and reproduction scripts live in `qa/lind-character-hd-audit/`. Existing camera, Aidan, village-life, fisherman and Battle runners were reused with the prototype enabled; no game logic was rewritten to make tests pass. Mobile tests are emulation, not hardware certification.

## Performance

PNG inventory total45,659,652bytes (43.54MiB); nominal RGBA decoded upper-bound217,180,660bytes (207.12MiB), including the superseded idle. This is a source-size estimate, not measured process/GPU RAM. No higher-resolution replacements or additional PNG transfers. Compared views retain121 DOM images and identical loaded-image bytes between modes. Two small runtime files were added; the app does not load QA screenshots.

Real headless120-frame samples at camera1.80: prototype average16.67ms at allfour views (approximately60fps), maximum16.8ms in this sample. Baseline averages16.67–16.94ms, occasional33.4–49.9ms. No new frame-rate degradation observed; this short run does not establish physical-phone memory/performance. [Measurements](qa/lind-character-hd-audit/performance.json).

If initial asset cost becomes a priority, separately benchmark lossless WebP/PNG optimization and deferred decode/preload. Do not enlarge all PNGs: Aidan alone already represents120MiB nominal decoded RGBA. No format/preload change in this task.

## Emma motion — AUDIT ONLY

Routine is running. Origin(820,780), speed1.2 world px/s, route offsets[4,-2]→[0,0], rests24/36s. Index-phase staggering adds20.4s to initial rest, giving44.4s; first movement observed44.5s. In each300s audit:8 WALK episodes, total travel29.28px, maximum displacement4.08px (arrival tolerance stops within0.5px). Normal near-player DEV focus and player-away cases had no blocked samples. WindOFF gives the same result; human movement is not wind-driven.

Emma has one idle image, no distinct walk/work image or CSS body animation. EMMA routine does not enter the worker-only WORK pose. Most observation time is rest, and a movement excursion is only about7.3 screen px at camera1.80. This explains why the player can reasonably perceive her as stationary. No collision lock or routine-start failure was observed.

Suggested separate motion prototype, not implemented: initial rest8–12s with shorter independent phase offset, rests12–20s, short walkable route8–12px, speed1.5–2px/s. Retest cane/age-appropriate movement and collision before adopting. No sewing/story/illness/late-game change.

## Warnings and PLAYER QA

- Rendering is an opt-in candidate. Compare softened Emma/farmer outlines and Aidan clarity with original; artistic preference remains PLAYER QA.
- No bulk NPC deployment. Other NPCs await approval of these representatives.
- Fiona field art is not present; fisherman extreme DPR/zoom has a modest source-density limit. No regeneration requested or performed.
- Headless Chromium /mobile emulation only; no physical-device or long GPU-memory benchmark.
- Emma behavior is deliberately unchanged; motion adjustment is a separate next task.
- Branch is not deployed to main GitHub Pages. Use the source branch for QA; no public-page change was made.

PLAYER QA: DEV → リルド村・素材仮配置 → キャラクター画質（試験）. Compare 原表示 /HD prototype at camera1.00/1.80/2.10, focusエマ /農夫, and walk Aidan in allfour directions. Check face/outline/sword/cloak, feet, frame transitions and mobile softness. Await this approval before expanding to other NPCs.

HD PROTOTYPE PLAYER QA READY

## Complete asset table

RGBA/T means real alpha=0 pixels. CSS is the actual full PNG element size in world coordinates; camera1.80 is its actual PC screen rectangle. Transparent padding makes these larger than the character's visible body.

| Actor | File | Native | Alpha | Actual CSS | PC1.80 screen | Original rendering |
|---|---|---|---|---|---|---|
| aidan | characters/aidan/aidan_idle_down.png | 1536×1024 | RGBA/T | 89.03×59.36 | 160.26×106.85 | auto |
| aidan | characters/aidan/aidan_idle_left.png | 1536×1024 | RGBA/T | 79.12×52.75 | 142.43×94.95 | auto |
| aidan | characters/aidan/aidan_idle_right.png | 1536×1024 | RGBA/T | 78.86×52.56 | 141.95×94.61 | auto |
| aidan | characters/aidan/aidan_idle_up.png | 1536×1024 | RGBA/T | 85.11×56.73 | 153.20×102.12 | auto |
| aidan | characters/aidan/aidan_walk_down_01.png | 1536×1024 | RGBA/T | 87.42×58.28 | 157.36×104.91 | auto |
| aidan | characters/aidan/aidan_walk_down_02.png | 1536×1024 | RGBA/T | 87.53×58.36 | 157.56×105.05 | auto |
| aidan | characters/aidan/aidan_walk_down_03.png | 1536×1024 | RGBA/T | 82.81×55.20 | 149.06×99.37 | auto |
| aidan | characters/aidan/aidan_walk_down_04.png | 1536×1024 | RGBA/T | 86.53×57.69 | 155.76×103.84 | auto |
| aidan | characters/aidan/aidan_walk_left_01.png | 1536×1024 | RGBA/T | 79.97×53.31 | 143.94×95.96 | auto |
| aidan | characters/aidan/aidan_walk_left_02.png | 1536×1024 | RGBA/T | 79.69×53.12 | 143.44×95.62 | auto |
| aidan | characters/aidan/aidan_walk_left_03.png | 1536×1024 | RGBA/T | 79.41×52.94 | 142.93×95.29 | auto |
| aidan | characters/aidan/aidan_walk_left_04.png | 1536×1024 | RGBA/T | 79.88×53.25 | 143.77×95.85 | auto |
| aidan | characters/aidan/aidan_walk_right_01.png | 1536×1024 | RGBA/T | 79.88×53.25 | 143.77×95.85 | auto |
| aidan | characters/aidan/aidan_walk_right_02.png | 1536×1024 | RGBA/T | 80.27×53.50 | 144.48×96.30 | auto |
| aidan | characters/aidan/aidan_walk_right_03.png | 1536×1024 | RGBA/T | 78.22×52.14 | 140.79×93.85 | auto |
| aidan | characters/aidan/aidan_walk_right_04.png | 1536×1024 | RGBA/T | 80.36×53.56 | 144.65×96.41 | auto |
| aidan | characters/aidan/aidan_walk_up_01.png | 1536×1024 | RGBA/T | 80.36×53.56 | 144.65×96.41 | auto |
| aidan | characters/aidan/aidan_walk_up_02.png | 1536×1024 | RGBA/T | 74.50×49.67 | 134.10×89.41 | auto |
| aidan | characters/aidan/aidan_walk_up_03.png | 1536×1024 | RGBA/T | 82.31×54.88 | 148.16×98.77 | auto |
| aidan | characters/aidan/aidan_walk_up_04.png | 1536×1024 | RGBA/T | 77.50×51.66 | 139.50×92.98 | auto |
| emma | lind/npc/emma/emma_idle.png | 1182×1330 | RGBA/T | 39.22×44.12 | 70.59×79.43 | pixelated |
| fisherman | lind/npc/fisherman/fisherman_bite_01.png | 335×270 | RGBA/T | 67.00×54.00 | 120.60×97.20 | pixelated |
| fisherman | lind/npc/fisherman/fisherman_catch_01.png | 250×270 | RGBA/T | 50.00×54.00 | 90.00×97.20 | pixelated |
| fisherman | lind/npc/fisherman/fisherman_idle_01.png | 320×235 | RGBA/T | 64.00×47.00 | 115.20×84.60 | pixelated |
| fisherman | lind/npc/fisherman/fisherman_idle_02.png | 300×235 | RGBA/T | 60.00×47.00 | 108.00×84.60 | pixelated |
| fisherman | lind/npc/fisherman/fisherman_idle_03.png | 305×235 | RGBA/T | 61.00×47.00 | 109.80×84.60 | pixelated |
| fisherman | lind/npc/fisherman/fisherman_inspect_01.png | 240×270 | RGBA/T | 48.00×54.00 | 86.40×97.20 | pixelated |
| fisherman | lind/npc/fisherman/fisherman_inspect_02.png | 272×270 | RGBA/T | 54.39×54.00 | 97.90×97.20 | pixelated |
| fisherman | lind/npc/fisherman/fisherman_inspect_03.png | 215×219 | RGBA/T | 43.00×43.80 | 77.40×78.83 | pixelated |
| fisherman | lind/npc/fisherman/fisherman_inspect_04.png | 255×219 | RGBA/T | 51.00×43.80 | 91.80×78.83 | pixelated |
| fisherman | lind/npc/fisherman/fisherman_reel_01.png | 290×270 | RGBA/T | 58.00×54.00 | 104.40×97.20 | pixelated |
| fisherman | lind/npc/fisherman/fisherman_reel_02.png | 270×270 | RGBA/T | 54.00×54.00 | 97.20×97.20 | pixelated |
| fisherman | lind/npc/fisherman/fisherman_reset_01.png | 250×219 | RGBA/T | 50.00×43.80 | 90.00×78.83 | pixelated |
| boy | lind/npc/villagers/boy_idle.png | 1291×1218 | RGBA/T | 41.77×39.41 | 75.18×70.93 | pixelated |
| caretaker | lind/npc/villagers/caretaker_idle.png | 1263×1246 | RGBA/T | 53.31×52.59 | 95.96×94.67 | pixelated |
| elder_man | lind/npc/villagers/elder_man_idle.png | 1224×1285 | RGBA/T | 46.64×48.97 | 83.95×88.14 | pixelated |
| elder_woman | lind/npc/villagers/elder_woman_idle.png | 1230×1278 | RGBA/T | 44.86×46.61 | 80.75×83.90 | pixelated |
| farmer_female | lind/npc/villagers/farmer_female_idle.png | 1360×1156 | RGBA/T | 59.72×50.75 | 107.49×91.35 | pixelated |
| farmer_male | lind/npc/villagers/farmer_male_idle.png | 1377×1142 | RGBA/T | 65.09×53.98 | 117.17×97.17 | pixelated |
| farmer_male | lind/npc/villagers/farmer_male_walk.png | 1377×1142 | RGBA/T | 65.42×54.27 | 117.76×97.68 | pixelated |
| old fisherman | lind/npc/villagers/fisherman_idle.png | 1320×1191 | RGBA/T | unused | unused | not displayed |
| girl | lind/npc/villagers/girl_idle.png | 1275×1233 | RGBA/T | 38.52×37.25 | 69.33×67.05 | pixelated |
| innkeeper | lind/npc/villagers/innkeeper_idle.png | 1297×1212 | RGBA/T | 55.84×52.19 | 100.52×93.94 | pixelated |
| merchant | lind/npc/villagers/merchant_idle.png | 1322×1190 | RGBA/T | 56.70×51.05 | 102.07×91.88 | pixelated |
| young_man | lind/npc/villagers/young_man_idle.png | 1298×1212 | RGBA/T | 56.64×52.89 | 101.95×95.20 | pixelated |
| young_woman | lind/npc/villagers/young_woman_idle.png | 1303×1207 | RGBA/T | 58.25×53.97 | 104.85×97.14 | pixelated |
