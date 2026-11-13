# Morwen 3D target sheet — user-supplied 2026-11-13

**Status: DIRECTOR-SELECTED PNG PRESENT IN GITHUB / BYTE-LEVEL SHA256 VERIFIED.**
Director confirmed the uploaded PNG is the correct high-quality target. This reference does not silently supersede the separately approved canonical character master.

## Source / integrity
- **Approved production target PNG**: `assets/companions/morwen/reference/file_00000000301c8209af49625fd11d7670.png` on `feature/morwen-reference-binary-01`.
- GitHub directory listing confirms PNG exists and reports **2,543,634 bytes**. Director explicitly confirmed this PNG is correct on 2026-11-14.
- **PNG SHA-256: `7640822cfeb6c3de5b988a79e438babfaf7e3dafbdbc8433ae6cde78f3988957`** verified in GitHub Actions run [43459999519](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43459999519). PNG dimensions 1536 × 1024.
- **Superseded low-quality JPEG**: former local attachment `7855.png` (JPEG encoding), proposed path `morwen_3d_target_sheet_20261113.jpg`, SHA-256 `d9730dad8b1791204bb39f52697a176d4556e82a33442fdc0c101059bcc7113b`. It was **never uploaded to the checked GitHub branch**, and must not be used or re-uploaded. Keep this metadata solely as historical identification.
- No claim that the PNG is byte-identical to the former JPEG; it is a separately selected higher-quality source.

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
1. PNG existence on feature branch: **PASS**.
2. Director selection of PNG: **PASS**.
3. Verify actual PNG bytes and SHA-256 via GitHub Actions: **PASS** (run 43459999519).
4. Update model-reference checksum record with verified PNG SHA-256: **PASS**.
5. Independent visual review and comparison to separately approved canonical design: **PENDING**.
Do not treat the superseded JPEG as a pending upload.
