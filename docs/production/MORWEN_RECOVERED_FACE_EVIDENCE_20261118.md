# Morwen recovered-face evidence — 2026-11-18 (PREPRODUCTION ONLY)

## Direct evidence
Original GitHub Actions ZIP archives for PR #316 (artifact 14106227834), PR #318 (14111116241), PR #399 (14319881962), PR #407 (14324029891 / source 14325870825) were opened and PNGs read directly. A six-panel contact sheet was produced from their existing render files; **this is NOT a new Blender render or a calibrated comparison**.

- PR316: `MORWEN_ELM_04_CANDIDATE.blend` (8,627,692 bytes), 86 PNG files in artifact, legacy stylized large eye / tapered chin.
- PR318: `MORWEN_EYELID_05_CANDIDATE.blend` (8,640,804 bytes), 91 PNG files, static eye design candidate; prior deformation G3 FAIL remains.
- PR399: `morwen_head_study_UNAPPROVED.blend` in original artifact; front render shows realistic nose, small eyes and radially segmented bob, G2 FAIL.
- PR407: `morwen_sculpt02_v02_UNAPPROVED.blend`; actual `color_front.png` shows altered hair but still realistic face and incomplete likeness; G2 FAIL. Metadata reports 1,067 modified facial vertices, 8 rendered hair meshes; independent bpy verification NOT_RUN.
- Legacy #316/#318 screenshots have noncanonical hair/outfit. Their stylization may inform eye proportions but geometry transfer is NOT approved.
- Sources are not camera/light matched and cannot support direct shape or rig compatibility claims.

## Preservation
Seven original ZIPs backed up successfully to ChatGPT Library `/THE_WINDBOUND_OATH/Morwen_Artifact_Recovery_20261118/`. GitHub artifact SHA-256 and ZIP integrity PASS. Newly preserved:
- PR316 artifact 14106227834, SHA256 `3441d72185f9509b9f83a66b48aacfb44f9eb4fdf8306381f2c5d77838405d29`
- PR318 artifact 14111116241, SHA256 `4ae0f735cb85dcd50c91f25901df15d21f1436b6768e20a2d2764844dc3cc976`
This Library is NOT automatically readable by Codex/Claude. GitHub shared binary preservation still needs implementation.

## Decision
NO-GO new sculpt. First run actual Blender-level mesh/UV/shape-key/rig inventories and match reference cameras to canonical four views, then compare legacy face transfer feasibility and CC0 anatomical source. Do not rerun the failed annulus/zipper deformation or replace approved sources. No new branch/PR, main merge, destructive action, or G2 acceptance.
