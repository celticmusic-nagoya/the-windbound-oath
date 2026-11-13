# Morwen 3D target sheet — user-supplied 2026-11-13

**Status: REFERENCE SUBMITTED / IMAGE BINARY NOT YET STORED IN GITHUB.**
This record does **not** assert the attachment has been uploaded or that it supersedes approved canonical assets.

## Source / integrity
- Proposed path: `assets/companions/morwen/reference/morwen_3d_target_sheet_20261113.jpg`
- Original attachment: `7855.png` (actual file encoding **JPEG**, despite extension)
- Size: 1536 × 1024 pixels
- SHA-256: `d9730dad8b1791204bb39f52697a176d4556e82a33442fdc0c101059bcc7113b`
- The supplied image should be committed **byte-for-byte** under the .jpg extension and SHA verified.
- GitHub image binary status: **PENDING_UPLOAD**. Do not claim image is present until verified by Git tree and hash.

## Visual inventory
- Full-costume front, right, back, left orthographic-inspired views
- Close-up portrait with glasses, violet bob haircut, decorated wide-brim witch hat
- Four facial expressions
- Flower/pendant, academy shoulder emblem, satchel, potion vials, boots, cloak embroidery
- Lower-right Layer 0 four views with undergarments and knee-high socks

## Interpretation rules
- User-supplied **quality target / modeling reference**. Compare against existing approved canon; do not silently replace it.
- Full costume and Layer 0 are **separate** modeling layers; do not bake outer costume into skin mesh.
- Preserve asymmetric accessories and sock/garter design according to the approved canon; confirm exact side in source documents.
- A reference sheet is not a geometrically calibrated orthographic blueprint; estimate landmarks with uncertainty, then inspect renders.
- Do not assume all depicted accessories are already approved as production geometry.

## Registration completion gate
1. Commit JPEG bytes to proposed path on feature branch.
2. Verify SHA-256 equals the above.
3. Link image and this metadata in model-reference manifest.
4. Independently inspect visible match to supplied image; only then mark REGISTERED.
