# Lind production overnight — STEP 9–11 / Aidan A1

Initial checkout: branch `work`, HEAD `51cf09258b36c47ba1b9dc8954f385cbeaf018d9`, clean.
Work baseline: `211d935b5b27fdeabae485b7616d94ab60bbe5a6` on fetched `work/lind-step9-11-prep`, clean. Preparation commit adds only its instruction document; application remains STEP 8 baseline.
Local old `work` branch renamed `step8-local-checkpoint` to avoid Git's `work` vs `work/...` ref-name collision. No commit history changed.

Main remains protected. Checkpoints stay on the staging branch; no merge before PLAYER QA.

## Source/reference audit

Read AGENTS, CODEX_START_PROMPT, game design/roadmap and current field modules. Reuse camera, outdoor 125% movement, independent animal/water/wind timelines and DEV-only review save guard. No battle module/assets/CSS changes planned. Approved village/NPC sheet and Emma field reference visually inspected. Sheet images are design references only; production PNGs are generated standalone.

Aidan A1's explicitly designated Aidan/Fiona/Lou field reference was not found among current message attachments, repository references or prior uploaded ZIP. Existing Aidan images are battle sources, not the newly designated field source of truth. A1 is held pending that exact reference; do not invent or silently substitute a design. Fiona/Lou field generation is excluded.

## STEP 9

12 distinct occupational/age NPCs; 12 idle PNGs plus farmer's short walk PNG. All standalone RGBA with actual transparent pixels (68.09–82.26% fully transparent). Visually reviewed each original and a light-background comparison: no baked checker/white/black background, no major anatomy defect, all props uncut. No sheet crops or existing PNG replacements.

Adults height 39–46 px, children 31 px; fixed foot anchors, narrow independent 18×8 ground collision, 44 px touch targets. NPCs placed by occupation in DEV review only, not the live story map. All actor foot rectangles clear static structure colliders and other NPCs. Farmer patrol ±24px at 3px/s, IDLE rest 4s, two-pose WALK. Other occupational NPCs stand idle intentionally; no unneeded animation bank. Walk pose is a basic two-pose patrol, not a full four-direction cycle.

All 12 NPCs: click/tap and near Enter, proximity rejection contract, independent temporary interaction, stable save/story flags and preview exit. NPCs stop outside review. Three viewports passed; image 404/JS exception/console error zero. Battle regression passed normal and Raider COMMAND/enemy motion/DEV kill/KO/Victory/race tests in three viewports. Battle stable `73e02af` is an ancestor of this branch.

## STEP 10

`img/field/lind/npc/emma/emma_idle.png`: 1182×1330 RGBA, 1,056,558 fully transparent pixels (67.21%). New standalone generation from both approved Emma sources; no sheet crop. Normal peaceful IDLE only. Original and light-background composite checked for intact glasses/bun/embroidered green shawl/cane/shoes/hands and gentle elderly identity. No black/white/checker background. Sewing pouch retained. Distinct from generic red-kerchief braided-haired elder woman.

38 px display height versus adults 39–46 / current placeholder player44, fixed foot anchor, independent foot collision, safe touch target. All 13 NPCs tested in three viewports: no structure/actor foot overlap, click/tap/Enter functional, save/progression unchanged. Emma does not patrol or carry story content. No origin reveal, illness/death/letter/late-game scenes. Battle regression follows each gate.

STEP 9 checkpoint: `7189b175fcc02159bd3a0a4d798fb5a240745867`, pushed to preparation branch.

STEP 10 checkpoint: `3edf25d1ff4272ffc3a4fd3680e74414ae1d7c47`, pushed to preparation branch.

## STEP 11

Two standalone bird PNGs (perched/flying), 1536×1024 RGBA: fully transparent 88.49% / 78.85%. The first perched candidate had an unwanted halo and was rejected; image-generation transparency edit retained the bird and produced the adopted clean outline. Raw and light/dark alpha composites visually inspected: one head/body/tail, two wings/feet, no baked background or major anatomy fault. No existing asset edited.

