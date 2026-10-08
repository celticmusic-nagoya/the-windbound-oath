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
