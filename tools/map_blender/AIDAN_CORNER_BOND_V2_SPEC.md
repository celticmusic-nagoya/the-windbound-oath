# AIDAN CORNER BOND V2 — STRUCTURAL RE-DESIGN (CANDIDATE)

Status: DESIGN_CANDIDATE / NOT_ART_APPROVED. Preserve v1 and all canonical assets.
Evidence: GitHub Actions run 43679509889 (technical PASS, visual G2 FAIL).
Seed: 141127. Blender target: 4.0.2. Output: isolated wall section only.

## Root cause
The front elevation and side elevation are generated independently, while
six quoins are added afterward. The separate return mortar plane and
independent stone envelopes produce a visible vertical discontinuity. Adding
individual stones or tweaking their positions does not solve the topology.

## New construction model
Use one 2D plan footprint per course and partition it into NON-OVERLAPPING
closed solid masonry units. Do not append a decorative quoin column.

- World axes: X = front width; Y = depth / return; Z = elevation.
- Outside corner is shared by front and return. Every corner unit has exactly
  one watertight volume and physically spans the corner, not two overlapping
  cubes.
- Alternate corner bond:
  - A courses: long axis of corner stone follows X, with its return edge
    continuing into the Y wall.
  - B courses: long axis follows Y, with its front edge continuing into X wall.
- Front and side infill begin at the actual quoin footprint boundary, with
  10–15 mm joints; no intersecting nominal AABBs.
- Use one L-shaped backing volume inset 15 mm behind both exposed faces;
  mortar must not bridge the corner or leave a black void.
- First establish a structurally sound orthogonal plan partition. Only then
  deform exposed stone faces, with bounded displacement so joints cannot close.
- Quoin materials must use the same limestone family as adjacent stones.
  A second neutral fill light should reveal the return wall for art inspection.

## Quality gates
G1: compare against approved Aidan house reference; BLOCKED until exact source
    has been checked. No adoption.
G2: inspect front, 3/4 corner, and side renders at full and game display sizes.
    Reject black seam, detached vertical column, overly regular bond.
G3: assert nonzero manifold stone volumes, per-course footprint partition,
    minimum joint >= 8 mm, maximum joint <= 18 mm, no nominal AABB collision,
    correct course staggering, material assignments, deterministic manifest.
G4: only after G1–G3 PASS, test actual scene scale, occlusion and mobile FPS.

## Stopping rule
No more micro-adjustments to v1's independent quoin-column method. Build a
separate v2 generator, keep v1 and its QA evidence unchanged, then run a
single isolated technical render and inspect it before further iteration.

## Reference-use constraints
Real masonry construction references guide bonding and structural continuity.
Game environment tutorials guide trim/UV, mesh budgeting and baking.
Pinterest is visual reference only, not structural evidence or license to copy.
Record source URL and reuse rights before importing any external asset.