Two ground birds and a reusable three-bird overhead flock; fixed five DOM nodes, no collisions/input interception. Ground birds take off over 1.1 seconds within 70px, fade into flight, wait at least 25 seconds and return only when the player is >100px away. Flock starts after 18 seconds, crosses for 12 seconds, rests 45 seconds. Reduced motion suppresses flock and shortens takeoff. NPC/animal/water timelines remain independent.

Wind OFF hides birds and cancels their RAF/new spawns, pauses existing classified foliage/sign/laundry wind motion. Wind ON resumes. River water keeps animating in both states. No standalone waterfall exists in the current DEV asset set; waterfall integration is not claimed or expanded into STEP 12.

QA passed three viewports: actual keyboard/tap approach and takeoff, flock, wind toggle, 60-second OFF clock advance without new flock, water change, reduced motion, bounded DOM, no horizontal overflow, full preview/save/story restoration. Long ambient delays are advanced through the same update API in 0.1-second steps; takeoff uses real input and RAF clock playback. Initial bird-review placement intersected the Wind Stone collision; moved the bird from y690 to y750 and confirmed the player focus is unblocked without changing existing colliders/movement.

Normal/Raider regression passed all three viewports: COMMAND, enemy motion, DEV kill during motion, KO, Victory and stale-action protection. Image404 / JS exceptions / console errors zero in bird QA.

STEP 11 checkpoint: `aab7957dbdc5d99bf75f6fc3c82d0b02d344fc43`, pushed to preparation branch.

## Final regression and scope

Actual inputs in all three viewports: four live peaceful door entry/exits, existing fishing NPC, training dummy starts battle, Aidan/Fiona normal attacks through target selection, Aidan 一閃 consumes TP30, Fiona Guard. Registered battle image/cut-in paths all load. COMMAND click/tap open/close, normal/Raider enemy motion and DEV instant kill during motion, fixed KO and Victory validated. This does not exhaustively replay every battle skill/cut-in/critical/back-attack variant; all underlying battle code/CSS/assets are byte-identical.

Source protection: 153 original PNG/reference/non-field JS/non-review CSS files byte-identical to prep baseline. Inline game implementation unchanged. DEV_MODE=true. Raider HP1250, phase boundaries and current scale unchanged; sprite/HUD geometry exactly matches STEP8 in all three viewports. HUD remains outside sprite. No old embedded/numbered/old Lou code paths; embedded directory absent.

Movement helper confirms pointer5, keyboard22.5, cow72.8px (=130% of56), pig43/chicken24 unchanged, stable cow foot anchors, thin-collision microsteps, destination/boundary cancellation. WindStone NORMAL/GLOW/OFF keeps identical geometry; click/tap/Enter, reduced motion, collision/clear approach and independent river flow passed in all three viewports. NPC actor/structure foot overlaps zero; temporary interaction and preview restore leave story/save unchanged.

Existing livestock/nature/river/bridge/fishing/training regression passed all three viewports, including keyboard crossing of the eastern bridge, dock edge blocking, open training gate and click/tap/Enter dummy interaction. Evidence: `qa/lind-step9-11/final-existing-field-qa.json`.

Fishing regression adapts one old expectation: fisherman_future is now intentionally occupied by fisherman NPC; its terrain is walkable, player standing area remains walkable. No collider removed to make this assertion pass.

## Generated production files (16)

Villagers: `farmer_male_idle.png`, `farmer_male_walk.png`, `farmer_female_idle.png`, `young_man_idle.png`, `young_woman_idle.png`, `elder_man_idle.png`, `elder_woman_idle.png`, `boy_idle.png`, `girl_idle.png`, `merchant_idle.png`, `innkeeper_idle.png`, `fisherman_idle.png`, `caretaker_idle.png` under `img/field/lind/npc/villagers/`.

Emma: `img/field/lind/npc/emma/emma_idle.png`.
Birds: `img/field/lind/environment/birds/lind_bird_perched.png`, `lind_bird_flying.png`.
All 16 RGBA with real alpha. Rejected generator candidates outside repository are not production assets. Existing source PNGs remain unchanged; no sheet crops.

