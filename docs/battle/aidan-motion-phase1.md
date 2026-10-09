# Aidan Motion Phase 1 + Forest Bat flying idle prototype

RESULT: PASS WITH WARNINGS — branch-only PLAYER QA.

START MAIN: `d3e299ac7ca90eb49629570a57a90ff678ad7591`
SOURCE BRANCH: `work/battle-aidan-motion-phase1`
IMPLEMENTATION COMMIT: `e974a10`

## Implementation

The existing cached-image canvas controller retains one shared RAF. Battle Actor State delegates its three existing presentation hooks through `BattleMotion`; its sequence IDs, cancellation, KO/Victory priority and combat calculations are unchanged. The facade names future action slots and validates a complete, loaded six-image attack set. It never guesses or requests attack URLs. No attack directory/frames exist, so current lunge, damage, Critical and skill timing remain the legacy presentation. Impact frame 03 / 70ms hit-stop are future metadata only; no new attack renderer or damage callback is connected.

Aidan: `00 → 01 → 00 → 02 → 00`, configured 3.2–4.8s per micro cycle (previously 5.4–7.9s). Holds are respectively 700–1000 / 500–750 / 600–900 / 500–750 / 900–1400ms. After 3–5 cycles, add a 300–650ms pause, 03 for 1000–1500ms, then 00 for 700–1000ms. Fade remains 220ms. Action return starts at 00 with an 80–220ms extra hold. Ground anchors and root motion are unchanged. Cosmetic RNG never consumes `Math.random`.

Forest Bat: visual inspection found both wings raised in 00, alternate intermediate wings in 01/03, and both lowered in 02. Adopt `00 → 01 → 02 → 03 → 00`, not the proposed symmetric ping-pong. Each cycle chooses 800–1300ms, divided equally between its four frames. Fade 50ms. Hover has independent actor phase and 1600–2400ms period, ±2–5 CSS px amplitude. Horizontal drift is the explicit OFF constant 0. Initial hold and subsequent cycle variation desynchronize actors.

Bat anchors are manually inspected chest/flight landmarks: [780,740], [785,700], [790,670], [870,730]. A union of all corrected source rectangles plus 7px canvas padding preserves wing margins and hover space. No PNG is cropped or edited; no actor root is translated. Existing sprite drop-shadow is reused. No new shadow system.

## Asset audit

All eight Idle files are 1536×1024 RGBA, alpha 0–254, and contain actual alpha=0 pixels. Aidan transparency is 42.6–45.6%; Bat 56.3–59.2%. Visual inspection on contrasting background found no baked black/white/checkerboard background and acceptable forest-bat identity. Bat faint edge pixels reach some source edges; strong wing tips have narrow margins. Canvas padding prevents additional clipping but does not reconstruct absent source pixels. Complete dimensions, margins, pixel counts and original SHA-256 values are in `qa/aidan-motion-phase1/asset-audit.json`.

## QA evidence

- Actual game COMMAND/target attack, forced Critical + original 820ms lunge/hit-stop, 一閃/TP30/cut-in, enemy damage → idle: normal and Raider, all four viewports.
- State guard, dialogue/presentation pause, reduced motion, attack/damage → KO protection, DEV kill → Victory protection; no idle resurrection.
- 100 Actor State interruptions; one canvas, no DOM growth. Missing/partial/unloaded attack sets safely resolve to legacy, with no speculative requests.
- Rendered Aidan sole: primary foot 193.596px in all four frames; secondary foot range 0.998px.
- Aidan 60s RAF trace: 13 micro appearances and 3 special appearances. Micro onset intervals average 4520ms / min 3808 / max 6800 (includes special pauses); special intervals average 19112ms / min 14944 / max 23280. RNG calls = 0.
- Bat 60s browser-clock run: 52 completed flap intervals, average 1115ms / min 832 / max 1344. RAF quantization adds up to one frame delay per step beyond configured bounds.
- Five-minute browser-clock simulation with Aidan + three Bats: no DOM growth, no root drift, continuing animation. Bat ×1/2/3 layouts and individual phase parameters checked.
- Real headless RAF, Aidan + three Bats: average 16.85ms, max 33.3ms over 180 intervals. This is not a physical-phone performance benchmark.
- PC 1280×720 / 1920×1080, emulated 844×390 / 390×844. Gameplay HUD/target selection and layout remain unchanged. All PNG, Field JS and existing CSS unchanged.
- Observed image 404 / JS exceptions / console errors / invalid old runtime references: 0.

## PLAYER QA

On this source branch, open `dev/battle-motion-preview.html` for Aidan + Forest Bat ×1/2/3, pause/resume and idle-reset comparison. This explicitly labelled DEV visual fixture has no battle AI, HP or damage. In the main game use DEV Event Jump → Moss encounter / Raider for actual combat regression and Aidan idle feel.

Warnings: six normal-attack frames are absent; their renderer and impact integration are deferred. Bat is not a new gameplay encounter and has no Blood Drain. Its body/wing consistency, short crossfade and manually selected chest anchors need PLAYER QA. Timing is a candidate, not a final art-direction approval. Mobile checks are emulation. No main merge or Pages deployment.

PLAYER QA READY
