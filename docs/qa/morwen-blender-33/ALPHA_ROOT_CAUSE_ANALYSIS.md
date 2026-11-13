# BLENDER-33 | Alpha channel root-cause analysis

Status: BLOCKED. Do not repeat PNG/RGBA configuration-only attempts.

## Observed evidence
- BLENDER-32 smoke: rendering and PNG writing PASS, transparency FAIL.
- BLENDER-33 smoke run 43333344081: syntax, preflight, model build, render PASS; transparency FAIL.
- PIL alpha extrema (255,255); all four corners alpha=255.
- BLENDER-01 regression PASS.
- Actual rendered silhouette and visual art quality have NOT been approved.

## Interpretation
The image is fully opaque. Merely setting scene.render.film_transparent=True and image_settings.color_mode='RGBA' does not establish that the render result contains a transparent background. The .blend scene may contain a world-covering mesh/background plane, compositor override, or other scene content; these are hypotheses, not confirmed causes.

## Structural alternative, next isolated diagnostic
1. Enumerate all visible objects and collections after opening the source .blend. Log type, hide_render, bounds, material alpha, and camera visibility.
2. Produce one *diagnostic* render in a new isolated scene with only the candidate torso, camera and light, excluding inherited world, compositor, background planes and other scene objects. Do not modify the canonical .blend.
3. Compare pixel RGBA and mask bounding box between inherited scene and isolated scene.
4. If isolated scene passes, render five views with an explicit object allowlist. If it fails, inspect Blender render passes/film transparency and switch to geometry-based silhouette extraction for framing QA, retaining color renders for art review.
5. Do not approve anatomy or begin production integration before actual image inspection.

No main merge, canonical overwrite or publication.
