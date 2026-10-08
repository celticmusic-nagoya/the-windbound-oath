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
