# 3D人 / ymt3d technique triage for Aidan masonry (2026-11-16)

Status: research notes, NOT installed, NOT tested, NOT production-approved.
Reference: https://x.com/ymt3d ; author archive https://3dnchu.com/archives/author/ymt3d/
Review scope: improve existing G2 FAIL stone silhouette and hybrid PBR pipeline without changing canonical house assets.

## Findings and decision
- Floaters / decals tutorial (3dnchu, 2026-11-14): useful for shallow surface detail such as lime stains, tiny fissures, dirt and moss after base stone geometry is approved. NOT a remedy for regular quoin silhouettes. Defer until geometry G2 is credible.
- mPainter 0.9 alpha (3dnchu, 2026-11-12): layer/mask PBR painting candidate, but early alpha and interactive desktop workflow. Do not add to headless GitHub Actions until license, Blender compatibility, headless support and reproducibility are independently established.
- SculptForge (3dnchu, 2026-11-12): possible sculpt + retopology alternative if broad-plane procedural geometry fails twice; standalone workflow not automatically suitable for GitHub Actions. Defer.
- MPP Blender Addon (https://github.com/ymt3d/MPP-Blender-Addon): material copy workflow; little value for deterministic headless material assignment. No installation.
- AutoActiveCameraSwitcher Blender Addon (https://github.com/ymt3d/AutoActiveCameraSwitcher-Blender-Addon): camera convenience; existing script already sets active camera explicitly. No installation.
- UE5 stylized post process: not applicable to browser 2.5D production pipeline. Exclude.

## Next implementation priorities
1. Verify canonical architecture references and dimensions from approved sources. If not found, G1 BLOCKED.
2. Choose CC0 material with exact URL, license, SHA256 and PBR channel/color-space manifest. Until acquired, ASSET_NOT_ACQUIRED.
3. Create independent quoin+infill candidate script using broad asymmetric planes with protected mating faces and clearance; do not mutate aidan_corner_bond_v2.py.
4. Render matched comparisons with and without PBR; ensure silhouette and surface are evaluated separately. Include game-scale crop.
5. Inspect actual images and evaluated geometry. Never report PASS based only on CI.

## Gate status
G1 BLOCKED pending architecture-specific canonical reference verification.
G2 NOT_RUN for hybrid candidate; prior baseline G2 FAIL.
G3 NOT_RUN for hybrid candidate; previous evaluated-topology PASS applies only to old quoin.
G4 NOT_RUN.

No add-on downloaded or installed. No Blender render or game integration executed.
