# MORWEN 7.75-HEAD FOUR-VIEW CONSTRUCTION SPEC — 2026-11-17

**Status:** APPROVED-TO-PRODUCE CANDIDATE / ART_NOT_CREATED / G1 BLOCKED. This is a production specification, not a finished illustration or adopted 3D model.

## Source lock
Use the five byte-preserved images and their exact SHA-256 values from `assets/canonical/morwen/2026-11-16/MANIFEST.json`. Design-sheet JPEG governs face, short purple bob, hat, glasses, academy costume, cape, accessories, book crest, palette and asymmetry. Four Layer0 PNGs govern body, inner layers, anatomical right-leg garter, socks and profile consistency. Historical designs must not override this source set. Source original images are read-only.

## Production coordinate system
- Neutral A-pose or relaxed symmetric standing pose, no head tilt, no perspective; front, character-left, back, character-right all at the same orthographic scale.
- Character anatomical right = viewer's left in front; viewer's right in back. Right-leg garter remains a continuous band visible from back; right-facing profile shows it, left-facing profile does not.
- Define total **body height** from bare-foot floor to anatomical cranial vertex as `H`, **excluding hat, hair ornament and footwear soles**. Define anatomical head height from cranial vertex to chin underside as `H/7.75`. All costume projections beyond the body are separate and must not inflate head-count.
- Default layout for a proposed new drawing: 4 panels, each 768×1536 px, aligned floor and crown rulers; combined 3072×1536 px; transparent PNG (RGBA) plus editable master if available. Dimensions are **proposed candidate layout**, not established canonical pixel dimensions.
- Example proportional ruler in body-normalized units: crown 0, chin 1.00, floor 7.75 head units. Do not infer other anatomy from the older ~6.1-head Layer0 PNG. Shoulder, elbow, waist, crotch, knee, ankle placements require art-led anatomical design and four-view cross-check, not fixed invented measurements.
- Shared axis: vertical Z up; side profile mirrored only for alignment of body proportions, never as a substitute for genuinely different costume asymmetry. Keep matching ear/eye/nose/chin/shoulder/elbow/wrist/waist/hip/knee/ankle/floor guides across four panels.

## Layer architecture
0. Body and anatomy, skin, inner garment: accurate adult 7.75-head proportion, natural joints and topology planning.
1. Hair and face: canonical short purple bob, glasses, earrings; preserve face identity in profile.
2. Academy clothing: actual layered garments, pleated skirt, cape, knee-high socks, boots; ensure visible cloth thickness, drape and closures.
3. Accessories: witch hat/flower, crest/book, shoulder strap, satchel, potion/chain and asymmetric right-leg garter; preserve attachment points and occlusion.
4. PBR material intent and rigging clearances: metal, cloth, leather, skin and hair separated for later production.

## Candidate acceptance checklist
- [ ] Four independent orthographic views at identical body scale and floor/crown alignment.
- [ ] 7.5–8.0 measured anatomical heads; nominal 7.75; separate from hat height.
- [ ] Same recognizable face, hair silhouette, palette and outfit as approved JPEG.
- [ ] All body/inner-layer elements consistent with four approved Layer0 PNGs.
- [ ] Correct right-leg garter in front/back/right profile; no false mirrored left garter.
- [ ] No invented colors, ornaments, belts or clothing solutions where references are silent; unresolved details flagged for director.
- [ ] No silhouette collisions, disconnected costume pieces, hidden impossible attachments or inconsistent profile depth.
- [ ] Full-resolution and target in-game display size inspection, plus independent visual QA.
- [ ] Candidate art delivered for director visual approval **before** treating it as a canonical geometry sheet.

## QA gates and next action
G1 source identification PASS; candidate design comparison BLOCKED until art exists. G2 NOT_RUN. G3 layout/ratio checks NOT_RUN until PNG exists. G4 NOT_RUN. Produce the actual four-view candidate with direct visual reference to the five source images; do not treat this text document, an SVG grid, or generic base mesh renders as finished art. No canonical replacement, main merge, publication, or paid external generation.
