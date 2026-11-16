# ROUTE-MAT-01 image producer QA

Actual files: `assets/candidates/route-mat-01/attempt-01/`.
Request: Issue #359, method PR #358, baseline `9eb4d796d67789d3eea24aef7e5018ef088dae25`.

Codex generated two original images using the available OpenAI image tool. Both are native 1254×1254 RGB PNGs; requested 2048 was not returned and no upsample is claimed. The actual prompts/tool disclosure and immutable output/reference SHA are in generation.json/manifest.json. Seed/backend/model detail are not exposed by that tool; no fictitious values are supplied. No physical scan, height-from-color, or measured roughness claim is made.

The formal bridge CG and failed PR351 render were directly viewed. The existing failed ROUTE blend was reopened read-only in Blender4.3.2 (241 total mesh objects including context; existing noise/ramp/bump material nodes inspected). Its byte SHA stayed `99f83e08faf8b7661049cb3c195f9ad85b821af6b5b07f54b3886a9dd2e22443`. PR351 automatic-facing family remains stopped. The new texture is continuous stone-face appearance; full-thickness stone layout/relief belongs to Claude, not to a baked masonry grid.

## Executed

- Existing `validate_material_handoff.py`: PASS, no errors. Six existing unit tests PASS.
- PNG decode, dimensions >=1024, same resolution, nonconstant variance, actual SHA: PASS (`image-qa.json`).
- Global phase shift: 0px. Statistical coarse feature correspondence only; pixelwise physical registration is not claimed.
- Roughness scalar: R, Non-Color. RGB channels differ up to9/255; explicit Separate Color Red avoids ambiguous color-to-scalar conversion.
- Edge deltas are retained. NOT certified seamless; CLIP and in-bounds unique stone UV islands required.
- Blender4.3.2 node-loader probe: PASS. Both image hashes, dimensions, color spaces and Principled basecolor/roughness links verified, no geometry or object changes and no blend saved (`blender-node-load.json`).
- Producer image inspection: basecolor and roughness actually viewed. Natural multiscale stone variation without wall blocks, repeated brick grid, text or perspective. This is self-QA, not independent final G2.

G1 provenance/reference subset checked; no formal placement or metric adoption. G2 independent masonry/material comparison NOT_RUN. G3 actual new mesh UV/support/reopen/light-response NOT_RUN. G4 game/Android NOT_RUN. No shader probe constitutes completed bridge integration.

## Handoff

Use README and `create_material(repo_root)` in the candidate folder. Claude must independently build the new full-thickness abutment section, assign the paired maps with shared UVs, author/bake justified normal/height and mortar if needed, and provide its fixed-camera plus48px previews. Do not reuse stopped PR351 automatic facing or cover a flat shell and call it complete. No original/approved assets changed, main merge or publication performed.
