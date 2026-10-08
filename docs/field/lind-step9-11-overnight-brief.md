# Lind Village — Overnight production brief (STEP 9–11)

Base: `51cf09258b36c47ba1b9dc8954f385cbeaf018d9`

This branch is a safe staging branch. Do not merge to main without PLAYER QA.

## STEP 9 — Villager NPCs
Create diverse lived-in Lind villagers matching the established painterly hand-drawn chibi / pixel-art hybrid field style:
- adult male farmer
- adult female villager/farm worker
- young man
- young woman
- elderly man
- elderly woman
- boy
- girl
- item-shop merchant
- innkeeper
- fisherman
- farm caretaker

Place professions logically in the DEV review map. Add short-range idle/walk where practical and click/tap/Enter temporary interaction. Keep scale/anchors/collision consistent.

### Emma separation lock
Do NOT create Emma in STEP 9. Generic elderly women must not combine Emma's defining silhouette: silver/white hair bun + round glasses + deep-green embroidered shawl + cane. Use a clearly different hairstyle, palette, accessory and/or occupation.

Assets: `img/field/lind/npc/villagers/`
Standalone RGBA transparent PNGs only. No reference-sheet crops. No baked white/black/checker backgrounds.

## STEP 10 — Emma
Only after STEP 9 is internally QA-clean, create Emma as an important NPC from the approved visual source of truth:
- clearly elderly, small and stooped
- white/silver-gray hair bun
- round glasses
- wrinkles, kind expression
- cane
- deep-green shawl with floral/plant embroidery
- ivory/cream apron/dress
- burgundy/brown accents
- practical shoes
- seamstress details
- warm painterly field style matching Lind
Do not redesign her.

Assets: `img/field/lind/npc/emma/`
Provide only the field states genuinely needed for peaceful Lind review; standalone RGBA transparent files, consistent anchor/scale. Temporary interaction is allowed, but do not implement Fiona's origin reveal, Emma's illness/death, or later story scenes yet.

## STEP 11 — Birds / environment ambience
Only after STEP 10 is clean:
1. overhead flock crossing the village
2. small birds that take off when Aidan approaches
3. connect ambient wind-driven movement for suitable foliage/grass/sign/laundry elements
4. wind ON: ambience active
5. wind OFF: birds stop/disappear and wind-driven motion stops
6. water MUST continue flowing when wind is OFF

Avoid excessive motion. The village should feel alive, not visually noisy.

## Preserve / do not regress
- formal Lind layout; training ground east across bridge
- cattle 130%
- outdoor movement speed 125%
- Wind Stone NORMAL/GLOW/OFF
- existing Batch 1/2 assets unless a true blocker requires a minimal fix
- Battle stable baseline and all current battle behavior
- Raider HP 1250, giant display, independent HUD
- COMMAND, DEV instant kill, KO, Victory
- DEV_MODE=true

## QA at every checkpoint
PC 1280×720; mobile landscape 844×390; mobile portrait 390×844.
Check alpha/backgrounds, anatomy, scale, anchors, collision, interaction, movement bounds, image 404=0, JS exceptions=0, console errors=0, invalid/old refs=0. Run battle regression after each completed step.

Commit each step separately with a clear checkpoint. If any requirement is uncertain or would require redesigning a locked character/system, STOP that item rather than guessing.

Do NOT proceed to STEP 12 formal map integration. Final state should remain a DEV/QA review state and end with PLAYER QA READY.
