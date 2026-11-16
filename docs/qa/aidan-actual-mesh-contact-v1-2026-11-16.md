# Aidan actual evaluated-mesh contact QA — 2026-11-16

Evidence: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43788410636
Artifact `aidan-actual-mesh-contact-qa-v1` (id 14191068930). Source commit `b3e961af7eb9d4070b5b23760c3d66949885831a`.

Blender successfully generated meshes and actual cap geometry was inspected (not just input design values).
- Actual upper cap area: 1.394399881362915
- Lower support XY area: 1.3943999284267434
- Floating point support ratio: 1.0000000337520312 (interpret as 100% within numeric tolerance; NOT physically >100%).
- Lower plan overlap: 0.0.
- Bearing cap vertices: coplanar.
- BVH overlap candidate pairs: west/east 6, west/upper 4, east/upper 4. These pairs can represent legitimate touching faces; **do not interpret as proven penetrating triangles**.

**G3 PARTIAL_PASS** for measured coplanar bearing area and rendered artifact. Actual signed triangle penetration/clearance remains NOT_RUN. G1 BLOCKED for house master dimensions. G2 NOT_RUN for completed weathered masonry (this is simplified technical geometry). G4 NOT_RUN.

Next non-destructive action: introduce licensed scan-derived organic relief **only on exterior faces** with shared bearing caps unchanged; test cap areas, watertightness, normals and BVH before/after, render three directions and at 48px. Do not classify primitive-shaped geometry as a completed art asset. Preserve this QA baseline for regression comparison.
