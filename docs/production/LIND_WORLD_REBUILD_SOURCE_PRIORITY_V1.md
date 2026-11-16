# LIND WORLD REBUILD — source priority and legacy-map exclusion (2026-11-16)
Status: USER DIRECTIVE; governs all subsequent village spatial design on this branch. Supersedes the **design-source priority** of LIND_SPATIAL_LAYOUT_HANDOFF_02.md, LIND_CANON_MAP_VISUAL_AUDIT_01.md, and lind-visual-anchor-review.v1.json. These older files are retained as audit history, NOT approved layout or a source for future placement.

## Mandatory source hierarchy
1. Latest formally adopted world-map geography and its authoritative version in private handoff repo. Confirm current canon status and revision, not merely a file name or old chat.
2. Formally approved event CGs, including cliff vista, sunset, night, village fire, return route, attack, river-side escape and Aidan home architectural references. Treat approved background-only art differently from reference-only composites.
3. Current official bible, canon addendum/status and adopted prologue script.
4. New coherent world-scale Blender terrain/architecture and camera design derived from 1–3.

## Excluded as layout or visual authority
- Existing playable DOM field geometry (2200x1550), all legacy house/river/bridge/training positions, CSS geometry and map prototype screenshots.
- The previously inspected 'リルド村RPGアセット全体マップ.png' **as a binding geography/layout reference**, unless the current official world-map authority independently reconfirms it. It can remain in provenance/history, not dictate geography.
- The 15-image-pixel markers in lind-visual-anchor-review.v1.json and the old overlay are **SUPERSEDED / DO_NOT_USE_FOR_WORLD_PLACEMENT**. They do not define building footprints or coordinates.

## Provisional geography for source verification (NOT locked)
A previously reported 2026-11-08 world-map adoption described: Rilde central; wind-view coastal cliff west/northwest; inlet/fishing port southwest; farmland and main road to Dunvall Fort north; north-south river, bridge and riverside cliff east; Moss Forest and ancient altar southeast. **The coastal promise cliff and attack-time riverside cliff are distinct places.** Verify these details against the actual latest authoritative world-map document before locking G1. Other official village elements (windstone, well, houses, farms, training) must be placed to satisfy world-scale routes and event CG camera views, not old DOM coordinates.

## Technical preservation only
Keep existing event IDs, story flags, save compatibility, interaction semantics, battle and controls as migration requirements; implementation may need adapters/new collision/navmesh and new map coordinates. No old placement values may flow into spatial authoring. No main changes until separately approved.

## Next deliverables
A. WORLD-MAP-CANON-VERIFY: obtain exact latest approved world-map source, SHA/revision, event-CG manifest and official home reference; classify as approved/reference/candidate.
B. WORLD-ROUTES: new coast/cliff-village-river/bridge-forest/fort route topology; two distinct cliffs; view cones for CGs.
C. VILLAGE-NEW-L0: origin/axes/scale, terrain height, waterways, camera, architecture zones and anchors from world-map+CG, not legacy field.
D. HOME-MASTER: high-quality Aidan house architecture from approved visual source; independent module until approved placement.
E. MIGRATION: adapters preserving save/event semantics; G1-G4 and Android QA.

G1=BLOCKED pending direct latest-world-map and CG crosscheck; G2/G3/G4 for new world NOT_RUN. No Claude/Codex session automatically launched.
