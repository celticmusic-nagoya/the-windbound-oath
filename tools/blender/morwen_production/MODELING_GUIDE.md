# Morwen production modeling guide — NOT APPROVED

## Canonical references
Use the officially approved 4-view PNGs in `tools/blender/production_mesh_08/references/`, checked by `layer0_reference_manifest.json`. The newly supplied detailed costume sheet is additional guidance; it does not overwrite the four approved Layer 0 PNGs. Verify conflicts manually.

**Garter:** Morwen's anatomical RIGHT leg only (local +X). Front = SCREEN LEFT, back = SCREEN RIGHT. Right camera at +X, left camera at -X. Never mirror the garter.

## Quality-first build sequence
1. Calibrate reference images at shared orthographic scale, heel floor = Z0, face = -Y. Use approved silhouette landmarks for height, head, shoulder, hip, hem and shoe; no invented numeric body proportions.
2. Sculpt/retopologize continuous head, torso and limb forms; use deformation-friendly edge loops at shoulders, elbows, wrists, hips, knees and ankles. The previous voxel anatomy review is a **rejected intermediate**, not the final mesh.
3. Separately model face, purple bob haircut, round glasses, structured blouse, embroidered vest, layered pleated skirt, draped asymmetrical cloak, hat and floral ornament, buckled leather boots, satchel, potion vials and gold embroidery. Use separate material IDs and UV islands; prefer normal/roughness maps for tiny ornamental relief.
4. For the cape and hat, create intentional folds, cloth thickness, seams, and trim geometry. Avoid using flattened spheres or single cones as final assets.
5. Rig with 26 bones (22 core + 4 accessory). Bind with checked weights and deformation QA. Inspect right-only garter from all views.
6. Before animating, render 4 static directions at production resolution and in-game footprint. Require independent G1 official-art and G2 aesthetic approval.
7. Only then place the approved Blender file at `assets/characters/morwen/MORWEN_MASTER_APPROVED.blend` in an approved branch. Never create that file as a placeholder.
8. Run workflow manually to generate 4 directions × 8 FK walk frames, then 4×8 RGBA sheet. Evaluate foot sliding, cycle seam, cloth intersections, camera facing and Android memory/performance (G4).

## CI policy
Manual dispatch only. No automatic 32-frame rendering until the actual approved model exists. This repository change is scripts and QA gates only, not completed art. Do not merge to main or publish without approval.
