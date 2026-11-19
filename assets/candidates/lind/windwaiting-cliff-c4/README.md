# Windwaiting Cliff C4 — joinable coastal strip

C4 implements [Plan A](https://github.com/celticmusic-nagoya/the-windbound-oath/pull/421#issuecomment-7008563955). The asset is a closed cliff strip with explicit repeatable lateral boundaries. Two translated instances and inland context terrain stage it as a continuous coast for review. These context instances are placement proxies. C1–C3 remain archived as separate, unapproved candidates.

## Boundary contract

Asset-local provisional axes: +Z up, −Y seaward, +X along the coast. Z=0 is provisional sea datum. X=−17 and X=23 are matching YZ cross-sections. Translate the next module by +40 along X. Correspond along the perimeter ring order beginning at the inland top edge. Both longitudinal tangents are +X and the exterior corner normals match. The U coordinate advances by exactly one tile, and V is constant for a given perimeter vertex. The cap surfaces close the deliverable independently and are internal when modules are placed together. A separate rear context mesh covers rear closure in review. Water is an independent collection for staging. Standalone production water and seabed assets remain future work.

## Candidate changes

- The coastline preserves three rounded headlands of decreasing height and restores the central cove to 3.56 provisional units.
- Two geological shelf families terminate inside each block and move through different absolute heights. Design ranges are 1.17 and 1.20; thicknesses are 0.42–1.02, dips 1.3°–2.6°, and nominal shelf windows 36%–65% of facet width. Segment depths and shifted raked fractures are authored geometry. Seam transitions use a constant profile so courses meet at the prescribed ends.
- Reef clusters vary in breadth and are partly submerged. Cliff-foot talus continues to use upward support rays. Grass is blended with a continuous geometry-normal and height mask. These are review shaders; production PBR is pending review.

## QA and review limits

The reopened body is a closed single component; the boundary, nonmanifold and nonadjacent self-intersection counts are all zero. The split-corner normal, UV and geometry comparisons pass at all 85 lateral pairs. Exposed downward area is 6.59%. The conservative geometric end-slope proxy (above-sea, 20–60° triangles within either seam's two-unit band, including grass) is 3.80%, with rendered visibility assessed separately. Orthographic first-hit ray sampling reports one closure hit in the right view and zero in the other five. The raw whole-body inland-facing steep-area ratio includes hidden rear closure geometry; it is recorded alongside the camera visibility data. End-slope imagery and geological legibility are for independent review, so G2 remains NOT_RUN. G1 world placement is BLOCKED. Full game G3 and G4 remain NOT_RUN.

[Official CG](../../../approved/game/cliff/sunset_background.png) is locked to SHA-256 `db0b1f6ae12892047c0def8af53c2bab54b294b76afc08565bf1670252d94a07`. The asset uses original procedural shaders and geometry. Review water, camera and light are staging only. There is no approved world placement or game camera.

[Blender master](windwaiting_cliff_C4_UNAPPROVED.blend) · [CG comparison](comparison.png) · [machine QA and SHA-256](qa.json) · [build log](build.log) · [reopen QA log](qa.log)

Views: [front](front.png), [left](left.png), [right](right.png), [elevated](elevated.png), [shore detail](shore_detail.png), [sunset](sunset.png).

Reproduce with the C4 build and inspect scripts under `tools/map_blender/lind/` using `bpy==5.2.4` and the compare script using Pillow and DejaVu Sans. Use a common `--out` directory and supply the official CG as `--reference` for compare and inspect. Run in build, compare, inspect order.
