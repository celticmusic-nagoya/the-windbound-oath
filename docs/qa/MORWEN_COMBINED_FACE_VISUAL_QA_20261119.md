# Morwen combined legacy face — visual QA (2026-11-19)

## Evidence
- Workflow: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44543166552
- Artifact: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44543166552/artifacts/14538269453
- Commit: ac5f89cee46d523f853924e5b75f726638547fc4
- Renderer: Blender 5.2.4 / Cycles CPU, 960×960, front and three-quarter.
- Geometry manifest: 768 separated face-part faces + 1,982 complementary face faces = 2,750 original Face faces; eye mesh 1,120 faces.
- Provenance: PR #316 native candidate, **not** adopted Layer 0 design.

## Gates
- Render existence: PASS (two PNG files)
- Geometry count preservation: PASS (2,750 Face polygons accounted for)
- G1 official four-view appearance match: NOT_RUN (no calibrated side-by-side overlay)
- G2 art direction: FAIL
- G3 actual deformation/eyelid closure: NOT_RUN (shape key retention alone is not animation QA)
- G4 game integration: NOT_RUN

## Visual observations
1. Large white/pale material regions surround both eyes, incompatible with finished face appearance.
2. Three-quarter view exposes apparent intersections or occlusion issues across facial features; do not assume whether root cause is material, mesh or transforms without inspecting the source.
3. Eye and mouth presentation is stylized/unfinished relative to the approved target.
4. Hair and final silhouette are absent from this face-only render.

## Production decision
**STOP using the legacy face candidate as a direct final-quality base.** Keep the recovered native geometry as a protected reference/possible parts donor, not a G2 PASS model. Do not iterate material-only patches or re-run this same render as a substitute for genuine authored sculpt.

## Next non-destructive work
1. Open official front/side/back/left Layer 0 references and align the character head's landmarks and proportions in a single calibrated scene.
2. Assess whether any existing sculpt-quality mesh can be used without violating provenance or design; otherwise begin a new authored head sculpt, separate from eye/eyelash reference parts.
3. Produce full-face + hair neutral front, side, three-quarter renders at final display scale and request independent G2 review before retopology/rig.
4. Preserve original SHA-256 and license/source classification. No main merge or official adoption from this QA.
