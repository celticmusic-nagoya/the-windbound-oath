# AIDAN-HOME-MASTER-01 | Production-quality design and QA gate

Status: DESIGN CANDIDATE — NOT CANON. No existing approved assets or dimensions are superseded.
Base: MAP Blender 08 preview, roof slate 02 candidate. The MAP22 field and slate 02 visual art QA were FAIL; technical rendering was PASS.

## Goal
Produce one coherent, game-camera-ready Celtic medieval cottage for Aidan's home, rather than promoting an isolated slate sample or blockout. The approved reference imagery and canonical specifications must be verified before modeling. If missing, mark as BLOCKED and do not invent canonical dimensions, facade, color or asymmetry.

## Source hierarchy
1. Approved character/world/architecture canon and original assets in repository or confirmed director approvals.
2. Approved project concept art and reference boards.
3. Pinterest pins as visual research only (never copy textures or geometry without explicit rights).
4. Original procedural geometry and licensed/verified CC0 material sources as candidates.

## Production construction
- Master coordinate frame: meters, Z up; front/back/left/right and ground contact recorded in a machine-readable manifest.
- Separate collections: foundation; structural stone walls; mortar; timber frame; roof structure; individually varied slates; ridge/eaves/gables; windows and door; chimney; interior-visible props; vegetation/weathering; collision and LOD.
- Model stonework as interlocking courses with intentional irregularity, bevel and mortar depth. Avoid cube walls as final art.
- Roof must cover both slopes with plausible overlap, staggered courses, ridge/eaves closure, verge flashing, and consistent slate thickness; no exposed supports except where architecturally intended.
- Materials: coherent warm muted palette with controlled variation; microfracture and roughness detail at final pixel size; record texture source/license/checksums; deterministic procedural fallback must be labeled.
- Include focal details conveying habitation, without contradicting the canonical Aidan home design.
- Reproducibility: pin Blender version, seed, camera matrices, scene scale, render settings, source asset hashes and output hashes.
- Performance: modular scene with bakeable textures, collision separate from render mesh, and game-camera LOD.

## G1–G4 acceptance
G1 Canon: no conflict with approved silhouette, palette, asymmetry, story location, architecture and scale; all references tracked. Any unknown canonical property remains pending.
G2 Art: director review of silhouette, stone/wood/slate material cohesion, roof construction, wear distribution and living detail. Five criteria each >=4/5 and zero critical defects. Judge at full 1600x1200 and actual game display size.
G3 Tech: Blender headless render and .blend open; manifest SHA256 checks; image alpha as specified; reproducible rerun; geometry intersections/normals checked; all required views output.
G4 Integration: game-camera placement, navigation and collision, performance on target Android browser, visual continuity with field, no regression. Android device QA is NOT_RUN until performed.

## Required outputs
- front, rear, left, right, orthographic game-camera and detail render PNGs; original .blend; geometry/material manifest; licenses; render/QA report.
- Side-by-side comparison at actual game display size.
- Separate G1–G4 statuses; never label CANDIDATE as formally approved.

## Implementation sequence
1. Audit approved Aidan home canon and current scene assets. If missing, report precise blocker.
2. Build production-grade roof and wall module libraries with repeatable parameters, avoiding a series of low-quality render trials.
3. Compose full house and render all views in GitHub Actions, uploading artifacts even on QA failure.
4. Independently assess art and technical QA; at most two failed attempts with same approach, then change modeling/material method.
5. Only after G1–G4 PASS request formal adoption. Do not merge to main or publish without explicit approval.

## Current verified baseline (2026-11-13)
GitHub Actions run 43371532700 success. Roof slate 02 generated as original procedural fallback after Poly Haven HTTP 403. SHA256 and synthetic occlusion PASS. G2 art FAIL; G4 NOT_RUN.

## Source audit — 2026-11-13 (repository default branch)
- `data/maps/rilde_in_aidan.json`: game interior world 960x720, tile 8, unitScale 2.5; spawns default (250,330), from_village (480,532), from_bed (250,330); bed, fireplace, cupboard, window and tapestry. These are gameplay/map units, NOT exterior building dimensions.
- `js/field/lind-assets.js`: `lind_aidan_house` uses `img/field/lind/buildings/lind_aidan_house.png` and generic collision metadata; its header explicitly calls these DEV review positions, not final story/save coordinates. Preserve game integration behavior.
- `docs/story/WORLD_STORY_BIBLE_v1.1.txt`: explicitly SUPERSEDED. Do not use as canonical architecture authority.
- Current exterior architectural canon, approved house image, exact exterior dimensions and palette are NOT YET VERIFIED. Before production-grade geometry is approved, inspect `img/field/lind/buildings/lind_aidan_house.png` visually and retrieve the latest canonical v5.0 or approved exterior art. Do not convert unverified geometry into canon.
