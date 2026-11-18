# Legacy VRoid asset recovery — 2026-11-17

Status: ARTIFACTS_LOCATED_AND_DOWNLOADED / GEOMETRY_COMPATIBILITY_NOT_RUN.

## Actual recovered artifact sources
- PR #316, Actions run 43575126139, artifact **14106227834**, `morwen-eyes-lids-mouth-04`, size 48,528,516 bytes, reported not expired. Artifact downloaded through connected GitHub tool into inspection runtime.
- PR #318, Actions run 43587116653, artifact **14111116241**, `morwen-eyelid-retopo-05`, size 54,369,539 bytes, reported not expired. Artifact downloaded through connected GitHub tool into inspection runtime.
- PR #306 source branch `feature/morwen-head-sculpt-01` HEAD `5931b95ad79f09dbc64d339b0bdcece0eca1dce1`; its artifact not yet recovered.

## Confirmed PR evidence (not a new mesh QA)
- #316 retained 56 expression shape keys and evaluated iris, card binding, Blink and Joy, with technical tests passed in scope; 16 additional keys unreviewed, transparent-card intersections and mouth deformation issues remain. The annulus/zipper eyelid and mouth method failed twice and remains prohibited.
- #318 canthus-anchored static eyelid topology passed some static metrics, but animated deformation failed two method families; G3 FAIL, so its eyelid deformation is not approved for transfer.
- #399 currently uses a distinct Blender Studio CC0 anatomical basemesh, with 7.749997 measured heads and independent G2 FAIL. Do not merge legacy VRoid geometry blindly.

## Next reproducible verification
1. Enumerate ZIP entries and SHA-256 hashes; locate exact .blend / VRM / render / QA data.
2. Open each legacy Blender file in an isolated process, inventory objects, vertices, face topology, armature, UV and shape key names. Do not overwrite.
3. Render legacy head and current head with matched orthographic camera framing and neutral lighting; compare against the official five-image design sheet.
4. Produce actual compatibility matrix: REUSE_VERIFIED / TECHNIQUE_CANDIDATE / REFERENCE_ONLY / REJECTED_METHOD. Any transfer requires geometry and license evidence plus independent visual QA.

**No geometry transfer or new Blender render was performed in this recovery step.** G1 BLOCKED; G2 existing #399 FAIL; G3 legacy comparison NOT_RUN; G4 NOT_RUN.
