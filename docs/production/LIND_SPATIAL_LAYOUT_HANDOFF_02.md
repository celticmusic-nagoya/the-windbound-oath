# LIND spatial layout handoff 02 — non-canonical production proposal

Status: REVIEW_REQUIRED. Based on verified source image docs/art/reference/lind/リルド村RPGアセット全体マップ.png (SHA-256 83dd4ad1eb10103fdb7eb569e8b1b22cc92920d4c94d4eae85735125de87fe6c), visual audit docs/production/LIND_CANON_MAP_VISUAL_AUDIT_01.md and source/scene matrix. Map is a composite image: only its village overview is geography; side/bottom asset catalogue is NOT terrain.

## Relative topology — no fabricated metric dimensions
1. Village approach in lower-left visual sector, western houses and fenced plots -> central square.
2. Central square contains wind rune stone and well, with shop toward left; storage toward east/southeast.
3. Inn and Aidan home in upper village, house east/right of inn in the image. The actual door approach and relative footprint must be checked against architecture source.
4. Waterfall and elder house in upper-left sector. The main watercourse and possible smaller tributary must be separately traced from the reference before building collision.
5. Fields, orchard and livestock in lower/right sector, with fishing dock lower-right.
6. East/right-side training ground separated from main settlement by river and connected by a crossing. Do not equate every illustrated bridge with the existing single prototype collision bridge.
7. North hill is canon text but is not assigned an image-pixel coordinate or height until the map and scene viewpoints reconcile.

## Shared deliverable contract
WORLD: terrain boundaries, water path, candidate bridge IDs, walkable areas, elevation proposal, source crop IDs. No numeric geometry lock.
HOME: Aidan house modular architecture, roof silhouette, doors and entrance anchor, material palette and render-size QA. No final placement or overwrite of first-batch PNG.
BUILD: inn, shop, elder house, residences and farm buildings; doors and object footprints with candidate flags.
ECO: fields, trees, orchard, fences, livestock, wind response; water timeline remains independent.
STORY: scene CG-to-event anchors for cliff, return, village fire, attack and escape; preserve event and save flags.
INTEGRATION: camera/scale proposal, world coordinate conversion, static PNG/2.5D exports for existing HTML/JS, Android performance budget. Do not assume WebGL migration.
QA: independent G1–G4; map source hash, provenance and original/candidate separation.

## Explicit stop conditions
- G1 cannot PASS until director accepts cardinal orientation, scale, origin, camera, all crossing IDs, building entrance/foot anchors and scene routes.
- G2 requires direct comparison of render to official architectural references and final in-game display size.
- G3 requires verified Blender version/seed/source hashes, alpha/collision, render outputs.
- G4 requires Android playtest and save/event regression; CI success alone is insufficient.

Next concrete action: produce a director-reviewable annotated map overlay with **proposal** anchors and image-pixel coordinates only, preserving original PNG separately; seek approval before writing world transforms. No external Claude/Codex agents are launched by this document.