Modified runtime files: `index.html` (field script loading only), `css/lind-field-review.css` (scoped DEV NPC/bird rules), `js/field/lind-review.js` (DEV mount/lifecycle/focus/collision/interaction), `js/field/lind-content-bounds.js` (new alpha bounds). New runtime modules: `js/field/lind-npcs.js`, `lind-emma.js`, `lind-birds.js`. Updated manifest/audit/report; QA scripts/JSON/screenshots in this report's adjacent QA folder. No Battle file changes.

## Required final summary

- FINAL RESULT: FAIL for full requested scope — Aidan A1 reference is missing; no gameplay regression found. STEP9–11 individually PASS with limited visual-polish warnings.
- START COMMIT: `51cf09258b36c47ba1b9dc8954f385cbeaf018d9` (initial main-equivalent checkout). Actual staging start `211d935b5b27fdeabae485b7616d94ab60bbe5a6`.
- START BRANCH: `work` (initial); work branch `work/lind-step9-11-prep`. Initial worktree clean.
- STEP9 COMMIT: `7189b175fcc02159bd3a0a4d798fb5a240745867`.
- STEP10 COMMIT: `3edf25d1ff4272ffc3a4fd3680e74414ae1d7c47`.
- STEP11 COMMIT: `aab7957dbdc5d99bf75f6fc3c82d0b02d344fc43`.
- AIDAN ASSET COMMIT / AIDAN QA COMMIT: NOT CREATED.
- FINAL COMMIT: final QA/report checkpoint (see branch tip / completion response; avoids a self-referential commit hash).
- VILLAGER QA: alpha/anatomy/profession/scale/anchor/collision/patrol/click/tap/Enter PASS.
- EMMA QA: elderly identity, cane/glasses/bun/shawl, distinct generic elder, anatomy/alpha/anchor/collision/interaction PASS.
- BIRD QA / WIND ON/OFF QA: PASS; two perched birds, short takeoff and infrequent overhead flock; OFF absent, resumes ON.
- WATER QA: river flow PASS while wind OFF; no separate waterfall runtime to test.
- AIDAN GENERATED PNG: **0 / 20**. No substitute reference or premature generation.
- AIDAN ALPHA / ANATOMY / SWORD COUNT / CONSISTENCY / GROUND ANCHOR / ANIMATION / SCALE QA: **NOT RUN**. Sword count20/20 is not claimed. Current field placeholder retained.
- PC1280×720 / landscape844×390 / portrait390×844: STEP9–11 and existing field/battle regressions PASS; Aidan A1 not tested.
- BATTLE REGRESSION: PASS on exercised normal and Raider flows; stable source/assets unchanged.
- RAIDER HP: 1250. RAIDER SCALE: STEP8 identical. COMMAND / DEV INSTANT KILL / KO / VICTORY: PASS.
- IMAGE404 / JS EXCEPTIONS / CONSOLE ERRORS: 0 on completed browser QA.
- OLD/INVALID ASSET REFERENCES: 0 on code search and tested assets.

Warnings / remaining work:
1. Aidan A1 blocked by missing designated Aidan/Fiona/Lou field reference. Provide the exact image or repository path; then produce only Aidan20 PNG with full sword/alpha/animation QA. No guessed redesign.
2. Farmer has a minimal two-pose patrol; other NPCs peaceful IDLE only. Bird wing motion is minimal, not a multi-frame flight bank. PLAYER QA should review tiny-scale readability and visual balance.
3. Reference/layout changes, formal map integration, waterfall implementation, story event wiring, A2 and Fiona/Lou production are not undertaken.
4. Cloud Chromium viewport/touch emulation is not physical-device testing.

Main remains `51cf092...`; no merge before PLAYER QA as directed in the preparation brief. All checkpoints are normal pushes to the staging branch.

PLAYER QA READY — STEP9–11 only. Full overnight/Aidan A1 completion is pending the missing visual source of truth. No STEP12/A2/other character/story/battle work proceeds.

To review: check out `work/lind-step9-11-prep`, serve the repository by HTTP, open the DEV リルド村・素材仮配置 entry. Use 素材へ移動 for each NPC/Emma/小鳥, click/tap/Enter nearby, toggle wind, verify water, and return. Production story/save state is not mutated by the review.
