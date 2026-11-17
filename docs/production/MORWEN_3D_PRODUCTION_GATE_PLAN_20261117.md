# MORWEN 3D — dependency-first production gates (2026-11-17)

## Goal and authority
Produce a high-end Morwen 3D character without altering approved art. Canonical authority: `assets/canonical/morwen/2026-11-16/MANIFEST.json` and its five SHA-256-pinned images. The design sheet is the character appearance authority; Layer0 images are inner-body references, not approval for the finished outer silhouette. Target 7.5–8 heads, subject to canonical visual alignment. Do not overwrite approved sources.

## Diagnosis
- 33 hair-ribbon candidate: G2 FAIL (curtain-like strands, crown gaps).
- Continuous bob shell candidate: G2 FAIL (helmet-like/cylindrical hair), G3 limited technical PASS.
- Both methods derived hair dimensions from an **unapproved** provisional body mesh, causing downstream rework.
- Stop hair detail iteration until head and full-body silhouettes are approved.

## Production dependency order
1. **Canonical alignment / G1:** verify hashes and identify front, back, left, right reference directions; resolve image orientation, scale and anatomical right-side details. Keep a separate overlay set and alignment notes.
2. **Body and head proportions / G2:** editable anatomical base mesh at 7.5–8 heads; verify crown/chin/neck/shoulder/waist/hip/knee/ankle landmarks and front/side/back silhouette. Do not infer head ratios from the Layer0 silhouette.
3. **Outfit massing / G2:** hat, bob hair **outer silhouette only**, glasses, cape, skirt, footwear, satchel and asymmetric straps/garter; independent visible volumes, no decorative microdetails yet.
4. **Face and hair detailed sculpt / G2-G3:** controlled curved volumetric hair locks, asymmetric fringe, thickness and root continuity; HairHarpy only if GUI/Vulkan and import/export can be independently verified. Otherwise Blender curves and manual reference-driven editing.
5. **PBR, rig, LOD and game QA / G3-G4:** four-direction renders, topology/deformation QA, then WebGL/Android tests.

## Hard stop conditions
- If G1 canonical match is BLOCKED, do not claim artistic PASS.
- If body proportions or full-body silhouette G2 FAIL, do not detail hair, costume patterns or rig.
- A successful CI/render is only technical evidence.
- Max two effective revisions per identical root cause; change method after second failure.
- Keep full-resolution master and game-optimized outputs separate.
- All edits on feature branch/Draft PR. No main merge, publication, destructive cleanup or canonical replacement without explicit approval.

## Next executable task
Create a reference-aligned **proportion and silhouette measurement report** before any further 3D hair mesh generation. Include SHA-256 input verification, reference previews, front/back/profile landmarks, normalized widths and heights, source geometry head ratio, and mismatch diagnostics. Then choose whether to modify the provisional basemesh or rebuild from a reference-fitted sculpt workflow. Automated geometric checks are NOT an art QA substitute.
