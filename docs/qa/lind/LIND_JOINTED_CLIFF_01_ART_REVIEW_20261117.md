# LIND jointed cliff independent art review — 2026-11-17

## Evidence
- GitHub Actions run: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43989252627
- Artifact ID: 14287845013, 3 PNG renders, cliff_candidate.blend, manifest.json, blender.log
- Head: e805cdfa2c0288d36c301ef5f4b0a09f85efd929
- Renderer and SHA validation: PASS (GitHub Actions)
- Independently inspected clay_front.png and clay_threequarter.png from downloaded artifact.

## Gate results
- G1 BLOCKED: canonical source hash recorded but approved world placement/scale and visual comparison not completed.
- G2 FAIL: visually repeated near-vertical narrow zigzag grooves, diagonal shading/mesh facets and large uniform continuous rectangular cliff sheet. Flat turf-cap slab visibly disconnected from weathered cliff top. No credible Irish cliff geology, irregular massing, collapsed sections or slope transitions. Not high-end production quality.
- G3 PARTIAL PASS: Blender renders, .blend, 3 PNGs, output hash verification PASS. Open cliff surface and planar cap are not closed manifold terrain, no collider/navmesh/edge/placement verification.
- G4 NOT_RUN: WebGL/Android performance and game integration not tested.

## Decision
**Do not apply photo PBR textures to this candidate or mark it approved.**
Geometry deficiencies cannot be fixed by photo projection. Keep candidate and render evidence as failed experiment.
The prior smooth-heightfield/striped geology failed twice (PR #346). This separate joint-line grid approach has one G2 failure. Avoid another parameter-only variation. Next method should be a materially distinct sculpt/photogrammetry/rock-mass assembly with irregular non-grid silhouette, volumetric fracture planes, rubble talus, eroded ledges and top/ground transition. Obtain provenance/license for any photographic assets. Require independent clay G2 PASS before PBR.

## Regressions
No main merge, runtime change, approved asset overwrite or Codex bridge edit.
