# Aidan exterior relief v1 — independent visual inspection (2026-11-16)

Run: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43789139055
Artifact: 14191223024, downloaded and visually inspected actual `relief_three_quarter.png` and `relief_48px.png`. Script commit `6aa6b7231d2727617fe06130f3c2e9d745b80607`.

## Technical QA
- CI SUCCESS; Blender generated 3 large views and 48x48 PNG; all 3 objects report 0 boundary and 0 nonmanifold edges.
- Bearing elevations remain unchanged; actual *post-displacement contact area* and triangle penetration are NOT_RUN, so no blanket contact QA PASS.
- PNG output validation corrected from escaped literal to real byte tuple.

## Independent art QA: G2 FAIL
- Actual three-quarter image retains rectangular extruded block silhouette, perfectly flat horizontal caps and repetitive subdivided faces.
- No distinct individually fitted irregular fieldstones, weathered edge profiles, mortar/joint variation, lichen or plausible material breakup.
- At native 48px image, silhouette reads as stacked generic boxes rather than stone-built Celtic architecture.
- Surface perturbation is not scan-derived, and is NOT final PBR artwork.

**Method switch required**: do not repeat subdivided-box noise parameter tweaks. Next candidate must use true CC0 scan-derived rock exteriors or independently sculpted non-box masonry stones with preserved mating surfaces, plus measured triangle penetration, three-view visual QA and native 48px QA. Prior faceted/block approaches already failed G2; this visual finding confirms same root issue.

G1 BLOCKED (authoritative house dimensions), G2 FAIL (art), G3 PARTIAL_PASS (watertight/render only), G4 NOT_RUN. No formal adoption, canonical replacement, main merge or publication.
