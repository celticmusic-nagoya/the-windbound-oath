# MORWEN | Professional character modeling workflow (v1)

## Research foundation
- Blender manual, Mesh Structure / Edge Loops: deformation-friendly loops follow natural body contours and are denser around joints. https://docs.staging.blender.org/manual/en/latest/modeling/meshes/structure.html
- Blender manual, Subdivision Surface: topology and supporting loops control shape under Catmull–Clark subdivision. https://docs.staging.blender.org/manual/en/latest/modeling/modifiers/generate/subdivision_surface.html
- Blender manual, Retopology: automated remeshing alone does not create reliable animation-ready topology. https://docs.staging.blender.org/manual/en/latest/modeling/meshes/retopology.html
- Adobe Substance 3D: sculpt-to-texture workflows, baking and material authoring. https://blog.adobe.com/en/publish/2026/05/20/faster-workflows-precise-creative-control-more-connected-3d-pipeline-whats-new-substance-3d

## Adopted workflow
1. **Canonical four-view reference lock**: verify SHA, proportions, pose, design asymmetry, costume layers. Original reference PNGs immutable.
2. **Primary masses / silhouette blockout**: sculpt or hand-model head, neck, thorax, abdomen, pelvis as anatomical volumes; review orthographic front, side, back and 3/4 BEFORE surface details. Do not infer anatomy directly from garment alpha spans.
3. **Topology designed for motion**: deliberate quad edge loops at shoulder/armpit, chest, waist, hips and neck. Prefer hand-authored retopology for deformation; procedural rings only for provisional blockout.
4. **Subdivision and sculpt refinement**: evaluate base cage and subdivided results separately; protect silhouette and avoid smooth shading masking geometric errors.
5. **Separate costume / hair / accessories**: approved asymmetric shapes as independent layers; preserve knee-high socks and other official details.
6. **UV + normal/AO baking + stylized materials**: create after silhouette approval, not as a substitute for geometry.
7. **Rig / skinning / motion**: shoulder and hip deformation tests, neutral and dynamic poses; ensure mobile runtime budgets.
8. **QA gates**: topology checks + 5-view clay and silhouette contact sheet + independent art review + regression; production adoption requires explicit approval.

## Current status
BLENDER-24 candidate topology CI run 43322598847 PASS, regression 43322598809 PASS; artifact 13991710878 exists. **Art QA NOT_RUN.** Current ring-built torso is a provisional blockout, not a professional final character mesh. Next work: render the candidate, then replace or reshape with sculpt/retopology workflow as dictated by actual visual comparison. Do not iterate ring dimensions blindly.
