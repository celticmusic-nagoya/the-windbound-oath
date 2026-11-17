# LIND CLIFF-JOINT-01 — Independent three-view art QA (2026-11-17)

## Evidence inspected
Actual GitHub Actions artifact ZIP ID 14286377065, run 43988312919, six files extracted; directly viewed `front.png`, `three_quarter.png`, `top_contact.png` in a contact sheet. The .blend was already reopened successfully by CI; this QA is visual assessment of its actual renders, not of source code or a generated mockup.

## G2 result: FAIL
- Front view: many nearly planar polygon cells read as tessellated shards or manmade wall facing, not eroded natural cliff rock; fracture gaps are excessively clean and mechanically sharp.
- Three-quarter: rectangular extrusion silhouette and straight cliff bottom/end cuts remain visible. Turf top is a smooth blocky heightfield with an artificial edge.
- Top contact: regular quadrilateral tessellation clearly visible on upper ground. Several dark slots/gaps at the cliff–turf contact; physically continuous grass/soil/bedrock section is not established.
- No stratigraphic direction, realistic weathered joints, talus, undercut, erosion variation, coastal waterline or authored large-to-small fracture hierarchy. No game-size validation.
- Therefore **do not apply photo-PBR textures to this geometry**; materials cannot repair silhouette/topology failures.

## Engineering versus art
G3 limited: PASS (3 actual PNGs and .blend generated, checksums and saved-file reopen succeeded).
G1 full spatial/source: BLOCKED; G2 FAIL; G4 NOT_RUN.

## Failure history and stop condition
This is the first directly visually evaluated result of **Voronoi planar extruded joint cells**. Do not relabel parameter changes as a new method. A second same-family iteration is not recommended without evidence of structural changes. Previously exhausted smooth heightfield/striped geology A/B in PR #346 remains stopped.

## Next fundamentally different approach
1. Build a **single continuous rock mass** with a sculpted coastal profile (overhangs, nonparallel fault/joint traces, undercuts) and a physically continuous soil/turf cap; avoid separate planar extruded cells.
2. Use multiscale displacement/sculpt on the continuous mass, with hand-authored erosion masks and localized fractured secondary geometry. Do not confuse noise-only heightfields with authored geology.
3. Require silhouette clay views at wide and final game-size crops, explicit cliff–soil continuity checks, no rectangular study-end presentation in hero framing, and independent QA before texture intake.
4. Photo-derived Ireland landscape textures only after G2 clay acceptance; retain source-specific license evidence and SHA.

No approved source or bridge work modified; no merge/publication.
